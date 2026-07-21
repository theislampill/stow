"""README ontology-navigation integrity gates.

The README carries a generated domain/family navigation view over the same
primary rules the catalog covers, between generator-owned markers. These
gates make the view drift-resistant and keep it free of the count-leak the
rest of the prose surfaces are held to:

  * ``gen_ontology_nav.py --check`` passes (the committed README matches a
    fresh render of the ontology sidecar);
  * every one of the eight domains and all 104 primary rule ids appear in
    the region;
  * the region carries no bare forbidden partition count (53, 61, 11, 24),
    reusing ``test_count_leak.py``'s scanner directly.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import os
import subprocess
import sys

from ruamel.yaml import YAML

import test_count_leak

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
README = os.path.join(REPO, "README.md")
ONTOLOGY = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _ontology_rules():
    yaml = YAML(typ="safe")
    with open(ONTOLOGY, encoding="utf-8") as fh:
        return yaml.load(fh)["rules"]


RULES = _ontology_rules()
README_TEXT = _read(README)


def _nav_region():
    begin = README_TEXT.index("<!-- ONTOLOGY-NAV:BEGIN -->")
    end = README_TEXT.index("<!-- ONTOLOGY-NAV:END -->")
    return README_TEXT[begin:end]


NAV_REGION = _nav_region()


def test_generator_check_mode_is_current():
    proc = subprocess.run(
        [sys.executable, os.path.join(REPO, "tools", "gen_ontology_nav.py"),
         "--check"],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_every_domain_appears_in_the_region():
    domains = {fields["domain"] for fields in RULES.values()}
    assert len(domains) == 8, "expected eight ontology domains, found %d" % len(domains)
    for domain in domains:
        label_words = domain.split("-")
        # The generator title-cases each hyphen segment; a loose per-word
        # membership check tolerates its exact capitalization rules.
        assert all(word.lower() in NAV_REGION.lower() for word in label_words), (
            "domain %r not represented in the navigation region" % domain)


def test_every_rule_id_appears_exactly_once_in_the_region():
    seen = [rid for rid in RULES if ("`%s`" % rid) in NAV_REGION]
    assert sorted(seen) == sorted(RULES), (
        "nav/sidecar id mismatch: missing=%r" % sorted(set(RULES) - set(seen)))
    for rid in RULES:
        assert NAV_REGION.count("`%s`" % rid) == 1, (
            "%s appears more than once in the navigation region" % rid)


def test_exact_rendered_headings_are_pinned():
    # The acronym-cased family heading must not regress to plain title case.
    assert "**AI Stylistic Tells**" in NAV_REGION
    assert "**Ai Stylistic Tells**" not in NAV_REGION
    # A domain summary with its exact rendered text.
    assert "<summary><b>Terminology and Grammar</b></summary>" in NAV_REGION


def test_region_is_structurally_well_formed():
    assert NAV_REGION.count("<details>") == NAV_REGION.count("</details>")
    assert NAV_REGION.count("<summary>") == NAV_REGION.count("</summary>")
    # Eight domains, each its own <details> block with one summary.
    assert NAV_REGION.count("<details>") == 8
    assert NAV_REGION.count("<summary>") == 8


def test_domain_summaries_appear_in_sorted_order():
    domains = sorted({fields["domain"] for fields in RULES.values()})
    offsets = []
    for domain in domains:
        label = " ".join(
            "AI" if w == "ai" else w.capitalize() if (i == 0 or w not in
            ("and", "of", "the", "in", "for", "to", "on")) else w
            for i, w in enumerate(domain.split("-")))
        marker = "<summary><b>%s</b></summary>" % label
        assert marker in NAV_REGION, "missing summary for %r" % domain
        offsets.append(NAV_REGION.index(marker))
    # Sorted-by-slug domains must render in strictly increasing position.
    assert offsets == sorted(offsets), (
        "domain summaries are not in sorted order: %r" % offsets)


def test_nav_region_has_no_count_leak():
    findings = test_count_leak.scan_prose_text(NAV_REGION)
    assert findings == [], "count leak in the ontology navigation region: %r" % findings


def test_readme_as_a_whole_still_has_no_count_leak():
    # The generator adds new text to a surface test_count_leak.py already
    # gates; this is a direct, redundant confirmation scoped to this change.
    findings = test_count_leak.scan_prose_text(README_TEXT)
    assert findings == [], "count leak in README.md: %r" % findings
