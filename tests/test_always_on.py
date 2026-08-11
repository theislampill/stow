"""Gates for the always-on activation architecture.

The always-on rule families must govern ordinary user-facing prose turns without
turning closed lexical matches into authorship verdicts. These gates prove the
activation architecture structurally:

  1. a generated operational module exists, is registry-derived, and is current;
  2. every action rule and every descriptive taxonomy leaf is represented;
  3. the kernel carries ordinary guidance and keeps the generated detail cold;
  4. the ordinary-turn footprint stays bounded;
  5. the kernel still carries its byte-exact no-greedy-loading rule.

HONEST SCOPE: these are structural/routing contracts over the shipped files. There
is no model-invocation harness here, so they prove the kernel and cold detail are
complete -- not that a live model performed either behavior.
"""

import importlib.util
import os
import re
import subprocess
import sys

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL_DIR = os.path.join(REPO, "skills", "stow")
KERNEL = os.path.join(SKILL_DIR, "SKILL.md")
ALWAYS_ON = os.path.join(SKILL_DIR, "references", "always-on.md")
REGISTRY = os.path.join(SKILL_DIR, "rules", "registry.yaml")
GEN = os.path.join(REPO, "tools", "gen_always_on.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


measure_context = _load_module(
    "measure_context_for_always_on",
    os.path.join(REPO, "tools", "measure_context.py"))

# Measured budgets (o200k_base). The composition-hardening pass carries each
# action check's rule id, applicability condition, and principal exception into
# the module, plus the request-mode router and the compact descriptive digest.
#
# Mode-aware caps: the REAL caps bind when the tokenizer cache is available;
# the EST caps bind under the deterministic chars/3.5 fallback, which
# over-counts (measured 8-38% on shipped files), so each EST cap is the REAL
# cap scaled for that headroom. Ceilings are enforced in BOTH modes.
_ENCODER = measure_context.get_encoder()
_TOKENIZER_MODE = _ENCODER is not None

ALWAYS_ON_TOKEN_CAP = 1400 if _TOKENIZER_MODE else 1750
KERNEL_TOKEN_CEILING = 1500  # holds in both modes (kernel is small and dense)
ORDINARY_TURN_CAP = 2400 if _TOKENIZER_MODE else 3026

DESCRIPTIVE_LEAVES = (
    "semantic repetition",
    "empty metadiscourse",
    "manufactured contrast or escalation",
    "hollow evaluation",
    "mechanical symmetry or fragmentation",
    "heading opacity or unnecessary sectioning",
    "epistemic opacity",
    "lexical inflation or cliché clusters",
)

KERNEL_ALONE_LINE = (
    "Do not read every reference or corpus module. "
    "When no predicate is true, answer from this kernel alone."
)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _tokens(text):
    return measure_context.count_tokens(text, _ENCODER)


def _always_on_records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = yaml.load(fh)
    recs = reg.get("records") or reg.get("rules")
    return [r for r in recs if (r.get("activation") or {}).get("always_on_for_prose")]


def _all_records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = yaml.load(fh)
    return reg.get("records") or reg.get("rules")


# --------------------------------------------------------------------------- #
# 1. the module exists, is generated, and is current
# --------------------------------------------------------------------------- #

def test_always_on_module_exists():
    assert os.path.isfile(ALWAYS_ON), "always-on.md is missing"
    assert _read(ALWAYS_ON).strip(), "always-on.md is empty"


def test_always_on_is_current_with_registry():
    """Regeneration is deterministic: the committed file matches the registry."""
    result = subprocess.run([sys.executable, GEN, "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, "always-on.md is stale: %s" % result.stdout


# --------------------------------------------------------------------------- #
# 2. every always-on rule is represented
# --------------------------------------------------------------------------- #

def test_every_always_on_action_rule_is_present():
    text = _read(ALWAYS_ON)
    records = [r for r in _always_on_records()
               if r["id"].startswith("STOW-ACT-")]
    assert records, "no records carry activation.always_on_for_prose"
    missing = [r["id"] for r in records if r["title"].strip() not in text]
    assert not missing, "always-on rules absent from the module: %s" % missing


def test_moved_action_rules_are_not_in_the_ordinary_payload():
    """Accepted MOVE decisions must reduce the hot path in the real registry."""
    moved = {"STOW-ACT-004", "STOW-ACT-005", "STOW-ACT-006"}
    records = {r["id"]: r for r in _always_on_records()}
    assert moved.isdisjoint(records)
    text = _read(ALWAYS_ON)
    for rule_id in moved:
        assert rule_id.replace("STOW-", "") not in text


def test_module_bullet_count_matches_selector():
    bullets = [ln for ln in _read(ALWAYS_ON).splitlines() if ln.startswith("- ")]
    actions = [r for r in _always_on_records()
               if r["id"].startswith("STOW-ACT-")]
    assert len(bullets) == len(actions) + len(DESCRIPTIVE_LEAVES)


def test_every_action_bullet_cites_its_corpus_module():
    """Full action-rule statements stay behind their corpus module pointers."""
    for line in _read(ALWAYS_ON).splitlines():
        if re.match(r"^- ACT-\d{3} ", line):
            assert re.search(r"\(see corpus/[\w./-]+\.md(?:#[\w-]+)?\)", line), line


def test_descriptive_digest_has_exactly_the_eight_named_leaves():
    text = _read(ALWAYS_ON)
    digest = text.split("## Descriptive prose digest", 1)[1]
    labels = [line[2:].split(":", 1)[0] for line in digest.splitlines()
              if line.startswith("- ")]
    assert labels == list(DESCRIPTIVE_LEAVES)


# --------------------------------------------------------------------------- #
# 3. the kernel carries ordinary prose guidance and keeps detail cold
# --------------------------------------------------------------------------- #

def test_kernel_keeps_generated_detail_cold_for_explicit_review():
    kernel = _read(KERNEL)
    assert "references/always-on.md" in kernel, "kernel never routes to always-on.md"
    line = next(ln for ln in kernel.splitlines() if "references/always-on.md" in ln)
    assert "explicit" in line.casefold(), line
    assert "rule-audit" in line.casefold(), line


def test_kernel_excludes_protected_regions_from_ordinary_guidance():
    """A raw artifact must not receive editable-prose guidance."""
    line = next(ln for ln in _read(KERNEL).splitlines()
                if "ordinary editable user-facing prose ->" in ln)
    assert re.search(r"exclud", line, re.I), line
    for token in ("raw data", "code"):
        assert token in line, "protected-region exclusion does not name %s" % token


def test_kernel_routes_meta_code_artifacts():
    assert "references/meta-code.md" in _read(KERNEL)


# --------------------------------------------------------------------------- #
# 4/5. bounded footprint + the no-greedy-loading rule survives
# --------------------------------------------------------------------------- #

def test_always_on_module_within_budget():
    assert _tokens(_read(ALWAYS_ON)) <= ALWAYS_ON_TOKEN_CAP


def test_kernel_within_ceiling():
    assert _tokens(_read(KERNEL)) <= KERNEL_TOKEN_CEILING


def test_ordinary_prose_turn_footprint_is_bounded():
    total = _tokens(_read(KERNEL))
    assert total <= ORDINARY_TURN_CAP, "ordinary prose turn costs %d tokens" % total


def test_kernel_keeps_no_greedy_loading_rule():
    assert KERNEL_ALONE_LINE in _read(KERNEL)


def test_kernel_does_not_inline_corpus():
    """Tier-3 material must not be pulled into the always-loaded kernel."""
    kernel = _read(KERNEL)
    assert not re.search(r"corpus/[\w./-]+\.md", kernel), \
        "kernel inlines a concrete corpus module path"


# --------------------------------------------------------------------------- #
# 6. operational qualifiers survive generation; the router exists
# --------------------------------------------------------------------------- #

def test_every_action_qualifier_appears_in_the_module():
    """Action checks remain individually operational in the compact module."""
    text = _read(ALWAYS_ON)
    qualified = [r for r in _always_on_records()
                 if r["id"].startswith("STOW-ACT-")
                 if (r["activation"].get("applicability")
                     or r["activation"].get("exception"))]
    assert qualified, "no always-on action record carries an operational qualifier"
    for record in qualified:
        applicability = record["activation"].get("applicability")
        exception = record["activation"].get("exception")
        if applicability:
            assert applicability in text, (
                "%s applicability lost from always-on.md" % record["id"])
        if exception:
            assert exception in text, (
                "%s exception lost from always-on.md" % record["id"])


def test_the_known_condition_bearing_rules_carry_qualifiers():
    """The flagship qualifier-loss set from the composition audit: these
    records MUST have a non-empty applicability or exception in the registry.
    Removing the field is a regression even if generation stays faithful."""
    required = {
        "STOW-ACT-001", "STOW-ACT-004", "STOW-ACT-005", "STOW-ACT-006",
        "STOW-ACT-007", "STOW-PRO-002", "STOW-PRO-005", "STOW-PRO-006",
        "STOW-PRO-007", "STOW-PRO-009", "STOW-PRO-011", "STOW-PRO-013",
        "STOW-PRO-015", "STOW-PRO-017", "STOW-PRO-019",
    }
    by_id = {r["id"]: r for r in _all_records()}
    for rule_id in sorted(required):
        activation = by_id[rule_id]["activation"]
        assert activation.get("applicability") or activation.get("exception"), (
            "%s lost its operational qualifier fields" % rule_id)


def test_bullets_carry_short_rule_ids():
    text = _read(ALWAYS_ON)
    for record in _always_on_records():
        if not record["id"].startswith("STOW-ACT-"):
            continue
        short_id = record["id"].replace("STOW-", "", 1)
        assert re.search(r"^- %s " % re.escape(short_id), text, re.M), (
            "%s bullet does not lead with its id" % record["id"])


def test_request_mode_router_is_present_and_complete():
    text = _read(ALWAYS_ON)
    assert "## Request-mode router" in text
    for mode in ("informational question", "explanation", "actionable task",
                 "requested artifact", "raw artifact", "progress update",
                 "error report", "completed work", "open work"):
        assert re.search(r"^  %s:" % re.escape(mode), text, re.M), (
            "router misses the %r mode" % mode)


def test_router_rows_are_not_check_bullets():
    """Router rows must never inflate the check count."""
    text = _read(ALWAYS_ON)
    router = text.split("## Request-mode router", 1)[1].split("##", 1)[0]
    assert not any(ln.startswith("- ") for ln in router.splitlines())


def test_header_carries_the_accuracy_override():
    head = _read(ALWAYS_ON).split("##", 1)[0]
    for token in ("yield to safety", "justified uncertainty",
                  "material limitation or failed verification",
                  "hypothetical that is labeled as one", "conflicts.yaml"):
        assert token in head, "always-on header lost %r" % token


def test_digest_rejects_authorship_labels_and_routes_contextual_review():
    digest = _read(ALWAYS_ON).split("## Descriptive prose digest", 1)[1]
    assert "Authorship is irrelevant." in digest
    assert "references/descriptive-prose.md" in digest
    for label in ("AI", "machine-written", "human-written", "generated text"):
        assert label not in digest


def test_no_em_dash_in_the_generated_module():
    """The module that carries the no-em-dash check must not use one."""
    assert u"—" not in _read(ALWAYS_ON)
