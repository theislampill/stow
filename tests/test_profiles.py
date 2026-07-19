"""Profile resolver, activation matrix, and registry-consistency gates.

The resolver (skills/stow/runtime/profiles.py + rules/profiles.json) is the
single runtime authority on profile identity and check gating. These tests
pin, in both directions:

  * the resolver's shape and semantics (ids, aliases, lock, precedence);
  * the target behavior matrix for every profile-gated check;
  * scope fidelity: every CALLABLE registry record that is not always-on is
    silent outside its owning profile (the leakage class this pass removed);
  * predicate drift: the resolver's controlled include set equals the set of
    registry records whose activation predicate names the controlled profile.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import importlib.util
import json
import os
import sys

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")
RULES = os.path.join(REPO, "skills", "stow", "rules")
PROFILES_JSON = os.path.join(RULES, "profiles.json")
REGISTRY = os.path.join(RULES, "registry.yaml")

CONTROLLED_PREDICATE_PREFIX = "A controlled-technical writing profile is active"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


profiles = _load("profiles_under_test", os.path.join(RUNTIME, "profiles.py"))
lint_prose = _load("lint_prose_for_profiles", os.path.join(RUNTIME, "lint_prose.py"))

DATA = profiles.load_profiles()
TABLES = lint_prose.load_banned_lists()


def _registry():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        return yaml.load(fh)


REG = _registry()
RECORDS = REG["records"]


# --------------------------------------------------------------------------- #
# Shape and resolver semantics
# --------------------------------------------------------------------------- #

def test_profiles_json_shape():
    with open(PROFILES_JSON, encoding="utf-8") as fh:
        raw = json.load(fh)
    assert raw["schema_version"] == 1
    ids = [p["id"] for p in raw["profiles"]]
    assert ids == ["stow-default", "technical-clarity",
                   "controlled-technical-guided", "controlled-technical-strict"]
    for profile in raw["profiles"]:
        for key in ("id", "status", "locked", "aliases", "auto_contexts",
                    "includes", "guidance_rules", "lint_checks", "notes"):
            assert key in profile, "%s missing %s" % (profile["id"], key)
    assert raw["auto_precedence"] == [
        "controlled-technical-guided", "technical-clarity", "stow-default"]
    assert raw["artifact_modes"]["raw"]["prose_checks"] == "none"


def test_exactly_one_default_profile_for_editable_prose():
    defaults = [p["id"] for p in DATA["profiles"]
                if p.get("default_for_editable_prose")]
    assert defaults == ["stow-default"]


def test_resolver_default_alias_lock_and_unknown():
    assert profiles.resolve(None)["id"] == "stow-default"
    assert profiles.resolve("controlled-technical")["id"] == \
        "controlled-technical-guided"
    assert profiles.resolve("technical-clarity")["id"] == "technical-clarity"
    with pytest.raises(profiles.LockedProfileError):
        profiles.resolve("controlled-technical-strict")
    with pytest.raises(profiles.UnknownProfileError):
        profiles.resolve("no-such-profile")


def test_strict_profile_is_locked_in_the_data():
    strict = [p for p in DATA["profiles"]
              if p["id"] == "controlled-technical-strict"]
    assert strict and strict[0]["locked"] is True
    assert strict[0]["status"] == "locked"


def test_cli_choices_cover_every_id_and_alias():
    choices = set(lint_prose._profile_choices())
    expected = set()
    for profile in DATA["profiles"]:
        expected.add(profile["id"])
        expected.update(profile.get("aliases", []))
    assert choices == expected


def test_profiles_cli_resolves_and_reports_lock(capsys):
    assert profiles.main(["resolve", "controlled-technical"]) == 0
    assert capsys.readouterr().out.strip() == "controlled-technical-guided"
    assert profiles.main(["resolve", "controlled-technical-strict"]) == 2
    assert "locked" in capsys.readouterr().out
    assert profiles.main(["resolve", "nope"]) == 1


def test_check_active_defaults_to_always_on_for_unlisted_checks():
    default = profiles.resolve("stow-default")
    guided = profiles.resolve("controlled-technical-guided")
    # Unlisted -> always on, under every profile.
    assert profiles.check_active("em-dash", default)
    assert profiles.check_active("em-dash", guided)
    # Listed -> the profile decides.
    assert not profiles.check_active("semicolon", default)
    assert profiles.check_active("semicolon", guided)


# --------------------------------------------------------------------------- #
# Target behavior matrix -- the composition contract, row by row
# --------------------------------------------------------------------------- #

DEFAULT = "stow-default"
CLARITY = "technical-clarity"
GUIDED = "controlled-technical-guided"

CONTRACTION = "The cache isn't warm yet."
SEMICOLON = "The cache is cold; restart it."
EM_DASH = u"The cache is cold — restart it."
LATIN = "Flush the caches, e.g. the write cache."
PROC_21 = "- " + " ".join(["word"] * 21) + "."
DESC_26 = " ".join(["word"] * 26) + "."
SIX_ITEMS = "".join("- do task %d now\n" % i for i in range(6))
QUOTED = 'The report said "it isn\'t cold; restart it" yesterday.'
RAW_JSON = u'{"note": "Furthermore, we leverage it — robust; e.g. etc. isn\'t"}'

MATRIX = [
    # (case, text, profile, rule, expect_finding, extra-kwargs)
    ("default-contraction",   CONTRACTION, DEFAULT, "contraction", False, {}),
    ("controlled-contraction", CONTRACTION, GUIDED, "contraction", True,  {}),
    ("default-semicolon",     SEMICOLON,   DEFAULT, "semicolon",   False, {}),
    ("controlled-semicolon",  SEMICOLON,   GUIDED,  "semicolon",   True,  {}),
    ("default-em-dash",       EM_DASH,     DEFAULT, "em-dash",     True,  {}),
    ("controlled-em-dash",    EM_DASH,     GUIDED,  "em-dash",     True,  {}),
    ("default-latin",         LATIN,       DEFAULT, "latin-abbreviation", False, {}),
    ("controlled-latin",      LATIN,       GUIDED,  "latin-abbreviation", True,  {}),
    ("default-proc-cap",      PROC_21,     DEFAULT, "procedural-sentence-length", False, {}),
    ("controlled-proc-cap",   PROC_21,     GUIDED,  "procedural-sentence-length", True,  {}),
    ("default-desc-cap",      DESC_26,     DEFAULT, "descriptive-sentence-length", False, {}),
    ("controlled-desc-cap",   DESC_26,     GUIDED,  "descriptive-sentence-length", True,  {}),
    ("action-queue-advisory", SIX_ITEMS,   DEFAULT, "list-length", True,  {}),
    ("exhaustive-list-permitted", SIX_ITEMS, DEFAULT, "list-length", False,
     {"exhaustive_lists_ok": True}),
    ("quoted-spans-unflagged-contraction", QUOTED, GUIDED, "contraction", False, {}),
    ("quoted-spans-unflagged-semicolon",   QUOTED, GUIDED, "semicolon",   False, {}),
    ("clarity-contraction",   CONTRACTION, CLARITY, "contraction", False, {}),
    ("clarity-semicolon",     SEMICOLON,   CLARITY, "semicolon",   False, {}),
]


@pytest.mark.parametrize("case,text,profile,rule,expect,kw",
                         MATRIX, ids=[m[0] for m in MATRIX])
def test_target_behavior_matrix(case, text, profile, rule, expect, kw):
    found = [a for a in
             lint_prose.lint(text, profile=profile, tables=TABLES, **kw)
             if a.rule == rule]
    if expect:
        assert found, "%s: expected a %s finding" % (case, rule)
    else:
        assert not found, "%s: unexpected %s finding: %r" % (case, rule, found)


def test_raw_structured_artifact_is_never_prose_linted():
    assert lint_prose.lint(RAW_JSON, tables=TABLES,
                           artifact_type="structured") == []
    assert lint_prose.lint(RAW_JSON, tables=TABLES, artifact_type="raw") == []


# --------------------------------------------------------------------------- #
# Scope fidelity -- callable but not always-on => silent outside its profile
# --------------------------------------------------------------------------- #

# Tripping fixture per profile-gated CALLABLE validator. A new callable,
# profile-gated record without a fixture here fails the coverage assert below.
GATED_FIXTURES = {
    "no-semicolon": (SEMICOLON, "semicolon"),
    "no-latin-abbreviations": (LATIN, "latin-abbreviation"),
    "procedural-sentence-max-20-words": (PROC_21, "procedural-sentence-length"),
    "descriptive-sentence-max-25-words": (DESC_26, "descriptive-sentence-length"),
}


def _gated_callable_records():
    out = []
    for record in RECORDS:
        enforcement = record.get("enforcement", {})
        activation = record.get("activation", {})
        if enforcement.get("status") != "callable":
            continue
        if activation.get("always_on_for_prose"):
            continue
        out.append(record)
    return out


def test_every_gated_callable_record_has_a_scope_fixture():
    gated = _gated_callable_records()
    assert gated, "expected profile-gated callable records in the registry"
    validators = {r["enforcement"]["validator"] for r in gated}
    assert validators == set(GATED_FIXTURES), (
        "profile-gated callable validators changed; update GATED_FIXTURES: %s"
        % validators.symmetric_difference(set(GATED_FIXTURES)))


@pytest.mark.parametrize("validator", sorted(GATED_FIXTURES))
def test_no_profile_leakage_for_gated_callable_checks(validator):
    text, rule = GATED_FIXTURES[validator]
    for profile in (None, DEFAULT, CLARITY):
        found = [a for a in lint_prose.lint(text, profile=profile, tables=TABLES)
                 if a.rule == rule]
        assert not found, (
            "%s leaked outside the controlled profile (profile=%r): %r"
            % (validator, profile, found))
    found = [a for a in lint_prose.lint(text, profile=GUIDED, tables=TABLES)
             if a.rule == rule]
    assert found, "%s did not fire under its owning profile" % validator


# --------------------------------------------------------------------------- #
# Predicate drift -- resolver include set == registry predicate set
# --------------------------------------------------------------------------- #

def test_guided_include_set_matches_the_registry_predicates():
    guided = profiles.resolve(GUIDED)
    prefixes = tuple(guided["includes"]["category_prefixes"])
    by_prefix = {
        r["id"] for r in RECORDS
        if r["id"].split("-")[1] in prefixes
    }
    by_predicate = {
        r["id"] for r in RECORDS
        if r["activation"]["predicate"].startswith(CONTROLLED_PREDICATE_PREFIX)
    }
    assert by_prefix == by_predicate, (
        "resolver category prefixes and registry predicates disagree: %s"
        % by_prefix.symmetric_difference(by_predicate))


def test_guidance_rules_are_registry_records_inside_the_controlled_set():
    clarity = profiles.resolve(CLARITY)
    ids = {r["id"] for r in RECORDS}
    controlled = {
        r["id"] for r in RECORDS
        if r["activation"]["predicate"].startswith(CONTROLLED_PREDICATE_PREFIX)
    }
    for rule_id in clarity["guidance_rules"]:
        assert rule_id in ids, "unknown guidance rule %s" % rule_id
        assert rule_id in controlled, (
            "guidance rule %s is not a controlled-family record" % rule_id)


def test_default_and_clarity_include_only_the_always_on_selector():
    for name in (DEFAULT, CLARITY):
        record = profiles.resolve(name)
        assert record["includes"].get("selector") == "always_on_for_prose"
        assert "category_prefixes" not in record["includes"]


def test_gated_lint_checks_agree_across_profiles():
    """Every profile lists the SAME set of gated check names, so a check can
    never be accidentally ungated by being absent from one profile's map."""
    maps = [set(p["lint_checks"]) for p in DATA["profiles"]
            if not p.get("locked")]
    assert maps and all(m == maps[0] for m in maps)
