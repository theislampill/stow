"""README catalog integrity gates.

The README carries the complete primary-rule catalog between generator-owned
markers. These gates make the catalog drift-resistant without printing any
counts into the README itself:

  * every primary rule id appears exactly once (no missing, duplicate, or
    unknown ids);
  * each displayed enforcement status matches the registry, and the callable
    set matches the runtime's own validator constant;
  * per-class totals in the rendered catalog equal the registry's totals
    (computed dynamically on both sides, never hardcoded);
  * README example blocks marked for validation pass the shipped runtime.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import importlib.util
import os
import re
import subprocess
import sys

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
README = os.path.join(REPO, "README.md")
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")

RULE_ROW_RE = re.compile(
    r"^\|\s*`(STOW-[A-Z]{3}-\d{3})`\s*\|.*\|\s*(Callable|Planned|Review-fallback)\s*\|\s*$",
    re.M)
ID_ANYWHERE_RE = re.compile(r"`(STOW-[A-Z]{3}-\d{3})`")
VALIDATE_MARKER_RE = re.compile(
    r"<!--\s*validate:(json|yaml|jsonl|schema:[a-z-]+|lint-clean)\s*-->\s*\n```[a-z]*\n(.*?)```",
    re.S)

STATUS_LABEL = {"callable": "Callable", "planned": "Planned",
                "review-fallback": "Review-fallback"}


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        return yaml.load(fh)["records"]


RECORDS = _records()
README_TEXT = _read(README)


def _catalog_region():
    begin = README_TEXT.index("<!-- CATALOG:BEGIN -->")
    end = README_TEXT.index("<!-- CATALOG:END -->")
    return README_TEXT[begin:end]


def test_every_primary_id_appears_exactly_once_in_the_catalog():
    catalog = _catalog_region()
    rows = RULE_ROW_RE.findall(catalog)
    seen = [rid for rid, _status in rows]
    registry_ids = [r["id"] for r in RECORDS]
    assert sorted(seen) == sorted(registry_ids), (
        "catalog/registry id mismatch: missing=%r extra=%r dupes=%r" % (
            sorted(set(registry_ids) - set(seen)),
            sorted(set(seen) - set(registry_ids)),
            sorted({x for x in seen if seen.count(x) > 1})))


def test_no_unknown_id_is_referenced_anywhere_in_the_readme():
    known = {r["id"] for r in RECORDS}
    for rid in ID_ANYWHERE_RE.findall(README_TEXT):
        assert rid in known, "README references unknown rule id %s" % rid


def test_displayed_status_matches_the_registry():
    by_id = {r["id"]: STATUS_LABEL[r["enforcement"]["status"]] for r in RECORDS}
    for rid, label in RULE_ROW_RE.findall(_catalog_region()):
        assert label == by_id[rid], (
            "%s shown as %s but the registry says %s" % (rid, label, by_id[rid]))


def test_displayed_callable_set_matches_the_runtime():
    spec = importlib.util.spec_from_file_location(
        "lint_prose_for_catalog", os.path.join(RUNTIME, "lint_prose.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    runtime_count = len(module.IMPLEMENTED_VALIDATORS)
    shown_callable = [rid for rid, label in RULE_ROW_RE.findall(_catalog_region())
                      if label == "Callable"]
    assert len(shown_callable) == runtime_count, (
        "catalog shows %d callable rules; the runtime implements %d"
        % (len(shown_callable), runtime_count))


def test_per_class_totals_match_the_registry():
    """Both sides computed dynamically; no total is ever printed in the README."""
    catalog = _catalog_region()
    registry_by_cat = {}
    for record in RECORDS:
        registry_by_cat[record["category"]] = \
            registry_by_cat.get(record["category"], 0) + 1
    # Rendered groups are <details> blocks; count rule rows inside each.
    blocks = re.split(r"<details>", catalog)[1:]
    rendered_counts = sorted(len(RULE_ROW_RE.findall(b)) for b in blocks)
    assert rendered_counts == sorted(registry_by_cat.values())
    assert sum(rendered_counts) == len(RECORDS)


def test_generator_check_mode_is_current():
    proc = subprocess.run(
        [sys.executable, os.path.join(REPO, "tools", "gen_readme_catalog.py"),
         "--check"],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stdout + proc.stderr


MARKED_EXAMPLES = VALIDATE_MARKER_RE.findall(README_TEXT)


def test_readme_carries_marked_validated_examples():
    assert MARKED_EXAMPLES, "README has no validation-marked examples"


@pytest.mark.parametrize("kind,body", MARKED_EXAMPLES,
                         ids=[k for k, _b in MARKED_EXAMPLES])
def test_marked_readme_example_validates(kind, body, tmp_path):
    sys.path.insert(0, RUNTIME)
    try:
        import validate as validate_mod
        import lint_prose as lint_mod
    finally:
        sys.path.pop(0)
    if kind in ("json", "yaml", "jsonl"):
        result = {"json": validate_mod.validate_json,
                  "yaml": validate_mod.validate_yaml,
                  "jsonl": validate_mod.validate_jsonl}[kind](body)
        assert result.ok, "README %s example invalid: %r" % (kind, result.errors)
    elif kind.startswith("schema:"):
        result = validate_mod.validate_schema(kind.split(":", 1)[1], body)
        assert result.ok, "README %s example invalid: %r" % (kind, result.errors)
    else:  # lint-clean
        findings = lint_mod.lint(body)
        assert findings == [], "README example not lint-clean: %r" % findings
