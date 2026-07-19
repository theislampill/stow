"""Fixture tests for the meta-code layer templates.

Each template under ``skills/stow/templates/`` is a REAL, filled-in worked
example, not a skeleton, so it doubles as a validation fixture. These tests
assert the guarantees a cold reader depends on:

* every template file exists and is non-empty;
* ``task-packet.yaml`` parses as YAML and honours the packet invariants;
* ``event-stream.jsonl`` parses one JSON object per line, every ``type`` drawn
  from the closed event vocabulary, timestamps non-decreasing;
* the Markdown templates that carry a machine-readable block (HANDOFF, STATE,
  AUDIT) embed a YAML instance that carries the fields its schema requires.

No source-project name, path, hash, or URL appears in this file; every fixture
is STOW-native data.
"""

import io
import json
import os
import re

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TEMPLATES = os.path.join(REPO, "skills", "stow", "templates")

MD_TEMPLATES = ("HANDOFF.md", "PLAN.md", "AUDIT.md", "RUNBOOK.md", "STATE.md")
DATA_TEMPLATES = ("task-packet.yaml", "event-stream.jsonl")
ALL_TEMPLATES = MD_TEMPLATES + DATA_TEMPLATES

# The closed event-type core vocabulary, single-sourced from the shipped event
# schema (the anyOf's enum branch; the x- escape branch admits extensions).
def _event_types_from_schema():
    import json as _json
    path = os.path.join(REPO, "skills", "stow", "schemas", "event.schema.json")
    with open(path, encoding="utf-8") as fh:
        schema = _json.load(fh)
    for branch in schema["properties"]["type"]["anyOf"]:
        if "enum" in branch:
            return set(branch["enum"])
    raise AssertionError("event schema carries no enum branch for 'type'")


EVENT_TYPES = _event_types_from_schema()

