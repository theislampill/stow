"""Tier-1 controlled-dictionary extraction and sparse-lookup contracts."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "tools" / "data" / "controlled-dictionary-v1.json"
PROJECTION = ROOT / "skills" / "stow" / "rules" / "controlled-dictionary-v1.json.gz"
SCHEMA = ROOT / "skills" / "stow" / "rules" / "controlled-dictionary.schema.json"
GENERATOR = ROOT / "tools" / "gen_controlled_dictionary.py"
RUNTIME = ROOT / "skills" / "stow" / "runtime" / "dictionary_lookup.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def generator():
    return load_module("controlled_dictionary_generator", GENERATOR)


@pytest.fixture(scope="module")
def runtime():
    return load_module("controlled_dictionary_runtime", RUNTIME)


@pytest.fixture(scope="module")
def dictionary():
    return load_json(CANONICAL)


def test_canonical_dictionary_has_exact_accounting_and_schema(dictionary):
    assert dictionary["schema_version"] == 1
    assert dictionary["normalization"] == "NFKC-casefold-whitespace"
    assert dictionary["extraction_scope"].endswith(
        "example columns are intentionally excluded"
    )
    counts = dictionary["generated_counts"]
    assert counts == {
        "records": 2198,
        "approved": 879,
        "not_approved": 1319,
        "letter_sections": 25,
        "approved_verbs": 208,
    }
    assert len(dictionary["records"]) == counts["records"]
    assert SCHEMA.is_file()
    Draft202012Validator(load_json(SCHEMA)).validate(dictionary)


def test_every_record_is_source_neutral_complete_and_uniquely_located(dictionary):
    required = {
        "locator", "source_expression_raw", "headword_raw",
        "normalized_base_key", "part_of_speech", "status",
        "construction_annotation_raw", "forms_raw", "approved_forms",
        "form_parse_state", "meaning_or_alternatives_raw",
    }
    records = dictionary["records"]
    assert all(set(record) == required for record in records)
    locators = [record["locator"] for record in records]
    assert len(locators) == len(set(locators))
    rendered = CANONICAL.read_text(encoding="utf-8").lower()
    assert "source_sha" not in rendered
    assert "source_path" not in rendered
    assert "source_line" not in rendered


def test_collisions_and_source_anomalies_are_preserved_not_overwritten(dictionary):
    by_key = {}
    for record in dictionary["records"]:
        by_key.setdefault(
            (record["normalized_base_key"], record["part_of_speech"]), []
        ).append(record)
    get_records = by_key[("get", "v")]
    assert {record["status"] for record in get_records} == {
        "approved", "not_approved"
    }
    prevent_records = by_key[("prevent", "v")]
    assert {record["status"] for record in prevent_records} == {
        "approved", "not_approved"
    }
    contact = next(
        record for record in dictionary["records"]
        if record["headword_raw"] == "CONTACT" and record["part_of_speech"] == "v"
    )
    assert contact["form_parse_state"] == "source-separator-anomaly"
    assert contact["approved_forms"] == [
        "CONTACT", "CONTACTS", "CONTACTED", "CONTACTED"
    ]
    anomalies = [
        record for record in dictionary["records"]
        if record["form_parse_state"] == "source-separator-anomaly"
    ]
    assert {record["headword_raw"] for record in anomalies} == {
        "CONTACT", "EAT", "OCCUR", "PROTRUDE", "SPRAY"
    }
    be_record = next(
        record for record in dictionary["records"]
        if record["headword_raw"] == "BE" and record["part_of_speech"] == "v"
    )
    assert be_record["approved_forms"] == ["BE", "IS", "WAS", "ARE", "WERE"]
    eat_record = next(
        record for record in dictionary["records"]
        if record["headword_raw"] == "EAT" and record["part_of_speech"] == "v"
    )
    assert eat_record["approved_forms"] == ["EAT", "EATS", "ATE"]
    assert eat_record["form_parse_state"] == "source-separator-anomaly"
    unclassified = [
        record["headword_raw"] for record in dictionary["records"]
        if record["part_of_speech"] == "unclassified"
    ]
    assert unclassified == ["FOR EXAMPLE", "such as"]


def test_projection_is_deterministic_and_exactly_matches_canonical(generator):
    expected = generator.projection_bytes(load_json(CANONICAL))
    assert PROJECTION.read_bytes() == expected
    assert generator.projection_bytes(load_json(CANONICAL)) == expected
    with gzip.open(PROJECTION, "rb") as handle:
        projected = json.loads(handle.read().decode("utf-8"))
    assert projected == generator.runtime_projection(load_json(CANONICAL))
    Draft202012Validator(load_json(SCHEMA)).validate(projected)
    assert hashlib.sha256(expected).hexdigest() == hashlib.sha256(
        generator.projection_bytes(load_json(CANONICAL))
    ).hexdigest()


def test_extractor_fails_closed_and_preserves_raw_cells(generator):
    source = """## A

