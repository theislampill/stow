"""P6 adversarial-evals gate.

Validates the adversarial-evals register (``tests/evals/adversarial.yaml``): that
it enumerates all 14 named adversarial dimensions plus the 15th reviewer entry
(reference-paraphrase review), that every disposition carries BOTH a written
rationale AND a concrete evidence pointer (no bare label), that the dimensions
which map to an existing mechanical gate name that gate, and that the
controlled-technical strict / fully conformant profile is documented as LOCKED.

It also pins one residual: the narrative rule count in ``README.md`` must equal
the registry's committed primary total (the README/registry-drift dimension).

Source-name-free: this module names none of the external projects the rules were
derived from, so the whole repository stays clean when the anti-leak gate scans
it. The register is loaded with ruamel ``YAML(typ="safe")``.
"""

import os
import re

import pytest
from ruamel.yaml import YAML

# --------------------------------------------------------------------------- #
# Paths (resolved from this file, independent of the working directory)
# --------------------------------------------------------------------------- #

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ADVERSARIAL_PATH = os.path.join(HERE, "evals", "adversarial.yaml")
README_PATH = os.path.join(REPO, "README.md")
REGISTRY_PATH = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
CONFORMANCE_PATH = os.path.join(REPO, "skills", "stow", "references", "conformance.md")
DESIGN_PATH = os.path.join(REPO, "docs", "design.md")

# --------------------------------------------------------------------------- #
# Contract constants
# --------------------------------------------------------------------------- #

# The 14 named dimensions (by number) plus the 15th reviewer entry. The slugs are
# the canonical kebab-case identifiers the register must carry.
EXPECTED_DIMENSIONS = {
    1: "context-explosion",
    2: "greedy-reference-corpus-loading",
    3: "cross-source-rule-conflict",
    4: "raw-artifact-corruption",
    5: "quotation-mutation",
    6: "identifier-key-mutation",
    7: "unsupported-specificity",
    8: "suppressed-justified-uncertainty",
    9: "false-conformance-claim",
    10: "rule-count-drift",
    11: "readme-registry-drift",
    12: "prompt-injection-from-source-content",
    13: "non-deterministic-package",
    14: "provenance-source-name-leak",
    15: "reference-paraphrase-review",  # the named-reviewer (E8 proxy) entry
}

VALID_LABELS = frozenset({
    "fixed", "already-covered", "rejected-with-evidence",
    "owner-decision", "blocked", "deferred",
})

# An evidence pointer must point at something concrete: a test node, a source
# file, or a runnable gate. These markers make "no bare label" enforceable.
EVIDENCE_MARKERS = ("::", ".py", ".md", ".yaml", "tools/", "tests/", "--check", "--local")

# Dimensions that map to an existing mechanical gate MUST name that gate.
# (slug -> substrings the `gate` field must contain).
NAMED_GATE_REQUIREMENTS = {
    "rule-count-drift": ("gen_rule_index", "--check"),
    "provenance-source-name-leak": ("check_provenance_leak", "--local"),
    "non-deterministic-package": ("build test",),  # the P7 build test
}

# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _load_yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle)


REGISTER = _load_yaml(ADVERSARIAL_PATH)
ENTRIES = REGISTER["entries"]
BY_DIMENSION = {e["dimension"]: e for e in ENTRIES}
BY_NUMBER = {e["number"]: e for e in ENTRIES}


# --------------------------------------------------------------------------- #
# Sanity
# --------------------------------------------------------------------------- #

def test_register_loads_and_has_entries():
    assert isinstance(ENTRIES, list) and ENTRIES, "adversarial.yaml has no entries"


# --------------------------------------------------------------------------- #
# Completeness -- all 14 dimensions plus the paraphrase reviewer entry
# --------------------------------------------------------------------------- #

def test_all_fourteen_dimensions_plus_paraphrase_present():
    got = set(BY_DIMENSION)
    expected = set(EXPECTED_DIMENSIONS.values())
    missing = expected - got
    assert not missing, "adversarial.yaml is missing dimensions: %s" % sorted(missing)
    extra = got - expected
    assert not extra, "adversarial.yaml has unexpected dimensions: %s" % sorted(extra)
    # 14 named dimensions + 1 reviewer entry.
    assert len(ENTRIES) == 15, "expected exactly 15 entries, got %d" % len(ENTRIES)


def test_dimension_numbers_map_one_to_one():
    for number, slug in EXPECTED_DIMENSIONS.items():
        assert number in BY_NUMBER, "no entry carries dimension number %d" % number
        assert BY_NUMBER[number]["dimension"] == slug, (
            "dimension number %d is %r, expected %r"
            % (number, BY_NUMBER[number]["dimension"], slug))
    assert len(BY_NUMBER) == len(ENTRIES), "duplicate dimension numbers present"


def test_paraphrase_reviewer_entry_points_at_e8_proxy_gate():
    entry = BY_DIMENSION["reference-paraphrase-review"]
    blob = (entry["defense"] + " " + entry["disposition"]["rationale"] + " "
            + entry["disposition"]["evidence"] + " " + entry.get("gate", "")).lower()
    assert "e8" in blob, "paraphrase entry does not name the E8 proxy"
    assert "test_references.py" in blob, (
        "paraphrase entry does not point at tests/test_references.py")
    assert "baseline_text" in blob or "no-paraphrase" in blob or "verbatim" in blob, (
        "paraphrase entry does not describe the no-verbatim/no-paraphrase check")


