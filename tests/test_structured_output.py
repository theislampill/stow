"""P3 tests for the deterministic structured-output validators, the prose
linter, and the context measurer.

Design: RED-first. The trap fixtures under ``tests/fixtures/{json,jsonl,yaml}``
are things a NAIVE parser accepts (or, for the int/float YAML case, a naive
parser WRONGLY rejects) but that the P3 validators must classify correctly. Each
trap test demonstrates the naive behaviour and then the correct validator
behaviour side by side.

No source-project name appears in this file; every fixture is generic data.
"""

import ast
import importlib.util
import io
import json
import math
import os
import subprocess
import sys

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")
VALIDATE_PATH = os.path.join(RUNTIME, "validate.py")
LINT_PATH = os.path.join(RUNTIME, "lint_prose.py")
MEASURE_PATH = os.path.join(REPO, "tools", "measure_context.py")
FIX = os.path.join(HERE, "fixtures")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = _load("validate", VALIDATE_PATH)
lint_prose = _load("lint_prose", LINT_PATH)
measure_context = _load("measure_context", MEASURE_PATH)


def read(*parts):
    with open(os.path.join(FIX, *parts), encoding="utf-8") as fh:
        return fh.read()


def fixture(*parts):
    return os.path.join(FIX, *parts)


# --------------------------------------------------------------------------- #
# JSON -- RED traps (naive accepts, validator rejects)
# --------------------------------------------------------------------------- #

def test_json_nan_naive_accepts_validator_rejects():
    text = read("json", "nan.json")
    # NAIVE: stdlib json accepts the NaN literal as a float.
    assert math.isnan(json.loads(text)["value"])
    # VALIDATOR: rejects non-finite constants.
    assert validate.validate_json(text).ok is False


def test_json_duplicate_key_naive_accepts_validator_rejects():
    text = read("json", "dup_key.json")
    # NAIVE: stdlib json silently keeps the last value (last-wins).
    assert json.loads(text) == {"a": 2}
    # VALIDATOR: rejects the duplicate key via object_pairs_hook.
    assert validate.validate_json(text).ok is False


def test_json_trailing_comma_naive_accepts_validator_rejects():
    text = read("json", "trailing_comma.json")
    # NAIVE: a permissive literal parser accepts the trailing comma.
    assert ast.literal_eval(text) == {"a": 1, "b": 2}
    # VALIDATOR: strict JSON rejects it.
    assert validate.validate_json(text).ok is False


def test_json_valid_passes():
    assert validate.validate_json(read("json", "valid.json")).ok is True


def test_json_leading_bom_rejected():
    text = read("json", "bom.json")
    assert text.startswith("﻿")  # the BOM survived decoding
    assert validate.validate_json(text).ok is False


def test_json_markdown_fence_rejected():
    assert validate.validate_json(read("json", "fenced.json")).ok is False


# --------------------------------------------------------------------------- #
# JSONL
# --------------------------------------------------------------------------- #

def test_jsonl_valid_multirecord_passes():
    result = validate.validate_jsonl(read("jsonl", "valid.jsonl"))
    assert result.ok is True
    assert result.data["line_errors"] == []


def test_jsonl_bad_line_reported_by_number():
    result = validate.validate_jsonl(read("jsonl", "bad_line.jsonl"))
    assert result.ok is False
    reported = [lineno for lineno, _msg in result.data["line_errors"]]
    assert reported == [3]  # only line 3 is malformed


def test_jsonl_array_wrapped_naive_accepts_validator_rejects():
    text = read("jsonl", "array_wrapped.jsonl")
    # NAIVE: the whole file parses as one valid JSON array.
    assert json.loads(text) == [{"event": "start"}, {"event": "stop"}]
    # VALIDATOR: JSONL has no wrapping array; the bare '[' on line 1 fails.
    result = validate.validate_jsonl(text)
    assert result.ok is False
    assert result.data["line_errors"][0][0] == 1


# --------------------------------------------------------------------------- #
# YAML -- E5 duplicate-key discrimination
# --------------------------------------------------------------------------- #

def test_yaml_int_vs_float_distinct_valid_both_preserved():
    text = read("yaml", "int_vs_float.yaml")
    result = validate.validate_yaml(text)
    assert result.ok is True
    # BOTH keys are preserved as distinct source tokens.
    assert result.data["root_key_tokens"] == ["1", "1.0"]


def test_yaml_hex_vs_dec_distinct_valid():
    text = read("yaml", "hex_vs_dec.yaml")
    result = validate.validate_yaml(text)
    assert result.ok is True
    assert result.data["root_key_tokens"] == ["0x10", "16"]


