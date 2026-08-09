"""Behavioral contract for the closed-map canonical-term validator.

The validator is a G2 label-policy mechanism. These tests exercise its real
CLI and derive expected statuses and offsets directly from self-authored JSON
fixtures. They do not treat caller labels as semantic classifications.
"""

import json
import os
import subprocess
import sys

import pytest


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VALIDATE_TERMS = os.path.join(
    REPO, "skills", "stow", "runtime", "validate_terms.py")


def _write_json(path, value):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False)
        handle.write("\n")


def _base_map(**overrides):
    value = {
        "schema_version": 1,
        "case_sensitive": True,
        "entries": [{
            "canonical": "preferred term",
            "forbidden_variants": ["legacy term"],
            "match": "literal",
        }],
    }
    value.update(overrides)
    return value


def _segments(*segments):
    return {"schema_version": 1, "segments": list(segments)}


def _run_files(map_path, segments_path, isolated=False):
    interpreter = [sys.executable]
    if isolated:
        interpreter.extend(["-I", "-S"])
    return subprocess.run(
        interpreter + [
            VALIDATE_TERMS,
            "--map", str(map_path),
            "--segments", str(segments_path),
        ],
        capture_output=True,
        text=True,
    )


def _run(tmp_path, mapping, candidate, isolated=False):
    map_path = tmp_path / "terms.json"
    segments_path = tmp_path / "segments.json"
    _write_json(map_path, mapping)
    _write_json(segments_path, candidate)
    return _run_files(map_path, segments_path, isolated=isolated)


def _result(proc):
    assert proc.stderr == ""
    return json.loads(proc.stdout)


def test_compliant_result_is_stdlib_only_and_has_no_findings(tmp_path):
    proc = _run(
        tmp_path,
        _base_map(),
        _segments({"kind": "editable", "text": "Use the preferred term."}),
        isolated=True,
    )

    assert proc.returncode == 0
    assert _result(proc) == {"findings": [], "status": "COMPLIANT"}


def test_forbidden_literal_reports_zero_based_end_exclusive_offsets(tmp_path):
    proc = _run(
        tmp_path,
        _base_map(),
        _segments({"kind": "editable", "text": "Use legacy term here."}),
    )

    assert proc.returncode == 1
    assert _result(proc) == {
        "findings": [{
            "canonical": "preferred term",
            "end": 15,
            "forbidden_variant": "legacy term",
            "segment_index": 0,
            "start": 4,
        }],
        "status": "NONCOMPLIANT",
    }


def test_protected_segments_are_not_scanned(tmp_path):
    proc = _run(
        tmp_path,
        _base_map(),
        _segments(
            {"kind": "protected", "text": "Keep legacy term unchanged."},
            {"kind": "editable", "text": "Use the preferred term."},
        ),
    )

    assert proc.returncode == 0
    assert _result(proc)["status"] == "COMPLIANT"


@pytest.mark.parametrize(
    ("case_sensitive", "expected_offsets"),
    [
        (True, [(14, 20)]),
        (False, [(0, 6), (7, 13), (14, 20)]),
    ],
)
def test_case_mode_controls_matching(tmp_path, case_sensitive, expected_offsets):
    mapping = _base_map(
        case_sensitive=case_sensitive,
        entries=[{
            "canonical": "current",
            "forbidden_variants": "Legacy",
            "match": "literal",
        }],
    )
    proc = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "legacy LEGACY Legacy"}),
    )

    assert proc.returncode == 1
    findings = _result(proc)["findings"]
    assert [(item["start"], item["end"]) for item in findings] == expected_offsets


def test_token_match_requires_nonword_boundaries(tmp_path):
    mapping = _base_map(entries=[{
        "canonical": "feline",
        "forbidden_variants": "cat",
        "match": "token",
    }])
    proc = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "cat scatter cat."}),
    )

    assert proc.returncode == 1
    findings = _result(proc)["findings"]
    assert [(item["start"], item["end"]) for item in findings] == [
        (0, 3), (12, 15)]


def test_literal_match_includes_substrings_without_token_boundaries(tmp_path):
    mapping = _base_map(entries=[{
        "canonical": "feline",
        "forbidden_variants": "cat",
        "match": "literal",
    }])
    proc = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "cat scatter cat."}),
    )

    assert proc.returncode == 1
    findings = _result(proc)["findings"]
    assert [(item["start"], item["end"]) for item in findings] == [
        (0, 3), (5, 8), (12, 15)]


