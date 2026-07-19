"""Gates for the machine-readable conflict registry (rules/conflicts.yaml).

Pinned properties:
  * shape: required fields, unique CFL ids, valid kinds and bands;
  * coverage: at least the sixteen composition pairs this pass hardened;
  * registry fidelity: every conflicts[] edge in registry.yaml appears here
    with the VERBATIM edge resolution, and the enrichment never extends it
    (permitted_substitute is a substring of the registry resolution);
  * terminality: every entry names a winner band, a losing behavior, and a
    permitted substitute; same-band rule pairs carry a tie-break or are
    semantic-review;
  * generation: docs/rule-conflicts.md is current (via the generator --check).

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
CONFLICTS = os.path.join(REPO, "skills", "stow", "rules", "conflicts.yaml")
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
GENERATOR = os.path.join(REPO, "tools", "gen_rule_conflicts.py")

BANDS = {"system", "contract", "serialization", "literals", "accuracy",
         "terminology", "profile", "presentation"}
KINDS = {"rule", "kernel-duty", "band"}
RESOLUTION_KINDS = {"deterministic", "semantic-review"}

REQUIRED_FIELDS = ("id", "origin", "participants", "activation_predicate",
                   "winner", "losing_behavior", "permitted_substitute",
                   "resolution_kind", "fixtures", "evidence")


def _yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh)


DATA = _yaml(CONFLICTS)
ENTRIES = DATA["conflicts"]
REG = _yaml(REGISTRY)
RECORDS = {r["id"]: r for r in REG["records"]}

PRECEDENCE_BY_ID = {r["id"]: r.get("precedence") for r in REG["records"]}


def _registry_edges():
    edges = {}
    for record in REG["records"]:
        for edge in (record.get("conflicts") or []):
            edges[(record["id"], edge["rule"])] = edge["resolution"]
    return edges


REGISTRY_EDGES = _registry_edges()


# --------------------------------------------------------------------------- #
# Shape
# --------------------------------------------------------------------------- #

def test_schema_version_and_minimum_count():
    assert DATA["schema_version"] == 1
    assert len(ENTRIES) >= 16


def test_ids_are_unique_and_well_formed():
    ids = [e["id"] for e in ENTRIES]
    assert len(ids) == len(set(ids))
    for entry_id in ids:
        assert re.fullmatch(r"CFL-\d{3}", entry_id), entry_id


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_entry_shape(entry):
    for field in REQUIRED_FIELDS:
        assert entry.get(field), "%s missing %s" % (entry["id"], field)
    assert entry["origin"] in ("registry", "composition")
    assert entry["resolution_kind"] in RESOLUTION_KINDS
    assert len(entry["participants"]) == 2
    for participant in entry["participants"]:
        assert participant["kind"] in KINDS
        if participant["kind"] == "rule":
            assert participant["ref"] in RECORDS, (
                "%s names unknown rule %s" % (entry["id"], participant["ref"]))
    assert entry["winner"]["band"] in BANDS
    fixtures = entry["fixtures"]
    assert fixtures.get("positive") and fixtures.get("adversarial")


# --------------------------------------------------------------------------- #
# Registry fidelity -- the eight imported pairs
# --------------------------------------------------------------------------- #

def test_every_registry_edge_is_covered_verbatim():
    imported = {e["id"]: e for e in ENTRIES if e["origin"] == "registry"}
    covered_pairs = set()
    for entry in imported.values():
        refs = tuple(sorted(p["ref"] for p in entry["participants"]))
        covered_pairs.add(refs)
        for a, b in ((refs[0], refs[1]), (refs[1], refs[0])):
            assert (a, b) in REGISTRY_EDGES, (
                "%s claims registry origin but no edge %s->%s exists"
                % (entry["id"], a, b))
            assert entry["registry_resolution"] == REGISTRY_EDGES[(a, b)], (
                "%s registry_resolution diverges from the %s->%s edge"
                % (entry["id"], a, b))
    registry_pairs = {tuple(sorted(k)) for k in REGISTRY_EDGES}
    assert registry_pairs == covered_pairs, (
        "registry conflicts[] pairs not mirrored: %s"
        % registry_pairs.symmetric_difference(covered_pairs))


def test_imported_substitutes_never_extend_the_registry_resolution():
    for entry in ENTRIES:
        if entry["origin"] != "registry":
            continue
        assert entry["permitted_substitute"] in entry["registry_resolution"], (
            "%s permitted_substitute is not a verbatim substring of the "
            "registry resolution" % entry["id"])


def test_composition_entries_carry_no_registry_resolution():
    for entry in ENTRIES:
        if entry["origin"] == "composition":
            assert "registry_resolution" not in entry, entry["id"]


# --------------------------------------------------------------------------- #
# Terminality and same-band discipline
# --------------------------------------------------------------------------- #

def test_same_band_rule_pairs_carry_a_tie_break_or_semantic_review():
    for entry in ENTRIES:
        rule_refs = [p["ref"] for p in entry["participants"]
                     if p["kind"] == "rule"]
        if len(rule_refs) != 2:
            continue
        bands = {PRECEDENCE_BY_ID[r] for r in rule_refs}
        if len(bands) == 1:
            assert entry.get("tie_break") or \
                entry["resolution_kind"] == "semantic-review", (
                    "%s is a same-band pair with no tie-break" % entry["id"])


def test_winner_ref_is_a_participant_or_band():
    for entry in ENTRIES:
        refs = {p["ref"] for p in entry["participants"]}
        assert entry["winner"]["ref"] in refs or \
            entry["winner"]["ref"] in BANDS, entry["id"]


# --------------------------------------------------------------------------- #
# Required composition coverage -- the sixteen hardened pairs
# --------------------------------------------------------------------------- #

# participant-ref pairs that must exist, one per required conflict class.
REQUIRED_PAIRS = [
    {"STOW-ACT-001", "result-first"},            # action-first vs answer-first
    {"STOW-ACT-003", "STOW-ACT-007"},            # next action vs completed work
    {"STOW-ACT-009", "contract"},                # list cap vs exhaustive list
    {"STOW-PRO-015", "accuracy"},                # anti-hedging vs uncertainty
    {"STOW-PRO-024", "accuracy"},                # narration vs material limitation
    {"STOW-PRO-005", "contract"},                # concrete detail vs conceptual
    {"STOW-PRO-013", "contract"},                # researcher tone vs requested voice
    {"STOW-PRO-017", "contract"},                # fabrication vs labeled hypothetical
    {"STOW-PRO-021", "terminology"},             # banned terms vs technical senses
    {"STOW-WRD-014", "contract"},                # regional spelling vs style directive
    {"STOW-ACT-005", "STOW-PRO-024"},            # progress state vs narration
    {"STOW-PRC-001", "STOW-PRO-007"},            # caps vs variation
    {"STOW-WRD-011", "STOW-PRO-007"},            # terminology vs variation
    {"STOW-PCT-001", "STOW-PRO-001"},            # semicolon vs em dash
    {"STOW-WRD-014", "STOW-PRO-021"},            # protected literals vs preferences
    {"STOW-SAF-001", "STOW-ACT-009"},            # safety vs brevity and caps
]


@pytest.mark.parametrize("pair", REQUIRED_PAIRS,
                         ids=["+".join(sorted(p)) for p in REQUIRED_PAIRS])
def test_required_pair_is_covered(pair):
    for entry in ENTRIES:
        refs = {p["ref"] for p in entry["participants"]}
        if refs == pair:
            return
    pytest.fail("no conflict entry covers %s" % sorted(pair))


def test_expected_rewrites_accompany_the_narration_pairs():
    """The two narration-adjacent pairs teach the split with a rewrite."""
    for entry_id in ("CFL-013", "CFL-019"):
        entry = next(e for e in ENTRIES if e["id"] == entry_id)
        assert entry["fixtures"].get("expected_rewrite"), entry_id
        assert "tie_break" in entry, entry_id


# --------------------------------------------------------------------------- #
# Leak discipline inside the registry file itself
# --------------------------------------------------------------------------- #

def test_no_hex_hashes_in_the_conflict_registry():
    text = open(CONFLICTS, encoding="utf-8").read()
    assert not re.search(r"\b[0-9a-f]{64}\b", text)


# --------------------------------------------------------------------------- #
# Generation -- the human document derives from this file
# --------------------------------------------------------------------------- #

def test_generated_document_is_current():
    proc = subprocess.run(
        [sys.executable, GENERATOR, "--check"],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "current" in proc.stdout


def test_generated_document_declares_its_provenance():
    doc = open(os.path.join(REPO, "docs", "rule-conflicts.md"),
               encoding="utf-8").read()
    assert "GENERATED FILE" in doc
    assert "conflicts.yaml" in doc
    assert "gen_rule_conflicts.py" in doc
