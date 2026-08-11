"""Contract tests for the bounded paired behavioural challenge definitions."""

import copy
import re
from pathlib import Path

from ruamel.yaml import YAML

from test_rule_dispositions import LEDGER_PATH


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests" / "evals" / "rule-disposition-challenges-v2.yaml"


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
    language_pack = next(pack for pack in data["scenario_packs"] if pack["id"] == "BC-09")
    count_pack = next(pack for pack in data["scenario_packs"] if pack["id"] == "BC-10")
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
    language = language_pack.get("controlled_language_authority", {})
    if language.get("mode") != "sparse-fixture-authority":
        errors.append("controlled-language authority is not sparse and fixture-bounded")
    records = {row.get("word"): row for row in language.get("dictionary_records", [])}
    if set(records) != {"APPLY", "CHECK", "INSPECT", "RECORD"}:
        errors.append("bounded dictionary records are incomplete")
    elif records["CHECK"].get("part_of_speech") != "noun" or records["INSPECT"].get("part_of_speech") != "verb":
        errors.append("bounded dictionary part-of-speech authority drifted")
    terminology = language.get("terminology_records", {})
    if terminology.get("official_long_noun") != "emergency purge valve control assembly":
        errors.append("official long technical noun is absent")
    if terminology.get("declared_short_noun") != "purge control assembly":
        errors.append("declared short technical noun is absent")
    contract = count_pack.get("word_count_contract", {})
    if contract.get("list_colon_ends_sentence") is not True:
        errors.append("list colon boundary is not fixed")
    if contract.get("parenthetical_host_words") != 1:
        errors.append("parenthetical host count is not fixed")
    if contract.get("hyphenated_group_words") != 1:
        errors.append("hyphenated-group count is not fixed")
    expected_classes = {"number", "identifier", "quoted-text", "proper-noun"}
    if set(contract.get("atomic_classes", [])) != expected_classes:
        errors.append("atomic counting classes are incomplete")
    expected_counts = {
        "lead": 3,
        "parenthetical": 6,
        "atomic": 6,
        "hyphenated": 4,
    }
    if contract.get("expected_counts") != expected_counts:
        errors.append("expected calculations are absent")
    return errors


def test_challenge_file_exists():
    assert PATH.is_file()


def test_ten_paired_natural_tasks_cover_surviving_g1_surface():
    data = _load()
    packs = data["scenario_packs"]
    assert [pack["id"] for pack in packs] == [f"BC-{n:02d}" for n in range(1, 11)]
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
    language_pack = next(pack for pack in _load()["scenario_packs"] if pack["id"] == "BC-09")
    assert language_pack["expected_not_observable"]
    assert "NOT_OBSERVABLE" in pack["coverage_limit"]


def test_controlled_negative_control_closes_authority_and_counting_contract():
    data = _load()
    assert challenge_errors(data) == []

    bad_literal_count = copy.deepcopy(data)
    pack = next(pack for pack in bad_literal_count["scenario_packs"] if pack["id"] == "BC-05")
    pack["closed_authority"]["exact_literal_counts"]["pathology"]["20 kPa"] = 2
    assert challenge_errors(bad_literal_count)

    bad_count = copy.deepcopy(data)
    pack = next(pack for pack in bad_count["scenario_packs"] if pack["id"] == "BC-10")
    pack["word_count_contract"]["expected_counts"]["lead"] = 4
    assert challenge_errors(bad_count)

    missing_sparse_authority = copy.deepcopy(data)
    pack = next(pack for pack in missing_sparse_authority["scenario_packs"] if pack["id"] == "BC-09")
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
    assert thresholds["minimum_packs_with_pathology_reduction"] == 8
    assert thresholds["maximum_control_false_positive_damage"] == 1


def test_prior_regressions_are_preregistered_at_the_right_evidence_layer():
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


def test_repaired_design_separates_prior_overloaded_controlled_families():
    packs = {pack["id"]: pack for pack in _load()["scenario_packs"]}
    lexical_families = ("STOW-WRD-", "STOW-MWN-", "STOW-VRB-", "STOW-SEN-", "STOW-STY-", "STOW-GEN-")
    assert set(packs["BC-09"]["positive_coverage"]) <= {
        rule for rule in _surviving_g1_ids() if rule.startswith(lexical_families)
    }
    assert set(packs["BC-10"]["positive_coverage"]) == {
        "STOW-PCT-004", "STOW-PCT-005", "STOW-PCT-006", "STOW-PCT-007"
    }
    assert len(packs["BC-05"]["positive_coverage"]) < 20
    assert "20 kPa" in packs["BC-05"]["pathology_input"]
    assert "However," in packs["BC-08"]["paired_negative_control"]
    assert "and its timer" in packs["BC-06"]["paired_negative_control"]


def test_completion_case_has_an_explicit_defensible_uncertainty_boundary():
    pack = next(pack for pack in _load()["scenario_packs"] if pack["id"] == "BC-02")
    for text in (pack["pathology_input"], pack["paired_negative_control"]):
        assert "parser check passed" in text.lower()
        assert "storage redesign" in text.lower()
        assert "timing" in text.lower()
        assert "tomorrow" in text.lower()
