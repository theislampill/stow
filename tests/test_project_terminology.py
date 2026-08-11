"""Project-local terminology authority overlay contracts.

The overlay is explicitly selected by a caller.  It supplies project
declarations without turning candidate terms, examples, or lexical membership
into contextual sense proof.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "stow" / "runtime" / "dictionary_lookup.py"
DICTIONARY = (
    ROOT / "skills" / "stow" / "rules" / "controlled-dictionary-v1.json.gz"
)
SCHEMA = ROOT / "skills" / "stow" / "rules" / "project-terminology.schema.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runtime():
    return load_module("project_terminology_runtime", RUNTIME)


@pytest.fixture(scope="module")
def dictionary(runtime):
    return runtime.load_dictionary(DICTIONARY)


def record(
    term,
    *,
    kind="technical-noun",
    status="approved",
    preferred_form=None,
    approved_forms=None,
    nonpreferred_forms=None,
    match="token-casefold",
    good_example=None,
    bad_example=None,
):
    value = {
        "term": term,
        "kind": kind,
        "status": status,
        "preferred_form": preferred_form,
        "approved_forms": approved_forms or [],
        "nonpreferred_forms": nonpreferred_forms or [],
        "meaning_scope": "The declared project meaning only.",
        "source_locator": "project-glossary#" + term.replace(" ", "-"),
        "match": match,
    }
    if good_example is not None:
        value["good_example"] = {
            "text": good_example,
            "origin": "project-authority",
        }
    if bad_example is not None:
        value["bad_example"] = {
            "text": bad_example,
            "origin": "project-authority",
        }
    return value


def authority(*records):
    return {
        "schema_version": 1,
        "normalization": "NFKC-casefold-whitespace",
        "authority": {
            "id": "maintenance-terms",
            "kind": "project-glossary",
            "revision": "2026-08-11",
            "source": "docs/glossary.md",
        },
        "records": list(records),
    }


def segments(*items):
    return {"schema_version": 1, "segments": list(items)}


def test_schema_accepts_a_bounded_authority_document():
    value = authority(record(
        "purge assembly",
        preferred_form="purge assembly",
        approved_forms=["purge assembly", "purge assemblies"],
        nonpreferred_forms=["purge gizmo"],
        good_example="Inspect the purge assembly.",
        bad_example="Inspect the purge gizmo.",
    ))

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(value)


def test_overlay_requires_explicit_selection_and_is_never_auto_discovered(
    tmp_path, monkeypatch, runtime, dictionary,
):
    hidden = tmp_path / ".stow"
    hidden.mkdir()
    (hidden / "terminology.json").write_text(
        json.dumps(authority(record(
            "fluxwidget", preferred_form="fluxwidget",
            approved_forms=["fluxwidget"],
        ))),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = runtime.lookup(dictionary, "fluxwidget")

    assert result["classification"] == "UNKNOWN"
    assert "project_records" not in result


def test_approved_project_term_precedes_a_fixed_dictionary_rejection(
    runtime, dictionary,
):
    overlay = runtime.validate_authority(authority(record(
        "accomplish",
        kind="technical-verb",
        preferred_form="accomplish",
        approved_forms=["accomplish", "accomplishes"],
    )))

    result = runtime.lookup(dictionary, "accomplish", authority=overlay)

    assert result["classification"] == "PROJECT_APPROVED_DECLARATION"
    assert result["project_classification"] == "PROJECT_APPROVED_DECLARATION"
    assert result["dictionary_classification"] == "KNOWN_NOT_APPROVED_CANDIDATE"
    assert [row["term"] for row in result["project_records"]] == ["accomplish"]
    assert result["records"][0]["status"] == "not_approved"
    assert "sense" in result["boundary"]


def test_candidate_never_becomes_authoritative_and_fixed_facts_coexist(
    runtime, dictionary,
):
    overlay = runtime.validate_authority(authority(record(
        "ABSORB",
        kind="technical-verb",
        status="candidate",
    )))

    result = runtime.lookup(dictionary, "ABSORB", authority=overlay)

    assert result["classification"] == "PROJECT_CANDIDATE"
    assert result["project_classification"] == "PROJECT_CANDIDATE"
    assert result["dictionary_classification"] == "KNOWN_APPROVED_CANDIDATE"
    assert result["records"][0]["headword_raw"] == "ABSORB"
    assert "never approvals" in result["boundary"]


def test_nonpreferred_and_rejected_forms_support_consistent_reuse(
    runtime, dictionary,
):
    overlay = runtime.validate_authority(authority(
        record(
            "purge-assembly",
            preferred_form="purge control assembly",
            approved_forms=["purge control assembly"],
            nonpreferred_forms=["purge gizmo"],
        ),
        record(
            "dump rig",
            status="rejected",
            preferred_form="purge control assembly",
        ),
    ))

    result = runtime.scan(dictionary, segments({
        "kind": "editable",
        "text": "Inspect the purge gizmo. Do not call it the dump rig.",
    }), authority=overlay)

    assert result["status"] == "REVIEW"
    project_findings = [
        finding for finding in result["findings"]
        if finding["classification"].startswith("PROJECT_")
    ]
    assert [finding["classification"] for finding in project_findings] == [
        "PROJECT_NONPREFERRED", "PROJECT_REJECTED",
    ]
    assert [finding["preferred_form"] for finding in project_findings] == [
        "purge control assembly", "purge control assembly",
    ]


def test_protected_segments_precede_project_and_fixed_lookup(runtime, dictionary):
    overlay = runtime.validate_authority(authority(record(
        "accomplish",
        kind="technical-verb",
        preferred_form="accomplish",
        approved_forms=["accomplish"],
        nonpreferred_forms=["purge gizmo"],
    )))

    result = runtime.scan(dictionary, segments(
        {"kind": "protected", "text": "purge gizmo accomplish"},
        {"kind": "editable", "text": "accomplish"},
    ), authority=overlay)

    assert result["findings"] == []
    assert result["status"] == "NO_KNOWN_DICTIONARY_FINDINGS"


def test_colliding_project_surfaces_fail_closed(runtime):
    value = authority(
        record(
            "first",
            preferred_form="purge assembly",
            approved_forms=["purge assembly"],
        ),
        record(
            "second",
            preferred_form="other assembly",
            approved_forms=["other assembly"],
            nonpreferred_forms=["PURGE ASSEMBLY"],
        ),
    )

    with pytest.raises(runtime.DictionaryError, match="collision"):
        runtime.validate_authority(value)


def test_term_to_surface_ambiguity_fails_closed(runtime):
    value = authority(
        record(
            "actuator-concept",
            preferred_form="actuator",
            approved_forms=["actuator"],
        ),
        record(
            "actuator",
            preferred_form="servo",
            approved_forms=["servo"],
        ),
    )

    with pytest.raises(runtime.DictionaryError, match="collision"):
        runtime.validate_authority(value)


def test_malformed_or_ambiguous_authority_file_fails_closed(tmp_path, runtime):
    path = tmp_path / "terms.json"
    path.write_text(
        '{"schema_version":1,"schema_version":1}', encoding="utf-8"
    )

    with pytest.raises(runtime.DictionaryError, match="duplicate JSON key"):
        runtime.load_authority(path)


def test_optional_examples_are_sparse_and_non_authoritative(runtime, dictionary):
    overlay = runtime.validate_authority(authority(
        record(
            "actuator",
            preferred_form="actuator",
            approved_forms=["actuator", "actuators"],
            good_example="Inspect the actuator.",
            bad_example="Inspect the control thing.",
        ),
        record(
            "relay",
            preferred_form="relay",
            approved_forms=["relay", "relays"],
            good_example="Inspect the relay.",
        ),
    ))

    result = runtime.lookup(dictionary, "actuator", authority=overlay)

    assert len(result["project_records"]) == 1
    assert result["project_records"][0]["good_example"] == {
        "text": "Inspect the actuator.",
        "origin": "project-authority",
    }
    assert "non-authoritative" in result["boundary"]


@pytest.mark.parametrize(
    "bad_example",
    [
        "unstructured example",
        {"text": "Inspect the actuator."},
        {"text": "Inspect the actuator.", "origin": "unknown"},
        {
            "text": "Inspect the actuator.",
            "origin": "project-authority",
            "extra": True,
        },
    ],
)
@pytest.mark.parametrize("field", ["good_example", "bad_example"])
def test_example_origin_contract_fails_closed(runtime, bad_example, field):
    value = authority(record(
        "actuator",
        preferred_form="actuator",
        approved_forms=["actuator"],
    ))
    value["records"][0][field] = bad_example

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(value))

    with pytest.raises(runtime.DictionaryError, match=field):
        runtime.validate_authority(value)


def test_loading_and_lookup_do_not_mutate_the_authority_file(
    tmp_path, runtime, dictionary,
):
    path = tmp_path / "terms.json"
    path.write_text(json.dumps(authority(record(
        "actuator",
        preferred_form="actuator",
        approved_forms=["actuator", "actuators"],
    )), sort_keys=True), encoding="utf-8")
    before = path.read_bytes()

    overlay = runtime.load_authority(path)
    runtime.lookup(dictionary, "actuator", authority=overlay)
    runtime.scan(dictionary, segments({
        "kind": "editable", "text": "Inspect the actuator."
    }), authority=overlay)

    assert path.read_bytes() == before
