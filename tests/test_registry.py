"""P2 tests for the STOW machine-readable rule registry (index of 96 records).

Self-contained: no corpus dependency (the corpus arrives in P2B) and no
dependency on a runtime validate.py (it does not exist yet). The registry is
loaded with ruamel ``YAML(typ='safe')`` and validated against the committed JSON
Schema via ``jsonschema``.

No source-project name appears in this file; every negative fixture that must
FAIL the anti-leak gate is synthesised from tokens loaded out of the UNCOMMITTED
private pattern file, so the whole repository stays clean when scanned.
"""

import copy
import hashlib
import importlib.util
import os

import pytest
from jsonschema import Draft202012Validator
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY_PATH = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
SCHEMA_PATH = os.path.join(REPO, "skills", "stow", "rules", "registry.schema.json")
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")
HASH_POS = os.path.join(REPO, "tools", "hash-positions.txt")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))

REGISTRY_REL = "skills/stow/rules/registry.yaml"

# Expected per-domain counts (live in the TEST, never committed to the registry).
EXPECTED_COUNTS = {
    "WRD": 14, "MWN": 2, "VRB": 7, "SEN": 5, "PRC": 5, "DSC": 6,
    "SAF": 3, "PCT": 7, "STY": 4, "GEN": 8, "ACT": 11, "PRO": 24,
}

# precedence prefix -> enum EQUALITY table (the deciding authority).
PRECEDENCE_TABLE = {
    "SAF": "system",
    "WRD": "profile", "MWN": "profile", "VRB": "profile", "SEN": "profile",
    "PRC": "profile", "DSC": "profile", "PCT": "profile", "STY": "profile",
    "GEN": "profile",
    "ACT": "presentation", "PRO": "presentation",
}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def _load_yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh)


def _load_json(path):
    import json
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_provenance_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REGISTRY = _load_yaml(REGISTRY_PATH)
SCHEMA = _load_json(SCHEMA_PATH)
RECORDS = REGISTRY["records"]
IDS = [r["id"] for r in RECORDS]
ID_SET = set(IDS)

MOD = _load_checker()
_PATTERN_DATA = MOD.load_patterns(PATTERNS_PATH)


def _prefix(record_id):
    return record_id.split("-")[1]


def _precedence_ok(record):
    """EQUALITY check used by both the GREEN pass and the RED assertions."""
    return record["precedence"] == PRECEDENCE_TABLE[_prefix(record["id"])]


# --------------------------------------------------------------------------- #
# Schema + shape
# --------------------------------------------------------------------------- #

def test_registry_matches_schema():
    Draft202012Validator.check_schema(SCHEMA)
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(REGISTRY),
                    key=lambda e: e.path)
    assert errors == [], "\n".join(
        "%s: %s" % (list(e.path), e.message) for e in errors)


def test_exactly_96_primary_records():
    assert len(RECORDS) == 96
    assert all(r["record_class"] == "primary" for r in RECORDS)


def test_ids_unique_and_well_formed():
    import re
    assert len(IDS) == len(ID_SET)
    pat = re.compile(r"^STOW-(WRD|MWN|VRB|SEN|PRC|DSC|SAF|PCT|STY|GEN|ACT|PRO)-\d{3}$")
    for rid in IDS:
        assert pat.match(rid), rid


def test_domain_counts_and_total():
    from collections import Counter
    got = Counter(_prefix(rid) for rid in IDS)
    assert dict(got) == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS.values()) == 96
    assert REGISTRY["generated_counts"]["primary_total"] == 96


def test_generated_counts_has_no_per_domain_totals():
    # Only the grand total is committed; per-domain counts live in the test.
    assert set(REGISTRY["generated_counts"].keys()) == {"primary_total"}


def test_every_record_has_retention_activation_enforcement():
    for r in RECORDS:
        assert r["retention"] == "retained"
        assert r["activation"]["kind"] in ("conditional", "always-user-facing")
        assert r["activation"]["predicate"].strip()
        assert r["enforcement"]["kind"] in (
            "deterministic", "parser", "heuristic", "semantic-review")
        assert r["enforcement"]["autofix"] is False


def test_conflicts_reference_existing_ids_with_nonempty_resolution():
    seen = False
    for r in RECORDS:
        for c in r["conflicts"]:
            seen = True
            assert c["rule"] in ID_SET, "%s -> unknown %s" % (r["id"], c["rule"])
            assert c["rule"] != r["id"], "%s references itself" % r["id"]
            assert isinstance(c["resolution"], str) and c["resolution"].strip()
    assert seen, "at least one conflict entry must exist for the RED leak test"


def test_conflicts_are_reciprocal():
    edges = {(r["id"], c["rule"]) for r in RECORDS for c in r["conflicts"]}
    for a, b in edges:
        assert (b, a) in edges, "conflict %s->%s is not reciprocated" % (a, b)


# --------------------------------------------------------------------------- #
# baseline_text integrity (sha256 recomputation)
# --------------------------------------------------------------------------- #

def test_baseline_text_sha256_roundtrip():
    for r in RECORDS:
        w = r["wording"]
        assert w["baseline_kind"] == "verbatim"
        recomputed = hashlib.sha256(w["baseline_text"].encode("utf-8")).hexdigest()
        assert recomputed == w["baseline_text_sha256"], r["id"]


