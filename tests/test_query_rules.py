"""Smoke gate for the optional rule-lookup helper.

runtime/query_rules.py is an optional, stdlib-only acceleration; it is not
shipped and no kernel path reads it. These checks confirm it resolves a known
id with a non-empty corpus section, exits 2 for an unknown id, and authors no
em dash of its own (the known id used here has an em-dash-free corpus section,
so a clean run proves the helper adds none).
"""

import importlib.util
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HELPER = os.path.join(REPO, "skills", "stow", "runtime", "query_rules.py")

# A rule whose corpus section carries no verbatim em dash, so the whole output
# is em-dash-free when the helper adds none.
KNOWN_ID = "STOW-ACT-001"


def _load():
    spec = importlib.util.spec_from_file_location("query_rules_under_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


query_rules = _load()


def _run(arg):
    """Run main([arg]); return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = query_rules.main([arg])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def test_known_id_resolves_with_non_empty_section():
    code, out, _err = _run(KNOWN_ID)
    assert code == 0, "known id did not resolve (exit %d)" % code
    assert KNOWN_ID in out
    assert "corpus section" in out
    # The printed section body is non-empty and is not the not-found sentinel.
    body = out.split("corpus section", 1)[1]
    assert "(section not found)" not in body
    assert len(body.strip().splitlines()) > 1


def test_unknown_id_exits_2():
    code, _out, err = _run("STOW-XXX-999")
    assert code == 2, "unknown id should exit 2, got %d" % code
    assert "unknown rule id" in err


def test_output_has_no_em_dash():
    _code, out, _err = _run(KNOWN_ID)
    assert "—" not in out, "query_rules output contains an em dash"


def test_helper_source_has_no_em_dash():
    with open(HELPER, encoding="utf-8") as handle:
        assert "—" not in handle.read(), "query_rules.py source contains an em dash"


def test_missing_argument_exits_2():
    code = query_rules.main([])
    assert code == 2