def test_list_valued_canonical_is_preserved_in_the_finding(tmp_path):
    mapping = _base_map(entries=[{
        "canonical": ["preferred term", "accepted term"],
        "forbidden_variants": ["legacy term", "old term"],
        "match": "literal",
    }])
    proc = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "Remove old term."}),
    )

    assert proc.returncode == 1
    assert _result(proc)["findings"][0]["canonical"] == [
        "preferred term", "accepted term"]


@pytest.mark.parametrize(
    "entries",
    [
        [{
            "canonical": "Term",
            "forbidden_variants": "term",
            "match": "literal",
        }],
        [
            {
                "canonical": "alpha",
                "forbidden_variants": "legacy",
                "match": "literal",
            },
            {
                "canonical": "beta",
                "forbidden_variants": "LEGACY",
                "match": "literal",
            },
        ],
    ],
)
def test_case_normalized_map_collisions_are_unknown(tmp_path, entries):
    proc = _run(
        tmp_path,
        _base_map(case_sensitive=False, entries=entries),
        _segments({"kind": "editable", "text": "clean"}),
    )

    assert proc.returncode == 2
    result = _result(proc)
    assert result["status"] == "UNKNOWN"
    assert result["findings"] == []
    assert "collision" in result["error"].lower()


def test_malformed_map_is_unknown(tmp_path):
    map_path = tmp_path / "terms.json"
    segments_path = tmp_path / "segments.json"
    map_path.write_text("{not json", encoding="utf-8")
    _write_json(
        segments_path,
        _segments({"kind": "editable", "text": "clean"}),
    )

    proc = _run_files(map_path, segments_path)

    assert proc.returncode == 2
    assert _result(proc)["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "candidate",
    [
        _segments({"kind": "unknown", "text": "clean"}),
        _segments({"kind": "protected", "text": "legacy term"}),
        {"schema_version": 1, "segments": [], "extra": True},
        {"schema_version": 1},
    ],
)
def test_invalid_or_unobservable_segments_are_unknown(tmp_path, candidate):
    proc = _run(tmp_path, _base_map(), candidate)

    assert proc.returncode == 2
    assert _result(proc)["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "mapping",
    [
        {
            "schema_version": 1,
            "case_sensitive": True,
            "entries": [],
        },
        {
            "schema_version": 1,
            "case_sensitive": True,
            "entries": [{
                "canonical": "preferred",
                "forbidden_variants": "legacy",
                "match": "literal",
                "extra": True,
            }],
        },
        {
            "schema_version": 1,
            "case_sensitive": "yes",
            "entries": [{
                "canonical": "preferred",
                "forbidden_variants": "legacy",
                "match": "literal",
            }],
        },
    ],
)
def test_invalid_map_shapes_are_unknown(tmp_path, mapping):
    proc = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "clean"}),
    )

    assert proc.returncode == 2
    assert _result(proc)["status"] == "UNKNOWN"


def test_repair_requires_revalidation_to_reach_compliant(tmp_path):
    mapping = _base_map()
    first = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "Use legacy term."}),
    )
    repaired = _run(
        tmp_path,
        mapping,
        _segments({"kind": "editable", "text": "Use preferred term."}),
    )

    assert first.returncode == 1
    assert _result(first)["status"] == "NONCOMPLIANT"
    assert repaired.returncode == 0
    assert _result(repaired) == {"findings": [], "status": "COMPLIANT"}


def test_valid_but_wrong_labels_prove_only_label_policy_mapping(tmp_path):
    protected_looking = "<protected>legacy term</protected>"
    editable_looking = "Draft text uses legacy term."
    first = _run(
        tmp_path,
        _base_map(),
        _segments(
            {"kind": "editable", "text": protected_looking},
            {"kind": "protected", "text": editable_looking},
        ),
    )
    swapped = _run(
        tmp_path,
        _base_map(),
        _segments(
            {"kind": "protected", "text": protected_looking},
            {"kind": "editable", "text": editable_looking},
        ),
    )

    assert first.returncode == 1
    assert _result(first)["findings"][0]["segment_index"] == 0
    assert swapped.returncode == 1
    assert _result(swapped)["findings"][0]["segment_index"] == 1
