"""P5 GREEN behavioural / structured-output detector-contract tests.

For each of the 27 deterministic cases in ``tests/evals/baseline.yaml`` (17
hard-gating + 10 semi-deterministic; the 6 judge cases are skipped), a paired
fixture in ``tests/evals/behavioural.yaml`` is run through the case's detector
(from ``tests/eval_runner.py``):

    no_stow -> red_assertion FALSE  (the P1 RED baseline: failure present)
    stow    -> red_assertion TRUE   (the P5 GREEN target: property satisfied)

That paired assertion is the RED->GREEN delta, asserted in one place.

For the structured-output / conflict-attack cases whose governing behaviour is a
protected region (byte-stable literals, wire keys, a verbatim quotation, an
approved technical term, or an unchanged brand title), an extra check asserts the
protected span is byte-identical to the runner's own source constant in the STOW
fixture.

SCOPE (honest): these are fixture / detector-contract tests. There is NO
model-invocation harness in this project. Passing here proves the detector
contract holds for a hand-authored STOW-compliant answer; it does not prove live
model behaviour. No source-project name appears in this file (it is scanned by
the anti-leak gate like any other authored surface).
"""

import importlib.util
import json
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "evals", "baseline.yaml")
BEHAVIOURAL = os.path.join(HERE, "evals", "behavioural.yaml")


def _load_runner():
    path = os.path.join(HERE, "eval_runner.py")
    spec = importlib.util.spec_from_file_location("stow_eval_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ev = _load_runner()
CASES = ev.load_cases(BASELINE)
BY_ID = {c["id"]: c for c in CASES}

# The 27 deterministic (gating) cases, derived from the catalog by elimination
# of the judge kind -- no hardcoded id list, so it tracks the catalog.
DETERMINISTIC = [c["id"] for c in CASES if c["detector_kind"] != "judge"]
JUDGE = [c["id"] for c in CASES if c["detector_kind"] == "judge"]


def _load_fixtures():
    from ruamel.yaml import YAML
    with open(BEHAVIOURAL, encoding="utf-8") as fh:
        data = YAML(typ="safe").load(fh)
    return data["fixtures"]


FIXTURES = _load_fixtures()


# --------------------------------------------------------------------------- #
# Protected-region byte-identity map (SO / CA cases that require it).
#
# Each entry names the source constant in eval_runner.py whose bytes must survive
# verbatim in the STOW fixture. Keeping the reference to the runner's own constant
# (rather than a re-typed literal) makes "byte-identical" mean identical to the
# thing the detector protects.
# --------------------------------------------------------------------------- #

def _protected_specs():
    return {
        "SO-06": [ev.SO06_CMD],
        "SO-07": list(ev.SO07_LITERALS),
        "CA-02": list(ev.WIRE_KEYS),
        "CA-03": [ev.QUOTES["CA-03"]],
        "CA-04": ["dummy load"],  # `kill` handled separately as a word-boundary term
        "CA-10": [ev.BRAND],
    }


PROTECTED = _protected_specs()


# --------------------------------------------------------------------------- #
# Coverage / shape
# --------------------------------------------------------------------------- #

def test_deterministic_set_is_27():
    assert len(DETERMINISTIC) == 27
    assert len(JUDGE) == 6


def test_fixtures_cover_exactly_the_deterministic_set():
    assert set(FIXTURES) == set(DETERMINISTIC)


def test_no_judge_case_has_a_fixture():
    assert set(FIXTURES).isdisjoint(set(JUDGE))


def test_every_fixture_has_both_sides():
    for cid, pair in FIXTURES.items():
        assert "stow" in pair and pair["stow"].strip(), "%s missing stow" % cid
        assert "no_stow" in pair and pair["no_stow"].strip(), \
            "%s missing no_stow" % cid


# --------------------------------------------------------------------------- #
# RED -> GREEN delta: the core P5 assertion.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cid", sorted(DETERMINISTIC))
def test_red_baseline_is_false(cid):
    """no-STOW fixture: the red_assertion is FALSE (failure present)."""
    case = BY_ID[cid]
    answer = FIXTURES[cid]["no_stow"]
    result = ev.run_detector(case["detector"], answer, case)
    assert result is False, \
        "%s expected RED (False) on no_stow but got %r" % (cid, result)


@pytest.mark.parametrize("cid", sorted(DETERMINISTIC))
def test_green_target_is_true(cid):
    """STOW fixture: the red_assertion is now TRUE (property satisfied)."""
    case = BY_ID[cid]
    answer = FIXTURES[cid]["stow"]
    result = ev.run_detector(case["detector"], answer, case)
    assert result is True, \
        "%s expected GREEN (True) on stow but got %r" % (cid, result)


@pytest.mark.parametrize("cid", sorted(DETERMINISTIC))
def test_red_to_green_delta(cid):
    """The pair flips the same detector from False (no_stow) to True (stow)."""
    case = BY_ID[cid]
    red = ev.run_detector(case["detector"], FIXTURES[cid]["no_stow"], case)
    green = ev.run_detector(case["detector"], FIXTURES[cid]["stow"], case)
    assert (red, green) == (False, True), \
        "%s expected (False, True) delta but got %r" % (cid, (red, green))


# --------------------------------------------------------------------------- #
# Protected-region byte-identity (SO / CA cases that require it).
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cid", sorted(PROTECTED))
def test_protected_region_byte_identical(cid):
    stow = FIXTURES[cid]["stow"]
    for literal in PROTECTED[cid]:
        assert literal in stow, \
            "%s: protected literal not byte-identical in stow fixture: %r" \
            % (cid, literal)


def test_ca04_kill_term_is_a_preserved_word():
    """CA-04: the approved term `kill` survives as a whole word (not softened)."""
    stow = FIXTURES["CA-04"]["stow"]
    assert re.search(r"\bkill\b", stow)


def test_so06_embedded_json_byte_stable():
    """SO-06: the embedded config parses to the exact supplied object."""
    stow = FIXTURES["SO-06"]["stow"]
    found = None
    for m in re.finditer(r"\{[^{}]*\}", stow):
        try:
            obj = json.loads(m.group(0))
        except Exception:
            continue
        if "retries" in obj or "timeoutMs" in obj:
            found = obj
            break
    assert found == ev.SO06_JSON
