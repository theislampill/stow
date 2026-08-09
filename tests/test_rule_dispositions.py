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

    routing = _yaml(root / "skills" / "stow" / "rules" / "routing.yaml")
    route_modes = {route["mode"] for route in routing["routes"]}

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
        elif target is not None:
            errors.append(f"{row['id']} carries an inapplicable target")

        if row["layer"] == "G1":
            coverage = row["behavioural_coverage"]
            if not coverage["positive"] or not coverage["paired_negative"]:
                errors.append(f"{row['id']} lacks paired G1 coverage")
        elif not row["deterministic_verification"]:
            errors.append(f"{row['id']} lacks deterministic verification")
        elif not all(
            evidence["kind"] == "deterministic-test"
            for evidence in row["deterministic_verification"]
        ):
            errors.append(f"{row['id']} has non-deterministic proof for {row['layer']}")

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


def test_baseline_captured_proposals_match_the_audited_map(ledger):
    assert ledger["ledger_status"] == "baseline-captured-proposals"
    actual = {
        disposition: {row["id"] for row in ledger["records"] if row["disposition"] == disposition}
        for disposition in EXPECTED_DISPOSITIONS
    }
    assert actual == EXPECTED_DISPOSITIONS
    assert all(row["decision_state"] == "proposed" for row in ledger["records"])


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
            destination.write_text("test fixture\n", encoding="utf-8")

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
