"""Tests for the meta-code coordination schemas and the ``validate.py --schema``
runner.

For each of the five schemas this asserts: the schema document itself loads and
is a valid draft 2020-12 schema; the shipped VALID fixture passes; a mutated
instance fails schema validation; and the three cross-field post-checks (sha256
recompute, status-done-needs-evidence, non-dangling supersession) each fire.

No literal 64-hex hash appears in this file: the sha256 cases are computed with
``hashlib`` at run time, so the file stays clean under the provenance leak gate.
No source-project name or derivation trail appears here; every instance is
generic STOW-native data.
"""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import jsonschema
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")
VALIDATE_PATH = os.path.join(RUNTIME, "validate.py")
SCHEMA_DIR = os.path.join(REPO, "skills", "stow", "schemas")
META_FIX = os.path.join(HERE, "fixtures", "meta")

# The five interchange meta-contracts (the registry catalog) plus the three
# validator schemas (event, plan, runbook) that do NOT join the catalog:
# meta_contract_total stays 5.
SCHEMA_IDS = [
    "output-contract",
    "handoff",
    "task-packet",
    "evidence-record",
    "state",
    "event",
    "plan",
    "runbook",
]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = _load("validate", VALIDATE_PATH)


def schema_doc(schema_id):
    with open(os.path.join(SCHEMA_DIR, schema_id + ".schema.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def fixture_path(schema_id):
    return os.path.join(META_FIX, schema_id + ".json")


def fixture_text(schema_id):
    with open(fixture_path(schema_id), encoding="utf-8") as fh:
        return fh.read()


def fixture_obj(schema_id):
    return json.loads(fixture_text(schema_id))


def run_obj(schema_id, obj):
    """Validate an in-memory instance against a named schema."""
    return validate.validate_schema(schema_id, json.dumps(obj), "inmem.json")


# --------------------------------------------------------------------------- #
# Each schema loads and is a valid draft 2020-12 document
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_schema_document_loads(schema_id):
    assert os.path.isfile(validate.schema_path(schema_id))


@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_schema_is_valid_draft_2020_12(schema_id):
    schema = schema_doc(schema_id)
    assert schema["$schema"].endswith("2020-12/schema")
    # Raises SchemaError if the document is not a legal draft 2020-12 schema.
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_schema_has_comment_required_and_no_additional_properties(schema_id):
    schema = schema_doc(schema_id)
    assert schema.get("$comment", "").strip() != ""
    assert schema["additionalProperties"] is False
    assert isinstance(schema["required"], list) and schema["required"]


# --------------------------------------------------------------------------- #
# Valid fixtures pass
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_valid_fixture_passes(schema_id):
    result = validate.validate_schema(schema_id, fixture_text(schema_id),
                                      fixture_path(schema_id))
    assert result.ok is True, result.errors


# --------------------------------------------------------------------------- #
# Invalid instances fail schema validation (one mutation per schema)
# --------------------------------------------------------------------------- #

# Each mutation drops a required field or injects an unknown one.
_SCHEMA_BREAKERS = {
    "output-contract": lambda o: o.pop("artifact_type"),
    "handoff": lambda o: o.pop("next_action"),
    "task-packet": lambda o: o.pop("acceptance"),
    "evidence-record": lambda o: o.pop("kind"),
    "state": lambda o: o.__setitem__("history_append_only", False),
    "event": lambda o: o.pop("type"),
    "plan": lambda o: o.pop("tasks"),
    "runbook": lambda o: o.pop("success_check"),
}


@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_mutated_instance_fails_schema(schema_id):
    obj = fixture_obj(schema_id)
    _SCHEMA_BREAKERS[schema_id](obj)
    result = run_obj(schema_id, obj)
    assert result.ok is False
    assert any("schema" in e for e in result.errors), result.errors


@pytest.mark.parametrize("schema_id", SCHEMA_IDS)
def test_additional_property_rejected(schema_id):
    obj = fixture_obj(schema_id)
    obj["surprise_field"] = "not allowed"
    assert run_obj(schema_id, obj).ok is False


# --------------------------------------------------------------------------- #
# Cross-field post-check 1: a declared sha256 must match a recomputed hash
# --------------------------------------------------------------------------- #

def _envelope_with_payload(payload, digest):
    return {
        "stow_version": "0.2",
        "artifact_type": "output-contract",
        "content_type": "text/markdown",
        "schema_id": None,
        "schema_version": 1,
        "region_map": [],
        "integrity": {"algo": "sha256", "value": digest},
        "payload": payload,
    }


def test_sha256_match_passes():
    payload = "coordination payload body"
    good = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    result = run_obj("output-contract", _envelope_with_payload(payload, good))
    assert result.ok is True, result.errors


def test_sha256_mismatch_fires():
    payload = "coordination payload body"
    wrong = hashlib.sha256(b"a different body").hexdigest()
    result = run_obj("output-contract", _envelope_with_payload(payload, wrong))
    assert result.ok is False
    assert any("integrity mismatch" in e for e in result.errors), result.errors


def test_sha256_check_unit():
    payload = "x"
    wrong = hashlib.sha256(b"y").hexdigest()
    inst = _envelope_with_payload(payload, wrong)
    assert validate.check_sha256(inst)  # non-empty error list
    inst["integrity"]["value"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert validate.check_sha256(inst) == []


# --------------------------------------------------------------------------- #
# Cross-field post-check 2: status 'done' must carry an evidence pointer
# --------------------------------------------------------------------------- #

def test_task_packet_done_without_evidence_fires():
    obj = fixture_obj("task-packet")
    obj.pop("evidence")  # schema-legal (optional) but post-check must fire
    result = run_obj("task-packet", obj)
    assert result.ok is False
    assert any("evidence pointer" in e for e in result.errors), result.errors


def test_state_gate_done_without_evidence_fires():
    obj = fixture_obj("state")
    for gate in obj["gates"]:
        if gate["status"] == "done":
            gate.pop("evidence_ref", None)
    result = run_obj("state", obj)
    assert result.ok is False
    assert any("evidence pointer" in e for e in result.errors), result.errors


def test_status_evidence_check_unit():
    assert validate.check_status_evidence({"status": "done"})
    assert validate.check_status_evidence(
        {"status": "done", "evidence_ref": "path/to/proof"}) == []
    assert validate.check_status_evidence({"status": "active"}) == []


# --------------------------------------------------------------------------- #
# Cross-field post-check 3: a decision supersession must not dangle
# --------------------------------------------------------------------------- #

def test_supersession_dangle_fires():
    obj = fixture_obj("state")
    for decision in obj["decisions"]:
        if decision.get("superseded_by"):
            decision["superseded_by"] = "OD-does-not-exist"
    result = run_obj("state", obj)
    assert result.ok is False
    assert any("dangling supersession" in e for e in result.errors), result.errors


def test_supersession_check_unit():
    dangling = {"decisions": [{"id": "A", "supersedes": ["Z"]}]}
    assert validate.check_supersession(dangling)
    resolved = {"decisions": [
        {"id": "A", "supersedes": ["B"]},
        {"id": "B", "superseded_by": "A"},
    ]}
    assert validate.check_supersession(resolved) == []


# --------------------------------------------------------------------------- #
# Runner robustness + CLI
# --------------------------------------------------------------------------- #

def test_unknown_schema_id_reports_available():
    result = validate.validate_schema("nope", "{}", "x.json")
    assert result.ok is False
    assert any("unknown schema id" in e for e in result.errors)


def test_malformed_schema_id_rejected():
    # Path traversal / separators must never resolve to a file.
    result = validate.validate_schema("../secrets", "{}", "x.json")
    assert result.ok is False
    assert any("malformed schema id" in e for e in result.errors)


def _run_cli(schema_id, path):
    return subprocess.run(
        [sys.executable, VALIDATE_PATH, "--schema", schema_id, path],
        capture_output=True, text=True)


def test_cli_valid_fixture_exit_zero():
    assert _run_cli("state", fixture_path("state")).returncode == 0


def test_cli_invalid_instance_exit_nonzero(tmp_path):
    obj = fixture_obj("handoff")
    obj.pop("next_action")
    bad = tmp_path / "bad-handoff.json"
    bad.write_text(json.dumps(obj), encoding="utf-8")
    assert _run_cli("handoff", str(bad)).returncode != 0


def test_cli_mutually_exclusive_modes():
    # --format and --schema together is a usage error (argparse exit 2).
    proc = subprocess.run(
        [sys.executable, VALIDATE_PATH, "--format", "json", "--schema", "state",
         fixture_path("state")],
        capture_output=True, text=True)
    assert proc.returncode == 2


def test_format_mode_still_works():
    # The pre-existing --format mode is unchanged by the schema addition.
    proc = subprocess.run(
        [sys.executable, VALIDATE_PATH, "--format", "json", fixture_path("handoff")],
        capture_output=True, text=True)
    assert proc.returncode == 0


# --------------------------------------------------------------------------- #
# Import-closure guard: stdlib + ruamel + jsonschema only
# --------------------------------------------------------------------------- #

def test_validate_import_closed():
    import ast
    with open(VALIDATE_PATH, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    allowed_roots = {"jsonschema", "ruamel"}
    stdlib = {"argparse", "hashlib", "io", "json", "math", "os", "sys"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_roots or root in stdlib, root
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root in allowed_roots or root in stdlib, root
