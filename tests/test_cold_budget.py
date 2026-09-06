"""Cold-cache regression for the amended STOW budget contract.

The exact ``o200k_base`` gate applies to the complete ``SKILL.md`` whenever the
encoding is available.  When the cache is cold, the deterministic
``ceil(chars / 3.5)`` proxy remains a hard gate only for the operative kernel
body after YAML frontmatter.  The complete-file fallback value is still
measured and documented, but it is not an acceptance failure.
"""

import importlib.util
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.join(REPO, "skills", "stow", "SKILL.md")
ALWAYS_ON = os.path.join(REPO, "skills", "stow", "references", "always-on.md")
MEASURE = os.path.join(REPO, "tools", "measure_context.py")
DESIGN = os.path.join(REPO, "docs", "design.md")
TECHNICAL_CLARITY = os.path.join(
    REPO, "skills", "stow", "references", "technical-clarity.md")
PUBLIC_DOCUMENTATION = os.path.join(
    REPO, "skills", "stow", "references", "public-documentation.md")

KERNEL_BODY_FALLBACK_CEILING = 1500
FULL_SKILL_EXACT_CEILING = 1500
ALWAYS_ON_EST_CAP = 1750


def _load_measure():
    spec = importlib.util.spec_from_file_location("measure_context_cold", MEASURE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _force_cold(monkeypatch, tmp_path):
    """Point every recognised tokenizer cache variable at an empty directory."""
    empty = tmp_path / "empty-tokenizer-cache"
    empty.mkdir()
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(empty))
    monkeypatch.setenv("DATA_GYM_CACHE_DIR", str(empty))
    return _load_measure()


def test_fallback_is_actually_selected(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    assert mc.find_cached_encoding() is None
    assert mc.get_encoder() is None
    sample = "the quick brown fox"
    assert mc.count_tokens(sample) == mc.estimate_tokens(sample)


def test_kernel_body_fits_its_fallback_ceiling_cold(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None, "cache must be cold for this assertion to mean anything"
    body = mc.skill_body_text(_read(SKILL))
    tokens = mc.estimate_tokens(body)
    assert tokens <= KERNEL_BODY_FALLBACK_CEILING, (
        "cold kernel body is %d fallback tokens, over the %d ceiling"
        % (tokens, KERNEL_BODY_FALLBACK_CEILING))


def test_always_on_module_fits_its_cap_cold(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    tokens = mc.count_tokens(_read(ALWAYS_ON), encoder)
    assert tokens <= ALWAYS_ON_EST_CAP, (
        "cold always-on.md is %d fallback tokens, over the %d cap"
        % (tokens, ALWAYS_ON_EST_CAP))


def test_full_skill_fallback_is_recorded_nonblocking(monkeypatch, tmp_path, capsys):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    text = _read(SKILL)
    measurements = mc.skill_budget_measurements(text, encoder=encoder)
    assert measurements["full_fallback_tokens"] > FULL_SKILL_EXACT_CEILING
    assert measurements["body_fallback_tokens"] <= KERNEL_BODY_FALLBACK_CEILING
    assert mc.run_skill_budget(SKILL, encoder, require_exact=False) == 0
    output = capsys.readouterr().out
    assert "full skill fallback (recorded, nonblocking):" in output
    assert "kernel body fallback hard ceiling 1500: OK" in output
    assert "full skill exact hard ceiling 1500: NOT EVALUATED" in output


def test_skill_budget_requires_exact_only_when_requested(monkeypatch, tmp_path, capsys):
    mc = _force_cold(monkeypatch, tmp_path)
    assert mc.run_skill_budget(SKILL, mc.get_encoder(), require_exact=True) != 0
    assert "exact o200k_base measurement required" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# Documentation-truth drift gates.
# --------------------------------------------------------------------------- #


def _design_budget_value(label):
    """Current integer from the amended four-column budget table."""
    with open(DESIGN, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or label not in cells[0]:
                continue
            value = re.search(r"\d+", cells[2])
            if value:
                return int(value.group()), cells[3]
    raise AssertionError("no amended budget row for %r in docs/design.md" % label)


def _design_exact_load_row(label):
    with open(DESIGN, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3 or label not in cells[0]:
                continue
            exact = re.search(r"\d+", cells[1])
            if exact:
                return int(exact.group())
    raise AssertionError("no exact load-path row for %r in docs/design.md" % label)


def test_design_budget_rows_match_fallback_measurements(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    text = _read(SKILL)
    body = mc.skill_body_text(text)
    body_documented, body_acceptance = _design_budget_value(
        "Operative kernel body fallback")
    full_documented, full_acceptance = _design_budget_value(
        "Complete `SKILL.md` fallback")
    assert mc.estimate_tokens(body) == body_documented
    assert mc.estimate_tokens(text) == full_documented
    assert "Hard" in body_acceptance and "1,500" in body_acceptance
    assert "Recorded" in full_acceptance and "nonblocking" in full_acceptance


def test_design_full_skill_exact_row_matches_measurement():
    mc = _load_measure()
    encoder = mc.get_encoder()
    if encoder is None:
        pytest.skip("exact tokenizer unavailable (cold cache); fallback gates still run")
    documented, acceptance = _design_budget_value(
        "Complete `SKILL.md` exact `o200k_base`")
    measured = mc.count_tokens(_read(SKILL), encoder)
    assert measured == documented
    assert "Hard" in acceptance and "1,500" in acceptance


def test_design_cold_reference_rows_match_exact_measurement():
    mc = _load_measure()
    encoder = mc.get_encoder()
    if encoder is None:
        pytest.skip("exact tokenizer unavailable (cold cache)")
    expected = {
        "Technical-clarity turn": (SKILL, TECHNICAL_CLARITY),
        "Public-documentation turn": (SKILL, PUBLIC_DOCUMENTATION),
    }
    for label, paths in expected.items():
        measured = sum(mc.count_tokens(_read(path), encoder) for path in paths)
        documented = _design_exact_load_row(label)
        assert measured == documented, (
            "design.md %s figure is stale (measured %d, doc says %d)"
            % (label, measured, documented))
