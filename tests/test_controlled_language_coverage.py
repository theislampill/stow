from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = ROOT / "docs" / "controlled-language-coverage.yaml"
REGISTRY_PATH = ROOT / "skills" / "stow" / "rules" / "registry.yaml"
DISPOSITIONS_PATH = ROOT / "docs" / "rule-dispositions.yaml"
PROFILES_PATH = ROOT / "skills" / "stow" / "rules" / "profiles.json"

CONTROLLED_PREFIXES = {
    "WRD", "MWN", "VRB", "SEN", "PRC", "DSC", "SAF", "PCT", "STY", "GEN"
}
DICTIONARY_AXES = {
    "approved-membership",
    "not-approved-alternatives",
    "approved-explicit-forms",
    "meaning-and-part-of-speech",
    "project-technical-nouns",
    "project-technical-verbs",
    "protected-exact-text",
    "strict-conformance",
}
VALID_STATUSES = {
    "IMPLEMENTED",
    "PARTIAL",
    "GUIDANCE_ONLY",
    "EXTERNAL_AUTHORITY_REQUIRED",
    "NOT_FEASIBLY_MECHANICAL",
    "NOT_IMPLEMENTED",
    "DEFERRED_AS_COSTLY_CONTEXTUAL_ENFORCEMENT",
}


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def controlled_id(rule_id):
    return rule_id.split("-")[1] in CONTROLLED_PREFIXES


def test_every_historical_controlled_requirement_has_one_coverage_row():
    coverage = load_yaml(COVERAGE_PATH)
    dispositions = load_yaml(DISPOSITIONS_PATH)
    expected = {
        row["id"] for row in dispositions["records"] if controlled_id(row["id"])
    }
    actual = [row["historical_id"] for row in coverage["requirements"]]
    assert len(actual) == len(set(actual))
    assert set(actual) == expected
    assert all(row["status"] in VALID_STATUSES for row in coverage["requirements"])


def test_coverage_owners_follow_terminal_dispositions_and_active_registry():
    coverage = load_yaml(COVERAGE_PATH)
    dispositions = {
        row["id"]: row for row in load_yaml(DISPOSITIONS_PATH)["records"]
    }
    active = {
        row["id"] for row in load_yaml(REGISTRY_PATH)["records"]
    }
    for row in coverage["requirements"]:
        historical_id = row["historical_id"]
        disposition = dispositions[historical_id]
        assert row["historical_disposition"] == disposition["disposition"]
        assert set(row["semantic_owners"]) <= active
        if disposition["disposition"] == "MERGE":
            assert row["semantic_owners"] == disposition["target"]["rule_ids"]
        elif disposition["disposition"] == "DROP":
            assert row["semantic_owners"] == []
            assert row["status"] == "NOT_IMPLEMENTED"
        else:
            assert row["semantic_owners"] == [historical_id]


def test_merge_preservation_terms_are_present_in_active_owner_titles():
    coverage = load_yaml(COVERAGE_PATH)
    registry = {
        row["id"]: row for row in load_yaml(REGISTRY_PATH)["records"]
    }
    for row in coverage["requirements"]:
        terms = row.get("preservation_terms", [])
        if not terms:
            continue
        owner_text = " ".join(
            registry[owner]["title"].lower() for owner in row["semantic_owners"]
        )
        for term in terms:
            assert term.lower() in owner_text, (row["historical_id"], term, owner_text)


def test_explicit_source_subrequirements_remain_accounted_in_owner_wording():
    coverage = load_yaml(COVERAGE_PATH)
    explicit = {
        row["source_ordinal"]: row["explicit_subrequirements"]
        for row in coverage["requirements"]
        if "explicit_subrequirements" in row
    }
    assert explicit == {"1.1": 3, "2.2": 2, "3.2": 6, "8.3": 7, "8.6": 7}
    assert sum(explicit.values()) == 25


def test_dictionary_axes_are_complete_and_tiered_without_unlocking_strict_mode():
    coverage = load_yaml(COVERAGE_PATH)
    axes = {row["id"]: row for row in coverage["dictionary_axes"]}
    assert set(axes) == DICTIONARY_AXES
    assert all(row["tier"] in {1, 2, 3, 4} for row in axes.values())
    assert all(row["status"] in VALID_STATUSES for row in axes.values())
    assert axes["meaning-and-part-of-speech"]["tier"] == 3
    assert axes["approved-membership"]["status"] == "IMPLEMENTED"
    assert axes["approved-explicit-forms"]["status"] == "IMPLEMENTED"
    assert axes["not-approved-alternatives"]["status"] == "PARTIAL"
    assert axes["project-technical-nouns"]["status"] == "EXTERNAL_AUTHORITY_REQUIRED"
    assert axes["project-technical-verbs"]["status"] == "EXTERNAL_AUTHORITY_REQUIRED"
    assert axes["strict-conformance"]["tier"] == 4

    profiles = __import__("json").loads(PROFILES_PATH.read_text(encoding="utf-8"))
    strict = next(
        profile for profile in profiles["profiles"]
        if profile["id"] == "controlled-technical-strict"
    )
    assert strict["locked"] is True
    assert strict["status"] == "locked"


def test_controlled_coverage_remains_off_the_ordinary_hot_path():
    profiles = __import__("json").loads(PROFILES_PATH.read_text(encoding="utf-8"))
    ordinary = next(profile for profile in profiles["profiles"] if profile["id"] == "stow-default")
    prefixes = set((ordinary.get("includes") or {}).get("category_prefixes") or [])
    assert not (prefixes & CONTROLLED_PREFIXES)
    assert ordinary["guidance_rules"] == []
