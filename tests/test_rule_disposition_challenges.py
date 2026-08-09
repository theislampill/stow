"""Contract tests for the bounded paired behavioural challenge definitions."""

from pathlib import Path

from ruamel.yaml import YAML

from test_rule_dispositions import STARTING_IDS


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests" / "evals" / "rule-disposition-challenges-v1.yaml"


def _load():
    parser = YAML(typ="safe")
    with PATH.open(encoding="utf-8") as stream:
        return parser.load(stream)


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
    assert "closed authority packet" in pack["pathology_input"].lower()
    assert pack["expected_not_observable"]
    assert "NOT_OBSERVABLE" in pack["coverage_limit"]


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