| Word (part of speech) | Status | Approved meaning / Alternative(s) | Example | Other |
|---|---|---|---|---|
| ACT (v), ACTS, ACTED, ACTED | approved | To do something | ACT NOW. |  |
| act (n) | not approved | ACTION (n) | DO THE ACTION. | Do an act. |

---

## Appendix 1
"""
    parsed = generator.extract_text(source, expected_sections=("A",))
    assert parsed["generated_counts"]["records"] == 2
    assert parsed["records"][0]["source_expression_raw"] == \
        "ACT (v), ACTS, ACTED, ACTED"
    malformed = source.replace("| act (n) |", "| act (n) | extra |")
    with pytest.raises(generator.ExtractionError):
        generator.extract_text(malformed, expected_sections=("A",))
    missing_pipe = source.replace(
        "| act (n) | not approved |", "act (n) | not approved |"
    )
    with pytest.raises(generator.ExtractionError):
        generator.extract_text(missing_pipe, expected_sections=("A",))
    duplicate = source.replace("\n---\n", "\n| act (n) | not approved | ACTION (n) | DO THE ACTION. | Do an act. |\n\n---\n")
    with pytest.raises(generator.ExtractionError):
        generator.extract_text(duplicate, expected_sections=("A",))


def test_semantic_validation_rejects_false_counts_and_keys(generator, dictionary):
    altered = json.loads(json.dumps(dictionary))
    altered["generated_counts"]["records"] -= 1
    with pytest.raises(generator.ExtractionError):
        generator.validate_value(altered)
    altered = json.loads(json.dumps(dictionary))
    altered["records"][0]["normalized_base_key"] = "wrong"
    with pytest.raises(generator.ExtractionError):
        generator.validate_value(altered)


def test_lookup_is_sparse_collision_safe_and_honest(runtime):
    data = runtime.load_dictionary(PROJECTION)
    approved = runtime.lookup(data, "ABSORBS")
    assert approved["classification"] == "FORM_LISTED"
    assert {row["headword_raw"] for row in approved["records"]} == {"ABSORB"}

    rejected = runtime.lookup(data, "accomplish")
    assert rejected["classification"] == "KNOWN_NOT_APPROVED_CANDIDATE"
    assert rejected["records"][0]["meaning_or_alternatives_raw"]

    ambiguous = runtime.lookup(data, "get")
    assert ambiguous["classification"] == "AMBIGUOUS"
    assert {row["status"] for row in ambiguous["records"]} == {
        "approved", "not_approved"
    }

    unknown = runtime.lookup(data, "fluxwidget")
    assert unknown["classification"] == "UNKNOWN"
    assert unknown["records"] == []

    assert runtime.check_form(data, "ABSORB", "ABSORBED")["classification"] == \
        "FORM_LISTED"
    assert runtime.check_form(data, "ABSORB", "ABSORBING")["classification"] == \
        "FORM_UNKNOWN"
    assert runtime.check_form(data, "BE", "ARE")["classification"] == "FORM_LISTED"
    assert runtime.check_form(data, "EAT", "ATE")["classification"] == "FORM_LISTED"
    assert runtime.lookup(data, "MATTE")["classification"] == \
        "KNOWN_APPROVED_CANDIDATE"
    assert runtime.lookup(data, "no longer")["classification"] == \
        "KNOWN_NOT_APPROVED_CANDIDATE"


def test_scan_is_cold_sparse_and_skips_caller_labeled_protected_text(runtime):
    data = runtime.load_dictionary(PROJECTION)
    candidate = {
        "schema_version": 1,
        "segments": [
            {"kind": "editable", "text": "Accomplish the task according to the manual."},
            {"kind": "protected", "text": "accomplish according to"},
        ],
    }
    result = runtime.scan(data, candidate)
    assert result["status"] == "REVIEW"
    assert [(row["surface"].lower(), row["segment_index"]) for row in result["findings"]] == [
        ("accomplish", 0), ("according to", 0)
    ]
    assert all(row["classification"] != "KNOWN_APPROVED_CANDIDATE"
               for row in result["findings"])


def test_scan_does_not_claim_unknown_terms_are_nonconformant(runtime):
    data = runtime.load_dictionary(PROJECTION)
    result = runtime.scan(data, {
        "schema_version": 1,
        "segments": [{"kind": "editable", "text": "Fluxwidget."}],
    })
    assert result == {
        "status": "NO_KNOWN_DICTIONARY_FINDINGS",
        "findings": [],
        "boundary": runtime.SCAN_BOUNDARY,
    }


def test_scan_consumes_approved_multiword_expression_before_inner_terms(runtime):
    data = runtime.load_dictionary(PROJECTION)
    result = runtime.scan(data, {
        "schema_version": 1,
        "segments": [{"kind": "editable", "text": "The task is in progress."}],
    })
    assert all(finding["surface"].lower() != "progress"
               for finding in result["findings"])


@pytest.mark.parametrize("text", ["re-", "re-install"])
def test_scan_reports_declared_not_approved_prefix_surface(runtime, text):
    data = runtime.load_dictionary(PROJECTION)
    result = runtime.scan(data, {
        "schema_version": 1,
        "segments": [{"kind": "editable", "text": text}],
    })
    assert result["status"] == "REVIEW"
    assert [(finding["surface"], finding["classification"])
            for finding in result["findings"]] == [
        ("re-", "KNOWN_NOT_APPROVED_CANDIDATE")
    ]


def test_prefix_scan_preserves_base_word_and_protected_segment_boundaries(runtime):
    data = runtime.load_dictionary(PROJECTION)
    result = runtime.scan(data, {
        "schema_version": 1,
        "segments": [
            {"kind": "editable", "text": "Accomplish-"},
            {"kind": "protected", "text": "re-install"},
        ],
    })
    assert [finding["surface"].lower() for finding in result["findings"]] == [
        "accomplish"
    ]


def test_runtime_rejects_malformed_projection_semantics(runtime):
    with gzip.open(PROJECTION, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    value["records"][0]["status"] = "bogus"
    with pytest.raises(runtime.DictionaryError):
        runtime._validate_document(value)
    with gzip.open(PROJECTION, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    value["records"][0]["headword_raw"] = ""
    value["records"][0]["normalized_base_key"] = ""
    with pytest.raises(runtime.DictionaryError):
        runtime._validate_document(value)
    with gzip.open(PROJECTION, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    value["schema_version"] = True
    value["generated_counts"]["records"] = True
    with pytest.raises(runtime.DictionaryError):
        runtime._validate_document(value)
    with pytest.raises(runtime.DictionaryError):
        runtime._validate_candidate({
            "schema_version": True,
            "segments": [{"kind": "editable", "text": "text"}],
        })
    value = {"schema_version": 1, "normalization": "NFKC-casefold-whitespace",
             "generated_counts": [], "records": []}
    with pytest.raises(runtime.DictionaryError):
        runtime._validate_document(value)
