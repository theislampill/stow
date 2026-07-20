"""Enrichment tests: enforcement.status (R1) and activation.always_on_for_prose
(R5-field), plus the meta-contract catalog kept outside primary_total.

Self-contained: loads the registry with ruamel ``YAML(typ='safe')`` and validates
against the committed JSON Schema via ``jsonschema``. No source-project name,
path, hash, or URL appears in this file.

Truthfulness model (per the runtime-enforcement matrix):
  * ``semantic-review`` records are honestly ``review-fallback`` -- the intended
    mechanism is a model/human review pass, never shipped code.
  * A record whose ``enforcement.kind`` is mechanized (deterministic / parser /
    heuristic) may claim ``callable`` ONLY when its validator names a shipped
    callable. The callable set is DERIVED from the packaged linter's
    ``IMPLEMENTED_VALIDATORS``, never hardcoded, so it cannot drift.
  * Everything else mechanized-but-uncoded is ``planned``.
"""

import json
import os
import sys
from collections import Counter

from jsonschema import Draft202012Validator
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY_PATH = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
SCHEMA_PATH = os.path.join(REPO, "skills", "stow", "rules", "registry.schema.json")

# The single unconditional-prose predicate that, together with an
# always-user-facing activation kind, defines the always-on-for-prose set.
# Sub-region-gated predicates (section headings, external quotation) are
# deliberately NOT part of the always-on set.
PROSE_TURN_PREDICATE = (
    "The response contains prose sentences outside code, quoted text, "
    "and structured data."
)

# Validators backed by shipped, callable runtime code. DERIVED from the packaged
# runtime itself -- never hardcoded -- so this honesty gate cannot drift as the
# linter grows: a record may claim 'callable' only when the shipped linter really
# implements that validator, and an implemented validator may not be left
# under-claimed. This is the gate that stops the registry asserting code that
# does not run.
_RUNTIME_DIR = os.path.join(REPO, "skills", "stow", "runtime")
if _RUNTIME_DIR not in sys.path:
    sys.path.insert(0, _RUNTIME_DIR)
import lint_prose  # noqa: E402  (packaged runtime module; import-closed)

NAMED_CALLABLES = set(lint_prose.IMPLEMENTED_VALIDATORS)

MECHANIZED_KINDS = {"deterministic", "parser", "heuristic"}
VALID_STATUS = {"callable", "review-fallback", "planned"}

# Per-domain record counts (reference snapshot; must stay unchanged after the
# additive enrichment).
EXPECTED_DOMAIN_COUNTS = {
    "WRD": 14, "MWN": 2, "VRB": 7, "SEN": 5, "PRC": 5, "DSC": 6,
    "SAF": 3, "PCT": 7, "STY": 4, "GEN": 8, "ACT": 11, "PRO": 24,
    "EVD": 4, "AUT": 3, "ART": 1,
}


def _load_yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh)


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


REGISTRY = _load_yaml(REGISTRY_PATH)
SCHEMA = _load_json(SCHEMA_PATH)
RECORDS = REGISTRY["records"]


def _domain(rid):
    return rid.split("-")[1]


def _selector_always_on(rec):
    """The activation selector: always-user-facing OR the unconditional-prose
    predicate. Sub-region-gated conditional predicates are excluded."""
    act = rec["activation"]
    if act["kind"] == "always-user-facing":
        return True
    return (act["kind"] == "conditional"
            and act["predicate"] == PROSE_TURN_PREDICATE)


# --------------------------------------------------------------------------- #
# Schema still validates with the new fields
# --------------------------------------------------------------------------- #

def test_registry_still_matches_schema():
    Draft202012Validator.check_schema(SCHEMA)
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(REGISTRY),
                    key=lambda e: list(e.path))
    assert errors == [], "\n".join(
        "%s: %s" % (list(e.path), e.message) for e in errors)


# --------------------------------------------------------------------------- #
# R1 -- enforcement.status on every record
# --------------------------------------------------------------------------- #

def test_every_record_has_valid_enforcement_status():
    for r in RECORDS:
        enf = r["enforcement"]
        assert "status" in enf, r["id"]
        assert enf["status"] in VALID_STATUS, "%s -> %r" % (r["id"], enf["status"])


def test_semantic_review_records_are_review_fallback():
    for r in RECORDS:
        if r["enforcement"]["kind"] == "semantic-review":
            assert r["enforcement"]["status"] == "review-fallback", r["id"]


