"""Gates for the meta-code layer's reference pages.

The meta-code layer adds seven references under ``skills/stow/references/`` that
describe the coordination artifacts STOW governs *between* actors (handoffs,
plans, audits, runbooks, state records, task packets, event streams, and the
cross-harness envelope). ``meta-code.md`` is the hub; the other six each cover one
artifact class.

This module asserts, for each of the seven pages:

  1. the file exists;
  2. it cites the ``schemas/<id>.schema.json`` path that governs its class;
  3. it cites the ``templates/<name>`` path that instantiates its class;
  4. the hub (``meta-code.md``) names all six siblings, all five schemas, and all
     seven templates;
  5. it passes the source-name gate (full mode only — skipped when the private
     pattern file is absent, exactly like ``test_provenance_leak.py``).

The module is itself source-name-free, so the whole repository stays clean when
the anti-leak gate scans it.
"""

import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REFS_DIR = os.path.join(REPO, "skills", "stow", "references")
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))

# --------------------------------------------------------------------------- #
# The seven meta-code references, each mapped to the schema id and template
# name it must cite. (reference file -> (schema id, template file name))
# --------------------------------------------------------------------------- #

META_REFS = {
    "meta-code.md": ("task-packet", "task-packet.yaml"),
    "agent-handoffs.md": ("handoff", "HANDOFF.md"),
    "implementation-plans.md": ("task-packet", "PLAN.md"),
    "audit-and-evidence.md": ("evidence-record", "AUDIT.md"),
    "runbooks.md": ("output-contract", "RUNBOOK.md"),
    "continuity-and-state.md": ("state", "STATE.md"),
    "cross-harness-interchange.md": ("output-contract", "event-stream.jsonl"),
}

# What the hub must enumerate.
HUB = "meta-code.md"
ALL_SIBLINGS = [name for name in META_REFS if name != HUB]
ALL_SCHEMAS = ("output-contract", "handoff", "task-packet", "evidence-record", "state")
ALL_TEMPLATES = ("HANDOFF.md", "PLAN.md", "AUDIT.md", "RUNBOOK.md", "STATE.md",
                 "task-packet.yaml", "event-stream.jsonl")

# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #


def _read(name):
    with open(os.path.join(REFS_DIR, name), encoding="utf-8") as handle:
        return handle.read()


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_provenance_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_checker()
_data = _mod.load_patterns(PATTERNS_PATH)


# --------------------------------------------------------------------------- #
# Gate 1 -- every meta-code reference exists
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", sorted(META_REFS))
def test_meta_reference_exists(name):
    assert os.path.isfile(os.path.join(REFS_DIR, name)), \
        "meta-code reference %s does not exist" % name


# --------------------------------------------------------------------------- #
# Gate 2 -- each reference cites its schema path and its template path
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", sorted(META_REFS))
def test_meta_reference_cites_schema_and_template(name):
    schema_id, template = META_REFS[name]
    text = _read(name)
    schema_path = "schemas/%s.schema.json" % schema_id
    template_path = "templates/%s" % template
    assert schema_path in text, \
        "%s does not cite its schema path %s" % (name, schema_path)
    assert template_path in text, \
        "%s does not cite its template path %s" % (name, template_path)


# --------------------------------------------------------------------------- #
# Gate 3 -- the hub names every sibling, schema, and template
# --------------------------------------------------------------------------- #

def test_hub_names_siblings_schemas_and_templates():
    text = _read(HUB)
    for sibling in ALL_SIBLINGS:
        assert "references/%s" % sibling in text, \
            "hub %s does not name sibling references/%s" % (HUB, sibling)
    for schema_id in ALL_SCHEMAS:
        assert "schemas/%s.schema.json" % schema_id in text, \
            "hub %s does not name schema %s" % (HUB, schema_id)
    for template in ALL_TEMPLATES:
        assert "templates/%s" % template in text, \
            "hub %s does not name template %s" % (HUB, template)


# --------------------------------------------------------------------------- #
# Gate 4 -- each reference points at the schema-runner validation command
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", sorted(META_REFS))
def test_meta_reference_names_the_validator(name):
    text = _read(name)
    assert "runtime/validate.py --schema" in text, \
        "%s does not name the schema-runner validation command" % name


# --------------------------------------------------------------------------- #
# Gate 5 -- every reference passes the source-name gate (full mode only)
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    _data is None, reason="private pattern file not present (weak/CI environment)")
@pytest.mark.parametrize("name", sorted(META_REFS))
def test_meta_reference_passes_source_name_gate(name):
    patterns = _mod.Patterns(_data)
    hash_specs = _mod.load_hash_positions(
        os.path.join(REPO, "tools", "hash-positions.txt"))
    rel = "skills/stow/references/%s" % name
    findings = _mod.scan_file(rel, _read(name), patterns, True, hash_specs)
    assert findings == [], \
        "%s tripped the anti-leak gate: %r" % (name, findings)


# --------------------------------------------------------------------------- #
# Gate 6 -- this test module itself passes the source-name gate (full mode only)
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    _data is None, reason="private pattern file not present (weak/CI environment)")
def test_this_module_passes_source_name_gate():
    patterns = _mod.Patterns(_data)
    hash_specs = _mod.load_hash_positions(
        os.path.join(REPO, "tools", "hash-positions.txt"))
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        source = handle.read()
    findings = _mod.scan_file("tests/test_meta_references.py", source,
                              patterns, True, hash_specs)
    assert findings == [], "test module tripped the anti-leak gate: %r" % findings
