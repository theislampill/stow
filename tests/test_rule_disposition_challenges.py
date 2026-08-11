"""Contract tests for the bounded paired behavioural challenge definitions."""

import copy
import re
from pathlib import Path

from ruamel.yaml import YAML

from test_rule_dispositions import LEDGER_PATH


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests" / "evals" / "rule-disposition-challenges-v1.yaml"


def _load():
    parser = YAML(typ="safe")
    with PATH.open(encoding="utf-8") as stream:
        return parser.load(stream)


def _surviving_g1_ids():
    parser = YAML(typ="safe")
    with LEDGER_PATH.open(encoding="utf-8") as stream:
        ledger = parser.load(stream)
    return {
        row["id"] for row in ledger["records"]
        if row["layer"] == "G1"
        and row["disposition"] in {"KEEP", "SIMPLIFY", "MOVE"}
    }


def challenge_errors(data):
    errors = []
    pack = next(pack for pack in data["scenario_packs"] if pack["id"] == "BC-05")
    authority = pack.get("closed_authority", {})
    controlled_text = pack["paired_negative_control"]
    if "Steps:" not in controlled_text or "Do these steps:" in controlled_text:
        errors.append("negative control uses an action-like list lead")
    if "(the pressure is high)" not in controlled_text or "(the pressure is low)" in controlled_text:
        errors.append("negative control contradicts its high-pressure state")
    expected_literals = {
        "pathology": {"20 kPa": 1, "`PV-17`": 1, '"OPEN SLOWLY"': 1, "North Plant": 1},
        "negative_control": {"20 kPa": 1, "`PV-17`": 2, '"OPEN SLOWLY"': 2, "North Plant": 1},
    }
    if authority.get("exact_literal_counts") != expected_literals:
        errors.append("closed authority does not derive per-source exact literal counts")
    language = pack.get("controlled_language_authority", {})
    if language.get("mode") != "sparse-fixture-authority":
        errors.append("controlled-language authority is not sparse and fixture-bounded")
    records = {row.get("word"): row for row in language.get("dictionary_records", [])}
    if set(records) != {"CHECK", "INSPECT", "ISOLATE", "RECORD"}:
        errors.append("bounded dictionary records are incomplete")
    elif records["CHECK"].get("part_of_speech") != "noun" or records["INSPECT"].get("part_of_speech") != "verb":
        errors.append("bounded dictionary part-of-speech authority drifted")
    elif records["INSPECT"].get("forms") != ["inspect", "inspects", "inspected", "inspected"]:
        errors.append("bounded dictionary form authority drifted")
    terminology = language.get("terminology_records", {})
    if terminology.get("official_long_noun") != "emergency purge valve control assembly":
        errors.append("official long technical noun is absent")
    if terminology.get("declared_short_noun") != "purge control assembly":
        errors.append("declared short technical noun is absent")
    hyphenation = language.get("hyphenation", {})
    if hyphenation.get("preserve") != ["high-pressure"]:
        errors.append("legitimate hyphen negative control is absent")
    if hyphenation.get("repair") != ["emergency-purge-valve-control-assembly"]:
        errors.append("over-hyphenated pathology target is absent")
    contract = pack.get("word_count_contract", {})
    if contract.get("procedural_sentence_max") != 20:
        errors.append("procedural cap is not fixed")
    if contract.get("list_colon_ends_sentence") is not True:
        errors.append("list colon boundary is not fixed")
    if contract.get("parenthetical_host_words") != 1:
        errors.append("parenthetical host count is not fixed")
    if contract.get("hyphenated_group_words") != 1:
        errors.append("hyphenated-group count is not fixed")
    expected_classes = {"number", "identifier", "quoted-text", "title", "proper-noun"}
    if set(contract.get("atomic_classes", [])) != expected_classes:
        errors.append("atomic counting classes are incomplete")
    calculations = contract.get("expected_calculations", [])
    expected_counts = {
        "condition": 13,
        "list-lead": 1,
        "identifier": 8,
        "quotation": 6,
        "atomic-classes": 6,
        "parenthetical-hyphenated": 12,
    }
    actual_counts = {item.get("id"): item.get("count") for item in calculations}
    if actual_counts != expected_counts or any(item.get("count", 99) > 20 for item in calculations):
        errors.append("expected calculations are absent or exceed the cap")
    control = pack["paired_negative_control"]
    if any(item.get("text", "") not in control for item in calculations):
        errors.append("expected calculation is not present in the negative control")
    counting_ids = {f"STOW-PCT-{number:03d}" for number in range(4, 8)}
    observability = pack.get("counting_observability", {})
    if set(pack["expected_not_observable"]) & counting_ids:
        errors.append("counting observability is ambiguously pack-wide")
    if set(observability.get("pathology_arm", {}).get("expected_not_observable", [])) != counting_ids:
        errors.append("pathology arm counting boundary is incomplete")
    negative = observability.get("negative_control_arm", {})
    if set(negative.get("deterministic_construction", [])) != counting_ids:
        errors.append("negative-control construction boundary is incomplete")
    if set(negative.get("false_positive_preservation", [])) != counting_ids:
        errors.append("negative-control preservation boundary is incomplete")
    if observability.get("model_output_semantic_count") != "NOT_OBSERVABLE_UNLESS_COUNT_REQUESTED_OR_RETURNED":
        errors.append("model-output counting limitation is not explicit")
    return errors