def test_yaml_same_token_str_duplicate_invalid():
    assert validate.validate_yaml(read("yaml", "dup_same_token.yaml")).ok is False


def test_yaml_same_token_int_duplicate_invalid():
    assert validate.validate_yaml(read("yaml", "dup_same_int.yaml")).ok is False


def test_naive_ruamel_wrongly_flags_int_vs_float_but_validator_accepts():
    text = read("yaml", "int_vs_float.yaml")
    # NAIVE: ruamel's built-in (resolved-value) duplicate check WRONGLY rejects
    # 1 vs 1.0 because 1 == 1.0 in Python.
    naive = YAML(typ="safe")  # allow_duplicate_keys defaults to False
    with pytest.raises(Exception):
        naive.load(io.StringIO(text))
    # VALIDATOR: token-level comparison keeps them distinct.
    assert validate.validate_yaml(text).ok is True


def test_naive_permissive_yaml_accepts_same_token_but_validator_rejects():
    text = read("yaml", "dup_same_token.yaml")
    # NAIVE: a permissive load (dupes allowed) silently collapses the two
    # entries into one key -- data loss with no signal to the caller.
    permissive = YAML(typ="safe")
    permissive.allow_duplicate_keys = True
    loaded = permissive.load(io.StringIO(text))
    assert loaded == {"name": "first"}  # the second entry vanished silently
    # VALIDATOR: the repeated source token is caught as a genuine duplicate.
    assert validate.validate_yaml(text).ok is False


def test_yaml_alias_rejected():
    assert validate.validate_yaml(read("yaml", "alias.yaml")).ok is False


def test_yaml_custom_tag_rejected():
    assert validate.validate_yaml(read("yaml", "custom_tag.yaml")).ok is False


def test_yaml_valid_passes():
    assert validate.validate_yaml(read("yaml", "valid.yaml")).ok is True


# --------------------------------------------------------------------------- #
# validate.py CLI exit codes
# --------------------------------------------------------------------------- #

def _run_validate(fmt, path):
    return subprocess.run([sys.executable, VALIDATE_PATH, "--format", fmt, path],
                          capture_output=True, text=True)


def test_cli_validate_valid_json_exit_zero():
    assert _run_validate("json", fixture("json", "valid.json")).returncode == 0


def test_cli_validate_invalid_json_nonzero():
    assert _run_validate("json", fixture("json", "nan.json")).returncode != 0


def test_cli_validate_invalid_yaml_nonzero():
    assert _run_validate("yaml", fixture("yaml", "dup_same_token.yaml")).returncode != 0


# --------------------------------------------------------------------------- #
# measure_context
# --------------------------------------------------------------------------- #

def test_measure_over_ceiling_exits_nonzero():
    assert measure_context.main([fixture("context", "over_ceiling.md")]) != 0


def test_measure_in_band_exits_zero():
    assert measure_context.main([fixture("context", "in_band.md")]) == 0


def test_measure_in_band_is_within_target_band():
    tokens, _chars = measure_context.measure_file(fixture("context", "in_band.md"))
    assert measure_context.band_status(tokens) == "WITHIN BAND"


def test_measure_over_ceiling_token_count_exceeds_hard_ceiling():
    tokens, _chars = measure_context.measure_file(fixture("context", "over_ceiling.md"))
    assert tokens > measure_context.HARD_CEILING


def test_measure_bundles_mode_is_soft_and_never_fails():
    # The manifest names a missing member on purpose; bundle mode still exits 0.
    assert measure_context.main(["--bundles", fixture("context", "bundles.yaml")]) == 0


# --------------------------------------------------------------------------- #
# lint_prose -- masking + report-only contract
# --------------------------------------------------------------------------- #

def test_lint_em_dash_inside_fence_is_masked_and_not_reported():
    advisories = lint_prose.lint(read("prose", "em_dash_in_fence.md"))
    assert not any(a.rule == "em-dash" for a in advisories)


def test_lint_em_dash_in_prose_is_reported():
    advisories = lint_prose.lint(read("prose", "em_dash_in_prose.md"))
    assert any(a.rule == "em-dash" for a in advisories)


def test_lint_masking_blanks_the_fenced_dash_but_keeps_prose_dash():
    fenced = lint_prose.mask_protected(read("prose", "em_dash_in_fence.md"))
    prose = lint_prose.mask_protected(read("prose", "em_dash_in_prose.md"))
    assert "—" not in fenced   # em-dash inside the code fence is gone
    assert "—" in prose        # em-dash in real prose survives masking


def test_lint_exit_code_is_always_zero():
    for name in ("em_dash_in_fence.md", "em_dash_in_prose.md"):
        assert lint_prose.main([fixture("prose", name)]) == 0