# --------------------------------------------------------------------------- #
# Structural fields present on every entry
# --------------------------------------------------------------------------- #

def test_every_entry_has_required_fields():
    for entry in ENTRIES:
        for field in ("id", "dimension", "number", "attack", "defense", "disposition"):
            assert field in entry, "entry %r is missing field %r" % (
                entry.get("id", "<no id>"), field)
        assert entry["attack"].strip(), "%s has an empty attack scenario" % entry["id"]
        assert entry["defense"].strip(), "%s has an empty defense" % entry["id"]


def test_entry_ids_are_unique():
    ids = [e["id"] for e in ENTRIES]
    assert len(ids) == len(set(ids)), "duplicate entry ids: %s" % ids


# --------------------------------------------------------------------------- #
# Disposition integrity -- rationale AND evidence, never a bare label
# --------------------------------------------------------------------------- #

def test_every_disposition_label_is_valid():
    for entry in ENTRIES:
        label = entry["disposition"]["label"]
        assert label in VALID_LABELS, (
            "%s has invalid disposition label %r" % (entry["id"], label))


def test_every_disposition_carries_rationale_and_evidence():
    for entry in ENTRIES:
        disp = entry["disposition"]
        rationale = (disp.get("rationale") or "").strip()
        evidence = (disp.get("evidence") or "").strip()

        assert len(rationale) >= 20, (
            "%s disposition has no real rationale (a bare label): %r"
            % (entry["id"], rationale))
        assert evidence, (
            "%s disposition has no evidence pointer (a bare label)" % entry["id"])
        assert any(m in evidence for m in EVIDENCE_MARKERS), (
            "%s disposition evidence names no concrete test/file/gate: %r"
            % (entry["id"], evidence))


def test_bare_label_disposition_would_be_rejected():
    """Teeth: a synthetic disposition that is only a label (no rationale, no
    evidence) must fail the integrity checks the register enforces."""
    bare = {"label": "already-covered", "rationale": "", "evidence": ""}
    rationale = (bare.get("rationale") or "").strip()
    evidence = (bare.get("evidence") or "").strip()
    assert not (len(rationale) >= 20)
    assert not evidence
    # And an evidence string that is mere prose (no concrete pointer) is rejected.
    prose_only = "we handle this carefully everywhere"
    assert not any(m in prose_only for m in EVIDENCE_MARKERS)


# --------------------------------------------------------------------------- #
# Named mechanical gates -- must be named where a dimension maps to one
# --------------------------------------------------------------------------- #

def test_mapped_dimensions_name_their_gate():
    for slug, required in NAMED_GATE_REQUIREMENTS.items():
        entry = BY_DIMENSION[slug]
        gate = (entry.get("gate") or "").strip()
        assert gate, "%s (%s) names no gate" % (entry["id"], slug)
        for token in required:
            assert token in gate, (
                "%s (%s) gate %r does not name %r"
                % (entry["id"], slug, gate, token))


def test_already_covered_and_fixed_entries_name_a_gate():
    """Any dimension disposed as already-covered or fixed must point at a runnable
    gate (either the `gate` field or a test node in its evidence)."""
    for entry in ENTRIES:
        if entry["disposition"]["label"] not in ("already-covered", "fixed"):
            continue
        gate = (entry.get("gate") or "").strip()
        evidence = entry["disposition"]["evidence"]
        assert gate or "::" in evidence or ".py" in evidence, (
            "%s is %s but names no runnable gate"
            % (entry["id"], entry["disposition"]["label"]))


# --------------------------------------------------------------------------- #
# LOCKED strict / conformant profile is documented
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", [CONFORMANCE_PATH, DESIGN_PATH])
def test_strict_conformant_profile_documented_as_locked(path):
    text = _read(path)
    low = text.lower()
    assert "profile" in low, "%s does not mention a profile" % os.path.basename(path)
    assert re.search(r"\block(?:ed)?\b", low), (
        "%s does not document the profile as LOCKED" % os.path.basename(path))
    assert re.search(r"strict|conformant|conformance", low), (
        "%s does not tie 'locked' to the strict/conformant profile"
        % os.path.basename(path))


# --------------------------------------------------------------------------- #
# README / registry drift residual -- README rule count == registry primary_total
# --------------------------------------------------------------------------- #

def _registry_primary_total():
    reg = _load_yaml(REGISTRY_PATH)
    return int(reg["generated_counts"]["primary_total"])


def test_readme_rule_count_matches_registry():
    total = _registry_primary_total()
    readme = _read(README_PATH)

    counts = [int(n) for n in re.findall(r"(\d+)\s+rules\b", readme)]
    counts += [int(n) for n in re.findall(r"indexes\s+(\d+)", readme)]

    assert counts, "README.md states no rule count to check against the registry"
    for value in counts:
        assert value == total, (
            "README.md advertises %d rules but the registry primary_total is %d"
            % (value, total))