def test_callable_status_requires_named_callable():
    """No record may claim status 'callable' unless it is a mechanized kind whose
    validator names a shipped callable."""
    for r in RECORDS:
        enf = r["enforcement"]
        if enf["status"] == "callable":
            assert enf["kind"] in MECHANIZED_KINDS, r["id"]
            assert enf["validator"] in NAMED_CALLABLES, (
                "%s claims callable but validator %r has no shipped code"
                % (r["id"], enf["validator"]))


def test_mechanized_without_named_callable_is_not_callable():
    """A deterministic/parser/heuristic record whose validator has no shipped
    callable must be 'planned', never 'callable'."""
    for r in RECORDS:
        enf = r["enforcement"]
        if enf["kind"] in MECHANIZED_KINDS and enf["validator"] not in NAMED_CALLABLES:
            assert enf["status"] == "planned", r["id"]


def test_implemented_validators_are_not_under_claimed():
    """The gate runs both ways: if the shipped linter implements a validator,
    the record naming it must say so. Prevents silently under-reporting real
    capability the way v0.1 over-reported phantom capability."""
    implemented = set(lint_prose.IMPLEMENTED_VALIDATORS)
    for r in RECORDS:
        enf = r["enforcement"]
        if enf.get("validator") in implemented:
            assert enf["status"] == "callable", (
                "%s names validator %r which the shipped linter implements, "
                "but status is %r" % (r["id"], enf["validator"], enf["status"]))


def test_every_implemented_validator_is_claimed_by_a_record():
    """No orphan checks: every implemented validator maps to a registry record."""
    named = {r["enforcement"].get("validator") for r in RECORDS}
    orphans = sorted(set(lint_prose.IMPLEMENTED_VALIDATORS) - named)
    assert not orphans, "linter implements validators no record names: %s" % orphans


def test_exactly_the_named_callable_is_callable():
    callable_ids = {r["id"] for r in RECORDS
                    if r["enforcement"]["status"] == "callable"}
    # Every callable record's validator is a shipped callable, and each shipped
    # callable is claimed by at most the records that name it.
    for r in RECORDS:
        if r["id"] in callable_ids:
            assert r["enforcement"]["validator"] in NAMED_CALLABLES, r["id"]
    assert callable_ids, "at least one validator ships callable code today"


# --------------------------------------------------------------------------- #
# R5-field -- activation.always_on_for_prose selector
# --------------------------------------------------------------------------- #

def test_every_record_has_always_on_flag_boolean():
    for r in RECORDS:
        val = r["activation"]["always_on_for_prose"]
        assert isinstance(val, bool), "%s -> %r" % (r["id"], val)


def test_always_on_flag_matches_selector():
    for r in RECORDS:
        assert r["activation"]["always_on_for_prose"] is _selector_always_on(r), \
            r["id"]


def test_always_on_count_matches_selector():
    flagged = {r["id"] for r in RECORDS if r["activation"]["always_on_for_prose"]}
    selected = {r["id"] for r in RECORDS if _selector_always_on(r)}
    assert flagged == selected
    # 11 always-user-facing (ACT) + 21 unconditional-prose (PRO) = 32.
    assert len(flagged) == 32
    # every always-user-facing record is always-on-for-prose
    for r in RECORDS:
        if r["activation"]["kind"] == "always-user-facing":
            assert r["id"] in flagged, r["id"]
    # sub-region-gated PRO records are excluded
    for rid in ("STOW-PRO-003", "STOW-PRO-016", "STOW-PRO-023"):
        assert rid not in flagged, rid


# --------------------------------------------------------------------------- #
# Invariants -- primary_total + per-domain counts unchanged; contracts outside
# --------------------------------------------------------------------------- #

def test_primary_total_and_domain_counts():
    assert len(RECORDS) == 104
    assert REGISTRY["generated_counts"]["primary_total"] == 104
    got = Counter(_domain(r["id"]) for r in RECORDS)
    assert dict(got) == EXPECTED_DOMAIN_COUNTS
    assert sum(EXPECTED_DOMAIN_COUNTS.values()) == 104


def test_contracts_catalog_kept_outside_primary_total():
    contracts = REGISTRY["contracts"]
    assert contracts["meta_contract_total"] == 5
    ids = [c["id"] for c in contracts["catalog"]]
    assert ids == ["output-contract", "handoff", "task-packet",
                   "evidence-record", "state"]
    assert len(ids) == 5
    # meta-contracts are counted separately from the 104 primary records
    assert REGISTRY["generated_counts"]["primary_total"] == 104
    assert "contracts" not in REGISTRY["generated_counts"]