def test_challenge_file_exists():
    assert PATH.is_file()


def test_eight_paired_natural_tasks_cover_surviving_g1_surface():
    data = _load()
    packs = data["scenario_packs"]
    assert [pack["id"] for pack in packs] == [f"BC-{n:02d}" for n in range(1, 9)]
    covered = []
    for pack in packs:
        assert pack["task_prompt"].strip()
        assert pack["pathology_input"].strip()
        assert pack["paired_negative_control"].strip()
        assert pack["positive_coverage"]
        assert pack["paired_negative_coverage"] == pack["positive_coverage"]
        assert pack["coverage_limit"].strip()
        assert set(pack["expected_not_observable"]) <= set(pack["positive_coverage"])
        covered.extend(pack["positive_coverage"])
    assert len(covered) == len(set(covered))
    assert set(covered) == _surviving_g1_ids()


def test_controlled_pack_does_not_overclaim_rule_level_observability():
    pack = next(pack for pack in _load()["scenario_packs"] if pack["id"] == "BC-05")
    assert pack["closed_authority"]["exact_literal_counts"]
    assert pack["expected_not_observable"]
    assert "NOT_OBSERVABLE" in pack["coverage_limit"]


def test_controlled_negative_control_closes_authority_and_counting_contract():
    data = _load()
    assert challenge_errors(data) == []

    bad_literal_count = copy.deepcopy(data)
    pack = next(pack for pack in bad_literal_count["scenario_packs"] if pack["id"] == "BC-05")
    pack["closed_authority"]["exact_literal_counts"]["pathology"]["20 kPa"] = 2
    assert challenge_errors(bad_literal_count)

    bad_count = copy.deepcopy(data)
    pack = next(pack for pack in bad_count["scenario_packs"] if pack["id"] == "BC-05")
    pack["word_count_contract"]["expected_calculations"][0]["count"] = 11
    assert challenge_errors(bad_count)

    ambiguous_observability = copy.deepcopy(data)
    pack = next(pack for pack in ambiguous_observability["scenario_packs"] if pack["id"] == "BC-05")
    pack["counting_observability"]["negative_control_arm"]["deterministic_construction"].pop()
    assert challenge_errors(ambiguous_observability)

    missing_sparse_authority = copy.deepcopy(data)
    pack = next(pack for pack in missing_sparse_authority["scenario_packs"] if pack["id"] == "BC-05")
    pack["controlled_language_authority"].pop("dictionary_records")
    assert challenge_errors(missing_sparse_authority)


def test_prompts_do_not_reveal_the_evaluation_frame():
    forbidden = ("stow", "rule id", "taxonomy", "language model", "llm", "ai-generated", "ai writing")
    for pack in _load()["scenario_packs"]:
        prompt = pack["task_prompt"].lower()
        assert all(term not in prompt for term in forbidden)


def test_scoring_covers_benefit_and_false_positive_damage():
    scoring = _load()["scoring"]
    assert set(scoring["dimensions"]) == {
        "fidelity",
        "voice_preservation",
        "naturalness",
        "editorial_restraint",
        "residual_pathology",
        "false_positive_damage",
    }
    assert set(scoring["critical_failures"]) == {
        "invented_fact",
        "dropped_qualification",
        "altered_literal",
        "unsafe_omission",
        "contract_failure",
    }
    thresholds = _load()["evaluation_thresholds"]
    assert thresholds["critical_treatment_failures"] == 0
    assert thresholds["minimum_packs_with_pathology_reduction"] == 6
    assert thresholds["maximum_control_false_positive_damage"] == 1


def test_v7_regressions_are_preregistered_at_the_right_evidence_layer():
    targets = {target["id"]: target for target in _load()["regression_targets"]}
    assert set(targets) == {
        "unknown-boundary", "unsupported-state", "unit-literal", "redundant-label",
        "coordination-preservation", "house-transition",
    }
    assert targets["unit-literal"]["mechanism"] == "exact-literal"
    assert targets["house-transition"]["mechanism"] == "fixture-specific-exact-literal"
    for target_id in ("unknown-boundary", "unsupported-state", "redundant-label", "coordination-preservation"):
        assert targets[target_id]["mechanism"] == "contextual-review"
    assert targets["house-transition"]["universal_rule"] is False