# --------------------------------------------------------------------------- #
# precedence EQUALITY table
# --------------------------------------------------------------------------- #

def test_precedence_equals_table_for_every_record():
    for r in RECORDS:
        assert _precedence_ok(r), \
            "%s precedence=%s expected %s" % (
                r["id"], r["precedence"], PRECEDENCE_TABLE[_prefix(r["id"])])


def test_exactly_three_safety_records():
    saf = [r for r in RECORDS if _prefix(r["id"]) == "SAF"]
    assert len(saf) == 3
    assert all(r["precedence"] == "system" for r in saf)


def test_red_saf_with_profile_precedence_fails_check():
    """RED-style unit assertion: a SAF record forced to precedence 'profile'
    must FAIL the equality check (the real records all pass it)."""
    saf = next(r for r in RECORDS if _prefix(r["id"]) == "SAF")
    broken = copy.deepcopy(saf)
    broken["precedence"] = "profile"
    assert _precedence_ok(saf) is True
    assert _precedence_ok(broken) is False


# --------------------------------------------------------------------------- #
# RED first: broken-fixture registries must be rejected by the gate logic
# --------------------------------------------------------------------------- #

def _has_duplicate_ids(records):
    ids = [r["id"] for r in records]
    return len(ids) != len(set(ids))


def _all_resolutions_nonempty(records):
    return all(
        isinstance(c["resolution"], str) and c["resolution"].strip()
        for r in records for c in r["conflicts"])


def test_broken_fixtures_are_rejected_but_real_registry_passes():
    # GREEN: the real registry passes all three structural gates.
    assert not _has_duplicate_ids(RECORDS)
    assert _all_resolutions_nonempty(RECORDS)
    assert all(_precedence_ok(r) for r in RECORDS)

    # RED 1 -- duplicate id.
    dup = copy.deepcopy(RECORDS)
    dup[1]["id"] = dup[0]["id"]
    assert _has_duplicate_ids(dup)

    # RED 2 -- missing (empty) conflict resolution.
    missing = copy.deepcopy(RECORDS)
    victim = next(r for r in missing if r["conflicts"])
    victim["conflicts"][0]["resolution"] = ""
    assert not _all_resolutions_nonempty(missing)

    # RED 3 -- precedence != table.
    bent = copy.deepcopy(RECORDS)
    saf = next(r for r in bent if _prefix(r["id"]) == "SAF")
    saf["precedence"] = "presentation"
    assert not all(_precedence_ok(r) for r in bent)


def test_broken_fixture_registry_fails_schema():
    # A structurally broken registry (wrong primary_total, 95 records) must be
    # rejected by the JSON Schema, proving the schema gate has teeth.
    broken = copy.deepcopy(REGISTRY)
    broken["records"] = broken["records"][:-1]
    broken["generated_counts"]["primary_total"] = 95
    errors = list(Draft202012Validator(SCHEMA).iter_errors(broken))
    assert errors, "schema should reject a 95-record registry"


# --------------------------------------------------------------------------- #
# Field-level anti-leak gate (skipped when the private pattern file is absent)
# --------------------------------------------------------------------------- #

_leak = pytest.mark.skipif(
    _PATTERN_DATA is None,
    reason="private pattern file not present (weak/CI environment)")


@_leak
def test_registry_passes_source_name_gate():
    patterns = MOD.Patterns(_PATTERN_DATA)
    hash_specs = MOD.load_hash_positions(HASH_POS)
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        text = fh.read()
    findings = MOD.scan_file(REGISTRY_REL, text, patterns, True, hash_specs)
    assert findings == [], "unexpected leak findings: %r" % findings


@_leak
def test_source_name_planted_in_resolution_fails_gate():
    """A source name planted into a conflicts[].resolution (a non-baseline,
    STOW-authored field) MUST be caught by the field-level gate."""
    patterns = MOD.Patterns(_PATTERN_DATA)
    hash_specs = MOD.load_hash_positions(HASH_POS)
    word_token = patterns.word_tokens[0]        # e.g. an uppercase abbreviation
    phrase_token = next(p for p in patterns.phrase_tokens
                        if "-" in p and " " not in p)

    word_line = "      - rule: STOW-PCT-001\n        resolution: The %s profile wins here.\n" % word_token
    assert MOD.scan_file(REGISTRY_REL, word_line, patterns, True, hash_specs) != []

    phrase_line = "        resolution: derived from %s upstream\n" % phrase_token
    assert MOD.scan_file(REGISTRY_REL, phrase_line, patterns, True, hash_specs) != []


@_leak
def test_baseline_field_is_not_exempt_from_source_name_gate():
    """The registry is fully STOW-native: a source-like token planted into a
    baseline_text field is caught like anywhere else (no exempt surfaces)."""
    patterns = MOD.Patterns(_PATTERN_DATA)
    hash_specs = MOD.load_hash_positions(HASH_POS)
    word_token = patterns.word_tokens[0]
    line = '      baseline_text: "Use the %s dictionary as written."\n' % word_token
    assert MOD.scan_file(REGISTRY_REL, line, patterns, True, hash_specs) != []
