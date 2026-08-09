"""Contract tests for the bounded paired behavioural challenge definitions."""

import copy
import re
from pathlib import Path

from ruamel.yaml import YAML

from test_rule_dispositions import STARTING_IDS


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests" / "evals" / "rule-disposition-challenges-v1.yaml"


def _load():
    parser = YAML(typ="safe")
    with PATH.open(encoding="utf-8") as stream:
        return parser.load(stream)


def challenge_errors(data):
    errors = []
    pack = next(pack for pack in data["scenario_packs"] if pack["id"] == "BC-05")
    authority = pack.get("closed_authority", {})
    required_verbs = {"confirm", "inspect", "isolate", "record"}
    if not required_verbs <= set(authority.get("approved_action_verbs", [])):
        errors.append("negative-control action verb is outside the closed authority")
    controlled_text = pack["paired_negative_control"]
    if "Steps:" not in controlled_text or "Do these steps:" in controlled_text:
        errors.append("negative control uses an action-like list lead")
    if "(the pressure is low)" not in controlled_text or "(after isolation)" in controlled_text:
        errors.append("negative control uses a nominalized parenthetical")
    if {"do", "isolation"} & set(authority.get("approved_vocabulary", [])):
        errors.append("obsolete action or nominalization remains in the authority")
    for literal in authority.get("protected_literals", []):
        controlled_text = controlled_text.replace(literal, " ")
    for term in (authority.get("technical_terms", {}).get("site_name", ""),):
        controlled_text = controlled_text.replace(term, " ")
    tokens = {token.lower() for token in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)?", controlled_text)}
    if not tokens <= set(authority.get("approved_vocabulary", [])):
        errors.append("negative-control vocabulary is outside the closed authority")
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
        "condition": 10,
        "list-lead": 1,
        "identifier": 3,
        "quotation": 6,
        "atomic-classes": 6,
        "parenthetical-hyphenated": 9,
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


def test_eight_paired_natural_tasks_cover_starting_inventory():
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
    assert sorted(covered) == sorted(STARTING_IDS)


def test_controlled_pack_does_not_overclaim_rule_level_observability():
    pack = next(pack for pack in _load()["scenario_packs"] if pack["id"] == "BC-05")
    assert pack["closed_authority"]["technical_terms"]
    assert pack["expected_not_observable"]
    assert "NOT_OBSERVABLE" in pack["coverage_limit"]


def test_controlled_negative_control_closes_authority_and_counting_contract():
    data = _load()
    assert challenge_errors(data) == []

    missing_verb = copy.deepcopy(data)
    pack = next(pack for pack in missing_verb["scenario_packs"] if pack["id"] == "BC-05")
    pack["closed_authority"]["approved_action_verbs"].remove("confirm")
    assert challenge_errors(missing_verb)

    bad_count = copy.deepcopy(data)
    pack = next(pack for pack in bad_count["scenario_packs"] if pack["id"] == "BC-05")
    pack["word_count_contract"]["expected_calculations"][0]["count"] = 11
    assert challenge_errors(bad_count)

    ambiguous_observability = copy.deepcopy(data)
    pack = next(pack for pack in ambiguous_observability["scenario_packs"] if pack["id"] == "BC-05")
    pack["counting_observability"]["negative_control_arm"]["deterministic_construction"].pop()
    assert challenge_errors(ambiguous_observability)


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