_FENCE_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _read(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        return fh.read()


def _load_yaml(text):
    return YAML(typ="safe").load(io.StringIO(text))


def _first_yaml_block(name):
    """Return the parsed first ```yaml fenced block of a Markdown template."""
    match = _FENCE_RE.search(_read(name))
    assert match, "%s carries no embedded ```yaml instance block" % name
    return _load_yaml(match.group(1))


# --------------------------------------------------------------------------- #
# Existence + non-empty (the minimum bar for every template)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", ALL_TEMPLATES)
def test_template_exists_and_non_empty(name):
    path = os.path.join(TEMPLATES, name)
    assert os.path.isfile(path), "missing template: %s" % name
    assert os.path.getsize(path) > 0, "empty template: %s" % name
    assert _read(name).strip() != ""


# --------------------------------------------------------------------------- #
# task-packet.yaml — parses + packet invariants
# --------------------------------------------------------------------------- #

def test_task_packet_parses_as_yaml():
    packet = _load_yaml(_read("task-packet.yaml"))
    assert isinstance(packet, dict)


def test_task_packet_has_required_fields():
    packet = _load_yaml(_read("task-packet.yaml"))
    required = {"packet_id", "goal", "inputs", "permissions", "expected_output",
               "acceptance", "done_definition", "status", "evidence"}
    assert required <= set(packet), \
        "task-packet missing: %s" % (required - set(packet))


def test_task_packet_read_only_forbids_write_scope():
    perms = _load_yaml(_read("task-packet.yaml"))["permissions"]
    if perms.get("read_only") is True:
        assert perms.get("write_scope") == [], \
            "read_only packet must carry an empty write_scope"


def test_task_packet_done_status_covers_every_acceptance():
    """Schema-legal coverage matching: each evidence item names the acceptance
    id it satisfies via its ``for`` field (the schema forbids restating the
    predicate on evidence items)."""
    packet = _load_yaml(_read("task-packet.yaml"))
    if packet.get("status") == "done":
        assert packet["evidence"], "status==done requires non-empty evidence"
        acceptance_ids = {a["id"] for a in packet["acceptance"]}
        covered = {e["for"] for e in packet["evidence"]}
        assert acceptance_ids <= covered, \
            "acceptance ids without evidence: %s" % (acceptance_ids - covered)


# --------------------------------------------------------------------------- #
# event-stream.jsonl — one JSON object per line, closed type enum, monotonic ts
# --------------------------------------------------------------------------- #

def _event_lines():
    return [ln for ln in _read("event-stream.jsonl").splitlines() if ln.strip()]


def test_event_stream_each_line_is_one_json_object():
    for lineno, line in enumerate(_event_lines(), start=1):
        obj = json.loads(line)  # raises on any malformed line
        assert isinstance(obj, dict), "line %d is not a JSON object" % lineno


def test_event_stream_types_are_in_the_closed_enum():
    for lineno, line in enumerate(_event_lines(), start=1):
        etype = json.loads(line).get("type")
        assert etype in EVENT_TYPES, \
            "line %d has out-of-vocabulary type %r" % (lineno, etype)


def test_event_stream_required_keys_present():
    for lineno, line in enumerate(_event_lines(), start=1):
        obj = json.loads(line)
        for key in ("ts", "actor", "type"):
            assert key in obj, "line %d missing %r" % (lineno, key)


def test_event_stream_timestamps_non_decreasing():
    stamps = [json.loads(line)["ts"] for line in _event_lines()]
    assert stamps == sorted(stamps), "event timestamps are not monotonic"


def test_event_stream_is_not_a_wrapping_array():
    text = _read("event-stream.jsonl").lstrip()
    assert not text.startswith("["), "JSONL must not be a wrapping array"


# --------------------------------------------------------------------------- #
# Markdown templates carry a schema-shaped instance block
# --------------------------------------------------------------------------- #

def test_handoff_block_has_required_fields():
    block = _first_yaml_block("HANDOFF.md")
    required = {"handoff_id", "from_actor", "to_actor", "created_ts", "goal",
               "plan_ref", "done", "not_done", "constraints", "next_action",
               "artifacts", "open_risks", "acceptance_for_next"}
    assert required <= set(block), "handoff missing: %s" % (required - set(block))


def test_handoff_next_action_is_single_non_empty_imperative():
    block = _first_yaml_block("HANDOFF.md")
    assert isinstance(block["next_action"], str)
    assert block["next_action"].strip() != ""


def test_state_block_has_required_fields():
    block = _first_yaml_block("STATE.md")
    required = {"run_id", "updated_ts", "current", "gates", "decisions",
               "andons", "history_append_only"}
    assert required <= set(block), "state missing: %s" % (required - set(block))


def test_state_history_append_only_is_true():
    assert _first_yaml_block("STATE.md")["history_append_only"] is True


def test_state_supersession_links_resolve():
    block = _first_yaml_block("STATE.md")
    ids = {d["id"] for d in block["decisions"]}
    for d in block["decisions"]:
        if d.get("superseded_by"):
            assert d["superseded_by"] in ids, "dangling superseded_by"
        for ref in d.get("supersedes", []) or []:
            assert ref in ids, "dangling supersedes"


def test_audit_records_have_required_fields():
    records = _first_yaml_block("AUDIT.md")["records"]
    assert records, "AUDIT.md carries no records"
    required = {"record_id", "kind", "statement", "locators", "severity",
               "disposition", "verified"}
    for rec in records:
        assert required <= set(rec), \
            "record %s missing: %s" % (rec.get("record_id"), required - set(rec))


def test_audit_verified_finding_has_failure_scenario():
    for rec in _first_yaml_block("AUDIT.md")["records"]:
        if rec["kind"] == "finding" and rec.get("verified") is True:
            assert rec.get("failure_scenario", "").strip() != "", \
                "verified finding %s needs a failure_scenario" % rec["record_id"]


# --------------------------------------------------------------------------- #
# Every template validates against its schema through the REAL runtime CLI.
# This is the drift gate the layer originally lacked: a template block whose
# shape diverges from its contract fails here, not in a reader's hands.
# --------------------------------------------------------------------------- #

import subprocess
import sys

RUNTIME_VALIDATE = os.path.join(
    REPO, "skills", "stow", "runtime", "validate.py")

TEMPLATE_CONTRACTS = [
    ("handoff", "HANDOFF.md"),
    ("state", "STATE.md"),
    ("evidence-record", "AUDIT.md"),
    ("plan", "PLAN.md"),
    ("runbook", "RUNBOOK.md"),
    ("task-packet", "task-packet.yaml"),
    ("event", "event-stream.jsonl"),
]


def test_every_template_has_a_contract_row():
    assert {name for _sid, name in TEMPLATE_CONTRACTS} == set(ALL_TEMPLATES)


@pytest.mark.parametrize("schema_id,name", TEMPLATE_CONTRACTS,
                         ids=[n for _s, n in TEMPLATE_CONTRACTS])
def test_template_validates_against_its_schema(schema_id, name):
    proc = subprocess.run(
        [sys.executable, RUNTIME_VALIDATE, "--schema", schema_id,
         os.path.join(TEMPLATES, name)],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, (
        "%s does not validate against %s:\n%s%s"
        % (name, schema_id, proc.stdout, proc.stderr))
    assert "VALID" in proc.stdout
