"""Structural contract for the audited starting-rule disposition ledger."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs" / "rule-dispositions.yaml"
SCHEMA_PATH = ROOT / "docs" / "rule-dispositions.schema.json"
REGISTRY_PATH = ROOT / "skills" / "stow" / "rules" / "registry.yaml"
ROUTING_PATH = ROOT / "skills" / "stow" / "rules" / "routing.yaml"

STARTING_IDS = tuple(
    [f"STOW-WRD-{n:03d}" for n in range(1, 15)]
    + [f"STOW-MWN-{n:03d}" for n in range(1, 3)]
    + [f"STOW-VRB-{n:03d}" for n in range(1, 8)]
    + [f"STOW-SEN-{n:03d}" for n in range(1, 6)]
    + [f"STOW-PRC-{n:03d}" for n in range(1, 6)]
    + [f"STOW-DSC-{n:03d}" for n in range(1, 7)]
    + [f"STOW-SAF-{n:03d}" for n in range(1, 4)]
    + [f"STOW-PCT-{n:03d}" for n in range(1, 8)]
    + [f"STOW-STY-{n:03d}" for n in range(1, 5)]
    + [f"STOW-GEN-{n:03d}" for n in range(1, 9)]
    + [f"STOW-ACT-{n:03d}" for n in range(1, 12)]
    + [f"STOW-PRO-{n:03d}" for n in range(1, 25)]
)


def _ids(prefix, values):
    return {f"STOW-{prefix}-{value:03d}" for value in values}


EXPECTED_KEEP = (
    _ids("WRD", [11]) | _ids("MWN", [1]) | _ids("VRB", [6, 7])
    | _ids("SEN", [3, 5]) | _ids("PRC", range(1, 5))
    | _ids("DSC", [1, 3, 4, 6]) | _ids("SAF", range(1, 4))
    | _ids("PCT", [1]) | _ids("STY", [1]) | _ids("GEN", [6])
    | _ids("ACT", [2, 7, 8, 11]) | _ids("PRO", [6, 16])
)
EXPECTED_SIMPLIFY = (
    _ids("WRD", [10]) | _ids("SEN", [2]) | _ids("PRC", [5])
    | _ids("GEN", [2, 3, 7]) | _ids("ACT", [1])
    | _ids("PRO", [5, 7, 9, 11, 20])
)
EXPECTED_MERGE = (
    _ids("WRD", [4, 5, 6, 9, 12, 13]) | _ids("MWN", [2])
    | _ids("VRB", [1, 3, 4]) | _ids("SEN", [1])
    | _ids("DSC", [2, 5]) | _ids("STY", [2, 4]) | _ids("GEN", [4])
    | _ids("ACT", [3, 10]) | _ids("PRO", [4, 8, 12, 14, 21, 22, 24])
)
EXPECTED_MOVE = (
    _ids("WRD", [1, 2, 3, 7, 8, 14]) | _ids("VRB", [2, 5])
    | _ids("SEN", [4]) | _ids("PCT", range(3, 8)) | _ids("STY", [3])
    | _ids("GEN", [5]) | _ids("ACT", [4, 5, 6])
    | _ids("PRO", [1, 2, 13, 15, 17, 18, 19, 23])
)
EXPECTED_DROP = _ids("PCT", [2]) | _ids("GEN", [1, 8]) | _ids("ACT", [9]) | _ids("PRO", [3, 10])
EXPECTED_DISPOSITIONS = {
    "KEEP": EXPECTED_KEEP,
    "SIMPLIFY": EXPECTED_SIMPLIFY,
    "MERGE": EXPECTED_MERGE,
    "MOVE": EXPECTED_MOVE,
    "DROP": EXPECTED_DROP,
}

EXPECTED_MERGE_TARGETS = {
    "STOW-WRD-004": ["STOW-WRD-002"],
    "STOW-WRD-005": ["STOW-WRD-001"],
    "STOW-WRD-006": ["STOW-WRD-001"],
    "STOW-WRD-009": ["STOW-MWN-001"],
    "STOW-WRD-012": ["STOW-WRD-001"],
    "STOW-WRD-013": ["STOW-VRB-007"],
    "STOW-MWN-002": ["STOW-MWN-001"],
    "STOW-VRB-001": ["STOW-WRD-002"],
    "STOW-VRB-003": ["STOW-WRD-002"],
    "STOW-VRB-004": ["STOW-VRB-002"],
    "STOW-SEN-001": ["STOW-PRC-001", "STOW-DSC-001", "STOW-DSC-003"],
    "STOW-DSC-002": ["STOW-WRD-011"],
    "STOW-DSC-005": ["STOW-DSC-004"],
    "STOW-STY-002": ["STOW-WRD-002", "STOW-WRD-003"],
    "STOW-STY-004": ["STOW-WRD-011"],
    "STOW-GEN-004": ["STOW-GEN-003"],
    "STOW-ACT-003": ["STOW-ACT-001"],
    "STOW-ACT-010": ["STOW-ACT-001"],
    "STOW-PRO-004": ["STOW-PRO-009"],
    "STOW-PRO-008": ["STOW-PRO-011"],
    "STOW-PRO-012": ["STOW-PRO-011"],
    "STOW-PRO-014": ["STOW-PRO-009"],
    "STOW-PRO-021": ["STOW-PRO-020"],
    "STOW-PRO-022": ["STOW-PRO-020"],
    "STOW-PRO-024": ["STOW-PRO-011"],
}


def _moves(rule_ids, path, route):
    return {rule_id: (path, route) for rule_id in rule_ids}


EXPECTED_MOVE_TARGETS = {}
EXPECTED_MOVE_TARGETS.update(_moves(
    _ids("WRD", [1, 2, 3, 7]) | _ids("VRB", [2, 5]) | _ids("SEN", [4]) | _ids("STY", [3]) | _ids("GEN", [5]),
    "references/conformance.md", "conformance",
))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("WRD", [8]), "references/canonical-terms.md", "canonical-term-map"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("WRD", [14]) | _ids("PRO", [1]), "references/prose-integrity.md", "prose-integrity-deep"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("PCT", range(3, 8)), "references/controlled-technical-writing.md", "controlled-technical"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("ACT", [4, 6]), "references/action-shaping.md", "action-shaping-deep"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("ACT", [5]), "references/continuity-and-state.md", "meta-code"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("PRO", [2, 15, 17, 18, 19, 23]), "references/audit-and-evidence.md", "meta-code"))
EXPECTED_MOVE_TARGETS.update(_moves(_ids("PRO", [13]), "references/meta-code.md", "meta-code"))

EXPECTED_G2_PROOFS = {
    "STOW-PRC-001": ("procedural-sentence-max-20-words", "tests/test_lint_prose.py::test_procedural_sentence_cap_is_20_words_and_applies_to_list_items"),
    "STOW-DSC-003": ("descriptive-sentence-max-25-words", "tests/test_lint_prose.py::test_descriptive_sentence_cap_is_25_words"),
    "STOW-PCT-001": ("no-semicolon", "tests/test_lint_prose.py::test_semicolon_is_reported_only_under_the_controlled_technical_profile"),
    "STOW-GEN-006": ("no-latin-abbreviations", "tests/test_lint_prose.py::test_punctuation_check_is_red_on_its_fixture"),
}

EXPECTED_G1_SIGNAL_PROOFS = {
    "STOW-ACT-009": ("list-max-5-items", "tests/test_profiles.py::test_target_behavior_matrix"),
    "STOW-PRO-001": ("no-em-dash", "tests/test_lint_prose.py::test_em_dash_fires_under_every_profile"),
    "STOW-PRO-004": ("no-intensifiers", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-010": ("no-scare-quotes", "tests/test_lint_prose.py::test_punctuation_check_is_red_on_its_fixture"),
    "STOW-PRO-011": ("no-filler-phrases", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-012": ("no-whether-youre-opener", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-015": ("no-weasel-words", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-020": ("no-ai-transitions", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-021": ("no-ai-verbs", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
    "STOW-PRO-022": ("no-academic-tells", "tests/test_lint_prose.py::test_lexical_check_is_red_on_its_fixture"),
}

DIAGNOSTIC_RUN_ID = "G1-BHV-20260809-V7D"
DIAGNOSTIC_LIMITS = (
    "Non-qualifying diagnostic only: all source calls failed deterministic validation; "
    "cluster association is not accepted paired evidence or causal rule proof."
)
DIAGNOSTIC_UNCERTAINTY = (
    "Fresh paired outputs were generated, but every call failed deterministic validation. "
    "The adjudication is diagnostic-only and does not satisfy the required accepted "
    "behavioral challenge."
)
SURVIVING_G1_DISPOSITIONS = {"KEEP", "SIMPLIFY", "MOVE"}


def _accepted_behavioural_receipt(candidate, row):
    return {
        "kind": "behavioural-challenge",
        "reference": "receipt:bounded-paired-run",
        "result": "accepted",
        "freshness": "fresh",
        "limits": "Bounded paired evidence only; external receipt verification remains required.",
        "subject_revision": candidate["subject_revision"],
        "positive_cases": list(row["behavioural_coverage"]["positive"]),
        "paired_negative_cases": list(row["behavioural_coverage"]["paired_negative"]),
        "receipt_sha256": "a" * 64,
        "candidate_sha256": "b" * 64,
        "protocol_revision": "g1-behavioural-v1",
        "qualification": "qualifying-pass",
        "rule_observation": "PASS",
    }


def _yaml(path: Path):
    parser = YAML(typ="safe")
    with path.open(encoding="utf-8") as stream:
        return parser.load(stream)


@pytest.fixture(scope="module")
def schema():
    import json

    with SCHEMA_PATH.open(encoding="utf-8") as stream:
        value = json.load(stream)
    Draft202012Validator.check_schema(value)
    return value


@pytest.fixture(scope="module")
def ledger():
    return _yaml(LEDGER_PATH)


def _copy_semantic_root(tmp_path):
    root = tmp_path
    rules = root / "skills" / "stow" / "rules"
    references = root / "skills" / "stow" / "references"
    rules.mkdir(parents=True)
    references.mkdir(parents=True)
    for name in ("registry.yaml", "routing.yaml"):
        (rules / name).write_text(
            (ROOT / "skills" / "stow" / "rules" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    for path in (ROOT / "skills" / "stow" / "references").iterdir():
        if path.is_file():
            (references / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return root


def _write_registry(root, registry):
    emitter = YAML()
    registry["generated_counts"]["primary_total"] = len(registry["records"])
    with (root / "skills" / "stow" / "rules" / "registry.yaml").open(
        "w", encoding="utf-8"
    ) as stream:
        emitter.dump(registry, stream)


def _accept_g2(candidate, rule_id):
    row = next(record for record in candidate["records"] if record["id"] == rule_id)
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    proof = row["deterministic_verification"][0]
    proof["result"] = "accepted"
    proof["freshness"] = "fresh"
    proof["subject_revision"] = candidate["subject_revision"]
    proof["proof_scope"] = "compliance"
    return row


def semantic_errors(candidate, root: Path = ROOT):
    errors = []
    records = candidate["records"]
    by_id = {row["id"]: row for row in records}
    ids = [row["id"] for row in records]

    if tuple(candidate["starting_population"]["ids"]) != STARTING_IDS:
        errors.append("starting ID inventory changed")
    if ids != list(STARTING_IDS) or len(ids) != len(set(ids)):
        errors.append("record IDs do not exactly match the frozen starting inventory")
    if candidate["starting_population"]["size"] != len(STARTING_IDS):
        errors.append("starting population size disagrees with frozen inventory")

    registry = _yaml(root / "skills" / "stow" / "rules" / "registry.yaml")
    if registry["generated_counts"]["primary_total"] != len(registry["records"]):
        errors.append("active registry count disagrees with primary_total")
    active_registry_ids = {record["id"] for record in registry["records"]}

    routing = _yaml(root / "skills" / "stow" / "rules" / "routing.yaml")
    routes = {route["mode"]: route for route in routing["routes"]}
    route_modes = set(routes)

    merge_graph = {}
    for row in records:
        disposition = row["disposition"]
        target = row.get("target")
        if disposition == "MERGE":
            targets = target["rule_ids"] if target and target.get("kind") == "rule-set" else []
            merge_graph[row["id"]] = targets
            if not targets:
                errors.append(f"{row['id']} lacks merge targets")
            for target_id in targets:
                if target_id not in by_id:
                    errors.append(f"{row['id']} has unknown merge target {target_id}")
                elif target_id == row["id"]:
                    errors.append(f"{row['id']} self-merges")
            if row["id"] in EXPECTED_MERGE_TARGETS and targets != EXPECTED_MERGE_TARGETS[row["id"]]:
                errors.append(f"{row['id']} changed its audited merge target")
        elif disposition == "MOVE":
            destinations = (
                target["destinations"]
                if target and target.get("kind") == "reference-surface"
                else []
            )
            if not destinations:
                errors.append(f"{row['id']} lacks move destinations")
            for destination in destinations:
                if not (root / "skills" / "stow" / destination["path"]).is_file():
                    errors.append(f"{row['id']} move destination does not exist")
                if destination["activation_route"] not in route_modes:
                    errors.append(f"{row['id']} move route is not named")
                    continue
                expected = EXPECTED_MOVE_TARGETS.get(row["id"])
                actual = (destination["path"], destination["activation_route"])
                if expected is not None and actual != expected:
                    errors.append(f"{row['id']} changed its audited move target")
                route = routes[destination["activation_route"]]
                direct = destination["path"] in route["references"]
                indirect = False
                for routed_reference in route["references"]:
                    reference_path = root / "skills" / "stow" / routed_reference
                    if reference_path.is_file() and destination["path"] in reference_path.read_text(encoding="utf-8"):
                        indirect = True
                if not direct and not indirect:
                    errors.append(f"{row['id']} route does not load its move destination")
        elif target is not None:
            errors.append(f"{row['id']} carries an inapplicable target")

        if row["decision_state"] == "proposed" and row["closure_state"] == "closed":
            errors.append(f"{row['id']} proposal cannot be closed")

        terminal = row["decision_state"] == "accepted" or row["closure_state"] == "closed"
        if terminal and disposition in {"MERGE", "DROP"} and row["id"] in active_registry_ids:
            errors.append(f"{row['id']} terminal retired source remains in active registry")
        if terminal and disposition in SURVIVING_G1_DISPOSITIONS and row["id"] not in active_registry_ids:
            errors.append(f"{row['id']} terminal survivor is absent from active registry")

        behavioural_evidence = [
            evidence for evidence in row["evidence"]
            if evidence["kind"] == "behavioural-challenge"
            and evidence["freshness"] == "fresh"
            and evidence["result"] == "accepted"
            and evidence.get("subject_revision") == candidate["subject_revision"]
            and evidence.get("qualification") == "qualifying-pass"
            and evidence.get("rule_observation") == "PASS"
            and evidence.get("protocol_revision")
            and evidence.get("receipt_sha256")
            and evidence.get("candidate_sha256")
        ]

        if row["layer"] == "G1":
            coverage = row["behavioural_coverage"]
            if not coverage["positive"] or not coverage["paired_negative"]:
                errors.append(f"{row['id']} lacks paired G1 coverage")
            paired_behavioural_evidence = [
                evidence for evidence in behavioural_evidence
                if evidence.get("positive_cases", []) == coverage["positive"]
                and evidence.get("paired_negative_cases", []) == coverage["paired_negative"]
            ]
            requires_behavioural_evidence = disposition in SURVIVING_G1_DISPOSITIONS
            if (
                requires_behavioural_evidence
                and coverage["status"] == "complete"
                and not paired_behavioural_evidence
            ):
                errors.append(f"{row['id']} complete G1 coverage lacks fresh matching evidence")
            if (
                requires_behavioural_evidence
                and (row["decision_state"] == "accepted" or row["closure_state"] == "closed")
            ):
                if coverage["status"] != "complete" or not paired_behavioural_evidence:
                    errors.append(f"{row['id']} accepted or terminal G1 claim lacks completed fresh evidence")
            if row["id"] in EXPECTED_G1_SIGNAL_PROOFS:
                expected_validator, expected_reference = EXPECTED_G1_SIGNAL_PROOFS[row["id"]]
                signal_proofs = [
                    (
                        evidence.get("proves_validator"),
                        evidence["reference"],
                        evidence.get("proof_scope"),
                    )
                    for evidence in row["deterministic_verification"]
                ]
                if signal_proofs != [
                    (expected_validator, expected_reference, "advisory-signal-only")
                ]:
                    errors.append(f"{row['id']} advisory signal is misclassified as compliance proof")
        elif not row["deterministic_verification"]:
            errors.append(f"{row['id']} lacks deterministic verification")
        elif not all(
            evidence["kind"] == "deterministic-test"
            for evidence in row["deterministic_verification"]
        ):
            errors.append(f"{row['id']} has non-deterministic proof for {row['layer']}")
        elif row["id"] in EXPECTED_G2_PROOFS:
            expected_validator, expected_reference = EXPECTED_G2_PROOFS[row["id"]]
            actual_proofs = [
                (
                    evidence.get("proves_validator"),
                    evidence["reference"],
                    evidence.get("proof_scope"),
                )
                for evidence in row["deterministic_verification"]
            ]
            if row["starting_validator"] != expected_validator:
                errors.append(f"{row['id']} starting validator changed")
            if actual_proofs != [(expected_validator, expected_reference, "compliance")]:
                errors.append(f"{row['id']} deterministic proof is not bound to its validator")
            if terminal and not any(
                evidence["kind"] == "deterministic-test"
                and evidence["result"] == "accepted"
                and evidence["freshness"] == "fresh"
                and evidence.get("subject_revision") == candidate["subject_revision"]
                and evidence.get("proves_validator") == expected_validator
                and evidence.get("proof_scope") == "compliance"
                for evidence in row["deterministic_verification"]
            ):
                errors.append(f"{row['id']} terminal G2 state lacks fresh current named compliance proof")

        if row["layer"] in {"G3", "G4"}:
            errors.append(f"{row['id']} introduces an unsupported {row['layer']} claim")

    visiting = set()
    visited = set()

    def resolves(rule_id):
        if rule_id not in by_id:
            return False
        if rule_id in visiting:
            return False
        if rule_id in visited:
            return True
        row = by_id[rule_id]
        if row["disposition"] == "DROP":
            return False
        if row["disposition"] != "MERGE":
            visited.add(rule_id)
            return True
        visiting.add(rule_id)
        ok = all(resolves(target_id) for target_id in merge_graph.get(rule_id, []))
        visiting.remove(rule_id)
        if ok:
            visited.add(rule_id)
        return ok

    for rule_id in merge_graph:
        if not resolves(rule_id):
            errors.append(f"{rule_id} merge graph is cyclic or resolves to a dead end")

    def resolves_to_active_sink(rule_id, seen=None):
        seen = set() if seen is None else seen
        if rule_id in seen or rule_id not in by_id:
            return False
        row = by_id[rule_id]
        if row["disposition"] == "DROP":
            return False
        if row["disposition"] != "MERGE":
            return rule_id in active_registry_ids
        return all(
            resolves_to_active_sink(target_id, seen | {rule_id})
            for target_id in merge_graph.get(rule_id, [])
        )

    for rule_id in merge_graph:
        row = by_id[rule_id]
        terminal = row["decision_state"] == "accepted" or row["closure_state"] == "closed"
        if terminal and not resolves_to_active_sink(rule_id):
            errors.append(f"{rule_id} terminal merge does not resolve to an active registry sink")
    return errors


def test_ledger_and_schema_exist():
    assert LEDGER_PATH.is_file()
    assert SCHEMA_PATH.is_file()


def test_ledger_conforms_to_strict_schema(schema, ledger):
    errors = sorted(Draft202012Validator(schema).iter_errors(ledger), key=lambda error: list(error.path))
    assert errors == [], "\n".join(error.message for error in errors)


def test_schema_rejects_missing_fields_invalid_enums_and_wrong_targets(schema, ledger):
    validator = Draft202012Validator(schema)

    missing = copy.deepcopy(ledger)
    missing["records"][0].pop("independent_harm")
    assert list(validator.iter_errors(missing))

    invalid_enum = copy.deepcopy(ledger)
    invalid_enum["records"][0]["disposition"] = "RETAIN"
    assert list(validator.iter_errors(invalid_enum))

    wrong_target = copy.deepcopy(ledger)
    keep_row = next(row for row in wrong_target["records"] if row["disposition"] == "KEEP")
    keep_row["target"] = {"kind": "rule-set", "rule_ids": ["STOW-WRD-001"]}
    assert list(validator.iter_errors(wrong_target))


def test_ledger_semantics_close_cross_surface_gaps(ledger):
    assert semantic_errors(ledger) == []


@pytest.mark.parametrize("disposition", sorted(SURVIVING_G1_DISPOSITIONS))
def test_terminal_surviving_g1_state_requires_matching_fresh_evidence(
    schema, ledger, disposition
):
    validator = Draft202012Validator(schema)
    g1_index = next(
        i for i, row in enumerate(ledger["records"])
        if row["layer"] == "G1" and row["disposition"] == disposition
    )

    proposed_closed = copy.deepcopy(ledger)
    proposed_closed["records"][g1_index]["closure_state"] = "closed"
    assert list(validator.iter_errors(proposed_closed)) or semantic_errors(proposed_closed)

    accepted_closed = copy.deepcopy(ledger)
    accepted_closed["records"][g1_index]["decision_state"] = "accepted"
    accepted_closed["records"][g1_index]["closure_state"] = "closed"
    assert list(validator.iter_errors(accepted_closed)) or semantic_errors(accepted_closed)

    status_only = copy.deepcopy(ledger)
    status_only["records"][g1_index]["behavioural_coverage"]["status"] = "complete"
    assert list(validator.iter_errors(status_only)) or semantic_errors(status_only)

    wrong_revision = copy.deepcopy(ledger)
    row = wrong_revision["records"][g1_index]
    row["behavioural_coverage"]["status"] = "complete"
    row["evidence"].append(_accepted_behavioural_receipt(wrong_revision, row))
    row["evidence"][-1]["subject_revision"] = wrong_revision["subject_revision"] + 1
    assert list(validator.iter_errors(wrong_revision)) == []
    assert semantic_errors(wrong_revision)

    matching = copy.deepcopy(wrong_revision)
    row = matching["records"][g1_index]
    row["evidence"][-1]["subject_revision"] = matching["subject_revision"]
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    assert list(validator.iter_errors(matching)) == []
    assert semantic_errors(matching) == []


def test_arbitrary_or_mismatched_receipt_is_not_paired_evidence(schema, ledger):
    validator = Draft202012Validator(schema)
    arbitrary = copy.deepcopy(ledger)
    row = next(
        row for row in arbitrary["records"]
        if row["layer"] == "G1" and row["disposition"] == "KEEP"
    )
    row["behavioural_coverage"]["status"] = "complete"
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    row["evidence"].append({
        "kind": "behavioural-challenge",
        "reference": "receipt:unbound",
        "result": "accepted",
        "freshness": "fresh",
        "limits": "Unbound receipt.",
        "subject_revision": arbitrary["subject_revision"],
    })
    assert list(validator.iter_errors(arbitrary))
    assert semantic_errors(arbitrary)

    mismatched = copy.deepcopy(arbitrary)
    receipt = next(
        record for record in mismatched["records"] if record["id"] == row["id"]
    )["evidence"][-1]
    receipt.update(_accepted_behavioural_receipt(mismatched, row))
    receipt["positive_cases"] = ["BC-06"]
    receipt["paired_negative_cases"] = ["BC-06"]
    assert list(validator.iter_errors(mismatched)) == []
    assert semantic_errors(mismatched)


def test_accepted_behavioural_evidence_is_bound_to_opaque_receipt_and_candidate(
    schema, ledger
):
    validator = Draft202012Validator(schema)
    candidate = copy.deepcopy(ledger)
    row = next(
        row for row in candidate["records"]
        if row["layer"] == "G1" and row["disposition"] == "KEEP"
    )
    row["behavioural_coverage"]["status"] = "complete"
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    row["evidence"].append(_accepted_behavioural_receipt(candidate, row))

    assert list(validator.iter_errors(candidate)) == []
    assert semantic_errors(candidate) == []

    for field in (
        "receipt_sha256",
        "candidate_sha256",
        "protocol_revision",
        "qualification",
        "rule_observation",
    ):
        missing = copy.deepcopy(candidate)
        missing_row = next(record for record in missing["records"] if record["id"] == row["id"])
        missing_row["evidence"][-1].pop(field)
        assert list(validator.iter_errors(missing)), field
        assert semantic_errors(missing), field

    uppercase_digest = copy.deepcopy(candidate)
    uppercase_row = next(
        record for record in uppercase_digest["records"] if record["id"] == row["id"]
    )
    uppercase_row["evidence"][-1]["receipt_sha256"] = "A" * 64
    assert list(validator.iter_errors(uppercase_digest))

    accepted_schema = schema["$defs"]["accepted_behavioural_evidence"]
    assert "externally rehash" in accepted_schema["$comment"]
    assert "does not prove existence" in accepted_schema["$comment"]


@pytest.mark.parametrize("disposition", ["MERGE", "DROP"])
def test_terminal_retired_g1_source_does_not_require_fabricated_behavioural_evidence(
    schema, ledger, disposition, tmp_path
):
    validator = Draft202012Validator(schema)
    root = _copy_semantic_root(tmp_path)
    candidate = copy.deepcopy(ledger)
    row = next(
        row for row in candidate["records"]
        if row["layer"] == "G1" and row["disposition"] == disposition
    )
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"

    assert not any(evidence["result"] == "accepted" for evidence in row["evidence"])
    assert list(validator.iter_errors(candidate)) == []
    assert semantic_errors(candidate, root=root)

    registry = _yaml(root / "skills" / "stow" / "rules" / "registry.yaml")
    registry["records"] = [record for record in registry["records"] if record["id"] != row["id"]]
    _write_registry(root, registry)
    assert semantic_errors(candidate, root=root) == []


def test_terminal_survivor_must_remain_in_active_registry(tmp_path, ledger):
    root = _copy_semantic_root(tmp_path)
    candidate = copy.deepcopy(ledger)
    row = _accept_g2(candidate, "STOW-PRC-001")

    assert semantic_errors(candidate, root=root) == []

    registry = _yaml(root / "skills" / "stow" / "rules" / "registry.yaml")
    registry["records"] = [record for record in registry["records"] if record["id"] != row["id"]]
    _write_registry(root, registry)
    assert any("terminal survivor is absent" in error for error in semantic_errors(candidate, root=root))


def test_terminal_merge_must_resolve_to_active_registry_sink(tmp_path, ledger):
    root = _copy_semantic_root(tmp_path)
    candidate = copy.deepcopy(ledger)
    row = next(record for record in candidate["records"] if record["id"] == "STOW-PRO-004")
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    target_id = row["target"]["rule_ids"][0]

    registry = _yaml(root / "skills" / "stow" / "rules" / "registry.yaml")
    registry["records"] = [record for record in registry["records"] if record["id"] != row["id"]]
    _write_registry(root, registry)
    assert semantic_errors(candidate, root=root) == []

    registry["records"] = [record for record in registry["records"] if record["id"] != target_id]
    _write_registry(root, registry)
    assert any("does not resolve to an active registry sink" in error for error in semantic_errors(candidate, root=root))


def test_surviving_merge_target_still_requires_accepted_behavioural_evidence(schema, ledger):
    validator = Draft202012Validator(schema)
    candidate = copy.deepcopy(ledger)
    merge_row = next(
        row for row in candidate["records"]
        if row["layer"] == "G1" and row["disposition"] == "MERGE"
        and any(
            next(record for record in candidate["records"] if record["id"] == target_id)["disposition"]
            in SURVIVING_G1_DISPOSITIONS
            for target_id in row["target"]["rule_ids"]
        )
    )
    target = next(
        row for row in candidate["records"]
        if row["id"] in merge_row["target"]["rule_ids"]
        and row["disposition"] in SURVIVING_G1_DISPOSITIONS
    )
    target["decision_state"] = "accepted"
    target["closure_state"] = "closed"
    target["behavioural_coverage"]["status"] = "complete"

    assert list(validator.iter_errors(candidate))
    assert semantic_errors(candidate)


def test_every_g1_row_records_nonqualifying_current_revision_diagnostic(ledger):
    g1_rows = [row for row in ledger["records"] if row["layer"] == "G1"]
    g2_rows = [row for row in ledger["records"] if row["layer"] == "G2"]

    for row in g1_rows:
        diagnostic = [
            evidence for evidence in row["evidence"]
            if evidence["reference"].startswith(f"{DIAGNOSTIC_RUN_ID}/")
        ]
        assert len(diagnostic) == 1, row["id"]
        evidence = diagnostic[0]
        assert evidence == {
            "kind": "behavioural-challenge",
            "reference": evidence["reference"],
            "result": "inconclusive",
            "freshness": "fresh",
            "limits": DIAGNOSTIC_LIMITS,
            "subject_revision": ledger["subject_revision"],
        }
        assert evidence["reference"].endswith(f"#{row['id']}")
        assert row["uncertainty"] == DIAGNOSTIC_UNCERTAINTY
        assert row["behavioural_coverage"]["status"] == "pending"
        assert row["decision_state"] == "proposed"
        assert row["closure_state"] != "closed"

    assert all(
        not any(
            evidence["reference"].startswith(f"{DIAGNOSTIC_RUN_ID}/")
            for evidence in row["evidence"]
        )
        for row in g2_rows
    )


def test_contextual_guidance_is_not_misclassified_as_g2_compliance(ledger):
    rows = {row["id"]: row for row in ledger["records"]}

    assert {row["id"] for row in ledger["records"] if row["layer"] == "G2"} == set(
        EXPECTED_G2_PROOFS
    )
    for rule_id, (validator_name, reference) in EXPECTED_G1_SIGNAL_PROOFS.items():
        row = rows[rule_id]
        assert row["layer"] == "G1"
        assert row["mechanism"] == "guidance-with-heuristic-detector"
        assert [(proof["proves_validator"], proof["reference"]) for proof in row["deterministic_verification"]] == [
            (validator_name, reference)
        ]
        assert all(
            proof["proof_scope"] == "advisory-signal-only"
            for proof in row["deterministic_verification"]
        )
        assert "not compliance proof" in row["deterministic_verification"][0]["limits"]
        assert row["behavioural_coverage"]["status"] == "pending"
        assert row["decision_state"] == "proposed"
        assert row["closure_state"] != "closed"
        assert row["uncertainty"] == DIAGNOSTIC_UNCERTAINTY

    misclassified = copy.deepcopy(ledger)
    row = next(record for record in misclassified["records"] if record["id"] == "STOW-PRO-011")
    row["deterministic_verification"][0]["proof_scope"] = "compliance"
    assert semantic_errors(misclassified)


@pytest.mark.parametrize("rule_id", sorted(EXPECTED_G2_PROOFS))
def test_terminal_g2_requires_current_fresh_accepted_named_proof(schema, ledger, rule_id):
    validator = Draft202012Validator(schema)

    baseline_only = copy.deepcopy(ledger)
    row = next(record for record in baseline_only["records"] if record["id"] == rule_id)
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    assert semantic_errors(baseline_only)

    valid = copy.deepcopy(ledger)
    _accept_g2(valid, rule_id)
    assert list(validator.iter_errors(valid)) == []
    assert semantic_errors(valid) == []

    mutations = {
        "pending result": ("result", "pending"),
        "baseline freshness": ("freshness", "baseline-captured"),
        "pending freshness": ("freshness", "pending"),
        "stale revision": ("subject_revision", valid["subject_revision"] + 1),
        "wrong validator": ("proves_validator", "unrelated-validator"),
        "signal-only scope": ("proof_scope", "advisory-signal-only"),
    }
    for label, (field, value) in mutations.items():
        candidate = copy.deepcopy(valid)
        candidate_row = next(record for record in candidate["records"] if record["id"] == rule_id)
        candidate_row["deterministic_verification"][0][field] = value
        assert semantic_errors(candidate), label


def test_diagnostic_evidence_cannot_satisfy_surviving_g1_terminal_gate(schema, ledger):
    validator = Draft202012Validator(schema)
    candidate = copy.deepcopy(ledger)
    row = next(
        row for row in candidate["records"]
        if row["layer"] == "G1" and row["disposition"] == "KEEP"
    )
    row["decision_state"] = "accepted"
    row["closure_state"] = "closed"
    row["behavioural_coverage"]["status"] = "complete"

    assert any(
        evidence["result"] == "inconclusive"
        and evidence["reference"].startswith(f"{DIAGNOSTIC_RUN_ID}/")
        for evidence in row["evidence"]
    )
    assert list(validator.iter_errors(candidate))
    assert semantic_errors(candidate)


def test_baseline_captured_proposals_match_the_audited_map(ledger):
    assert ledger["ledger_status"] == "baseline-captured-proposals"
    actual = {
        disposition: {row["id"] for row in ledger["records"] if row["disposition"] == disposition}
        for disposition in EXPECTED_DISPOSITIONS
    }
    assert actual == EXPECTED_DISPOSITIONS
    assert all(row["decision_state"] == "proposed" for row in ledger["records"])


def test_each_proposal_has_independently_reviewable_analysis(ledger):
    records = ledger["records"]
    for field in (
        "observed_phenomenon",
        "independent_harm",
        "decision_rationale",
        "implementation_consequence",
    ):
        assert len({row[field] for row in records}) == len(records), field
    assert len({row["cost"]["rationale"] for row in records}) == len(records)
    assert all(row["id"] in row["decision_rationale"] for row in records)


def test_provisional_targets_match_the_audited_target_map(ledger):
    rows = {row["id"]: row for row in ledger["records"]}
    actual_merges = {
        rule_id: rows[rule_id]["target"]["rule_ids"] for rule_id in EXPECTED_MERGE_TARGETS
    }
    assert actual_merges == EXPECTED_MERGE_TARGETS
    actual_moves = {
        rule_id: (
            rows[rule_id]["target"]["destinations"][0]["path"],
            rows[rule_id]["target"]["destinations"][0]["activation_route"],
        )
        for rule_id in EXPECTED_MOVE_TARGETS
    }
    assert actual_moves == EXPECTED_MOVE_TARGETS

    unrelated_merge = copy.deepcopy(ledger)
    row = next(row for row in unrelated_merge["records"] if row["id"] == "STOW-WRD-004")
    row["target"]["rule_ids"] = ["STOW-WRD-011"]
    assert semantic_errors(unrelated_merge)

    unrelated_route = copy.deepcopy(ledger)
    row = next(row for row in unrelated_route["records"] if row["id"] == "STOW-WRD-001")
    row["target"]["destinations"][0]["activation_route"] = "meta-code"
    assert semantic_errors(unrelated_route)


def test_missing_duplicate_added_and_changed_ids_fail(ledger):
    variants = []
    missing = copy.deepcopy(ledger)
    missing["records"].pop()
    variants.append(missing)
    duplicate = copy.deepcopy(ledger)
    duplicate["records"][-1] = copy.deepcopy(duplicate["records"][0])
    variants.append(duplicate)
    added = copy.deepcopy(ledger)
    added["records"].append(copy.deepcopy(added["records"][-1]))
    added["records"][-1]["id"] = "STOW-PRO-999"
    variants.append(added)
    changed = copy.deepcopy(ledger)
    changed["starting_population"]["ids"][0] = "STOW-WRD-999"
    variants.append(changed)
    assert all(semantic_errors(candidate) for candidate in variants)


def test_merge_failures_are_detected(ledger):
    merge_index = next(i for i, row in enumerate(ledger["records"]) if row["disposition"] == "MERGE")
    for target_id in ("STOW-NOT-999", ledger["records"][merge_index]["id"]):
        candidate = copy.deepcopy(ledger)
        candidate["records"][merge_index]["target"]["rule_ids"] = [target_id]
        assert semantic_errors(candidate)

    cycle = copy.deepcopy(ledger)
    merge_row = cycle["records"][merge_index]
    target_id = merge_row["target"]["rule_ids"][0]
    target = next(row for row in cycle["records"] if row["id"] == target_id)
    target["disposition"] = "MERGE"
    target["target"] = {"kind": "rule-set", "rule_ids": [merge_row["id"]]}
    assert semantic_errors(cycle)

    dead_end = copy.deepcopy(ledger)
    merge_row = dead_end["records"][merge_index]
    target = next(row for row in dead_end["records"] if row["id"] == merge_row["target"]["rule_ids"][0])
    target["disposition"] = "DROP"
    target.pop("target", None)
    assert semantic_errors(dead_end)


def test_target_and_evidence_failures_are_detected(ledger):
    move_index = next(i for i, row in enumerate(ledger["records"]) if row["disposition"] == "MOVE")
    move = copy.deepcopy(ledger)
    move["records"][move_index]["target"]["destinations"][0]["path"] = "references/missing.md"
    assert semantic_errors(move)

    unnamed_route = copy.deepcopy(ledger)
    unnamed_route["records"][move_index]["target"]["destinations"][0]["activation_route"] = "missing-route"
    assert semantic_errors(unnamed_route)

    g1_index = next(i for i, row in enumerate(ledger["records"]) if row["layer"] == "G1")
    no_control = copy.deepcopy(ledger)
    no_control["records"][g1_index]["behavioural_coverage"]["paired_negative"] = []
    assert semantic_errors(no_control)

    g2_index = next(i for i, row in enumerate(ledger["records"]) if row["layer"] == "G2")
    no_proof = copy.deepcopy(ledger)
    no_proof["records"][g2_index]["deterministic_verification"] = []
    assert semantic_errors(no_proof)


def test_deterministic_evidence_references_real_test_nodes(ledger):
    for row in ledger["records"]:
        for evidence in row["deterministic_verification"]:
            path_text, separator, node_name = evidence["reference"].partition("::")
            assert separator == "::"
            path = ROOT / path_text
            assert path.is_file(), evidence["reference"]
            assert f"def {node_name}(" in path.read_text(encoding="utf-8"), evidence["reference"]


def test_g2_proof_is_bound_to_the_named_validator(ledger):
    rows = {row["id"]: row for row in ledger["records"]}
    assert set(EXPECTED_G2_PROOFS) == {row["id"] for row in ledger["records"] if row["layer"] == "G2"}
    for rule_id, (validator, reference) in EXPECTED_G2_PROOFS.items():
        proofs = rows[rule_id]["deterministic_verification"]
        assert [
            (proof["proves_validator"], proof["reference"], proof["proof_scope"])
            for proof in proofs
        ] == [(validator, reference, "compliance")]

    unrelated = copy.deepcopy(ledger)
    row = next(row for row in unrelated["records"] if row["id"] == "STOW-PRC-001")
    row["deterministic_verification"][0]["proves_validator"] = "no-semicolon"
    assert semantic_errors(unrelated)

    unrelated_node = copy.deepcopy(ledger)
    row = next(row for row in unrelated_node["records"] if row["id"] == "STOW-DSC-003")
    row["deterministic_verification"][0]["reference"] = "tests/test_lint_prose.py::test_punctuation_check_is_red_on_its_fixture"
    assert semantic_errors(unrelated_node)


def test_move_route_must_load_its_paired_destination(tmp_path, ledger):
    root = tmp_path
    rules = root / "skills" / "stow" / "rules"
    references = root / "skills" / "stow" / "references"
    rules.mkdir(parents=True)
    references.mkdir(parents=True)
    for name in ("registry.yaml", "routing.yaml"):
        (rules / name).write_text((ROOT / "skills" / "stow" / "rules" / name).read_text(encoding="utf-8"), encoding="utf-8")
    for path in (ROOT / "skills" / "stow" / "references").iterdir():
        if path.is_file():
            (references / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    routing = _yaml(rules / "routing.yaml")
    route = next(route for route in routing["routes"] if route["mode"] == "meta-code")
    route["references"] = ["references/procedures.md"]
    emitter = YAML()
    with (rules / "routing.yaml").open("w", encoding="utf-8") as stream:
        emitter.dump(routing, stream)
    assert any("route does not load" in error for error in semantic_errors(ledger, root=root))


def test_no_g3_or_g4_rule_claims(ledger):
    assert {row["layer"] for row in ledger["records"]} <= {"G1", "G2"}


def test_ledger_coverage_matches_paired_challenge_definitions(ledger):
    challenges = _yaml(ROOT / "tests" / "evals" / "rule-disposition-challenges-v1.yaml")
    packs = {pack["id"]: pack for pack in challenges["scenario_packs"]}
    for row in ledger["records"]:
        for scenario_id in row["behavioural_coverage"]["positive"]:
            assert row["id"] in packs[scenario_id]["positive_coverage"]
        for scenario_id in row["behavioural_coverage"]["paired_negative"]:
            assert row["id"] in packs[scenario_id]["paired_negative_coverage"]


def test_active_registry_count_is_dynamic_not_pinned(tmp_path, ledger):
    root = tmp_path
    (root / "skills" / "stow" / "rules").mkdir(parents=True)
    for name in ("registry.yaml", "routing.yaml"):
        (root / "skills" / "stow" / "rules" / name).write_text(
            (ROOT / "skills" / "stow" / "rules" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    for path in (ROOT / "skills" / "stow" / "references").iterdir():
        if path.is_file():
            destination = root / "skills" / "stow" / "references" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    registry = _yaml(root / "skills" / "stow" / "rules" / "registry.yaml")
    registry["records"].pop()
    emitter = YAML()

    mismatched = copy.deepcopy(registry)
    mismatched["generated_counts"]["primary_total"] += 1
    with (root / "skills" / "stow" / "rules" / "registry.yaml").open("w", encoding="utf-8") as stream:
        emitter.dump(mismatched, stream)
    assert semantic_errors(ledger, root=root)

    registry["generated_counts"]["primary_total"] = len(registry["records"])
    with (root / "skills" / "stow" / "rules" / "registry.yaml").open("w", encoding="utf-8") as stream:
        emitter.dump(registry, stream)
    assert semantic_errors(ledger, root=root) == []
