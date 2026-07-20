"""Cold-cache budget regression: the kernel and the ordinary prose-turn bundle
must fit their ceilings under the DETERMINISTIC FALLBACK estimator, not only
under the exact tokenizer.

The warm suite measures with tiktoken when its encoding is cached locally. On a
cold host (no tokenizer cache, and the tool never downloads) measure_context
falls back to ceil(chars / 3.5). That fallback over-counts, so a file that fits
warm can still bust the ceiling cold. This module forces the fallback by pointing
the tokenizer cache at an empty directory, then re-runs the REAL budget
assertions on the shipped files. If SKILL.md or always-on.md grows past the cold
limit, these fail even when the warm suite is green.
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

# The same ceilings the warm suite enforces, in their fallback (EST) form.
# Kernel single-file ceiling holds in BOTH modes (test_references.py,
# test_build.py, measure_context single-file). The always-on and ordinary EST
# caps mirror test_always_on.py's fallback-mode caps.
KERNEL_CEILING = 1500
ALWAYS_ON_EST_CAP = 1750
ORDINARY_EST_CAP = 3100


def _load_measure():
    spec = importlib.util.spec_from_file_location("measure_context_cold", MEASURE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _force_cold(monkeypatch, tmp_path):
    """Point every tokenizer-cache variable measure_context honors at an empty
    directory, so the encoding is never found and the estimator is selected."""
    empty = tmp_path / "empty-tokenizer-cache"
    empty.mkdir()
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(empty))
    monkeypatch.setenv("DATA_GYM_CACHE_DIR", str(empty))
    return _load_measure()


def test_fallback_is_actually_selected(monkeypatch, tmp_path):
    """Guard the guard: with an empty cache dir the tool must choose the
    estimator, or the assertions below would silently test the warm path."""
    mc = _force_cold(monkeypatch, tmp_path)
    assert mc.find_cached_encoding() is None
    assert mc.get_encoder() is None
    sample = "the quick brown fox"
    assert mc.count_tokens(sample) == mc.estimate_tokens(sample)


def test_kernel_fits_its_ceiling_cold(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None, "cache must be cold for this assertion to mean anything"
    tokens = mc.count_tokens(_read(SKILL), encoder)
    assert tokens <= KERNEL_CEILING, (
        "cold kernel is %d fallback tokens, over the %d ceiling"
        % (tokens, KERNEL_CEILING))


def test_always_on_module_fits_its_cap_cold(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    tokens = mc.count_tokens(_read(ALWAYS_ON), encoder)
    assert tokens <= ALWAYS_ON_EST_CAP, (
        "cold always-on.md is %d fallback tokens, over the %d cap"
        % (tokens, ALWAYS_ON_EST_CAP))


def test_ordinary_prose_turn_bundle_fits_its_cap_cold(monkeypatch, tmp_path):
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    total = (mc.count_tokens(_read(SKILL), encoder)
             + mc.count_tokens(_read(ALWAYS_ON), encoder))
    assert total <= ORDINARY_EST_CAP, (
        "cold ordinary prose-turn bundle is %d fallback tokens, over the %d cap"
        % (total, ORDINARY_EST_CAP))


def test_measure_single_file_exits_zero_cold(monkeypatch, tmp_path):
    """The build's extracted-SKILL ceiling check shells out to measure_context;
    it must exit 0 (ceiling OK) in fallback mode too."""
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    assert mc.run_single(SKILL, encoder) == 0


# --------------------------------------------------------------------------- #
# Documentation-truth drift gate: the two-mode budget table in docs/design.md
# ("Always-resident path" | exact | fallback) must stay in step with a fresh
# measurement, so the published numbers cannot go stale unnoticed.
# --------------------------------------------------------------------------- #

KERNEL_PATHS = (SKILL,)
ORDINARY_PATHS = (SKILL, ALWAYS_ON)


def _sum_tokens(mc, encoder, paths):
    return sum(mc.count_tokens(_read(p), encoder) for p in paths)


def _design_two_mode_row(label):
    """(exact, fallback) integers from the design.md two-mode budget row whose
    first cell contains ``label``."""
    with open(DESIGN, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3 or label not in cells[0]:
                continue
            exact = re.search(r"\d+", cells[1])
            fallback = re.search(r"\d+", cells[2])
            if exact and fallback:
                return int(exact.group()), int(fallback.group())
    raise AssertionError("no two-mode budget row for %r in docs/design.md" % label)


def test_design_budget_table_fallback_matches_measurement(monkeypatch, tmp_path):
    """The fallback column of the design.md two-mode table must equal a fresh
    fallback measurement. The estimator is deterministic (pure char count), so
    this is an exact-equality drift gate that runs on every host, CI included."""
    mc = _force_cold(monkeypatch, tmp_path)
    encoder = mc.get_encoder()
    assert encoder is None
    _k_exact, k_fallback = _design_two_mode_row("Kernel alone")
    _o_exact, o_fallback = _design_two_mode_row("Ordinary prose turn")
    assert _sum_tokens(mc, encoder, KERNEL_PATHS) == k_fallback, (
        "design.md kernel fallback figure is stale (measured %d, doc says %d)"
        % (_sum_tokens(mc, encoder, KERNEL_PATHS), k_fallback))
    assert _sum_tokens(mc, encoder, ORDINARY_PATHS) == o_fallback, (
        "design.md ordinary fallback figure is stale (measured %d, doc says %d)"
        % (_sum_tokens(mc, encoder, ORDINARY_PATHS), o_fallback))


def test_design_budget_table_exact_matches_measurement():
    """The exact column must match the exact tokenizer when its encoding is
    cached. On a cold host the exact tokenizer is unavailable, so the check is
    skipped rather than measured in the wrong mode; the fallback gate above
    still catches drift there."""
    mc = _load_measure()
    encoder = mc.get_encoder()
    if encoder is None:
        pytest.skip("exact tokenizer unavailable (cold cache); "
                    "fallback drift gate still runs")
    k_exact, _k_fallback = _design_two_mode_row("Kernel alone")
    o_exact, _o_fallback = _design_two_mode_row("Ordinary prose turn")
    assert _sum_tokens(mc, encoder, KERNEL_PATHS) == k_exact, (
        "design.md kernel exact figure is stale (measured %d, doc says %d)"
        % (_sum_tokens(mc, encoder, KERNEL_PATHS), k_exact))
    assert _sum_tokens(mc, encoder, ORDINARY_PATHS) == o_exact, (
        "design.md ordinary exact figure is stale (measured %d, doc says %d)"
        % (_sum_tokens(mc, encoder, ORDINARY_PATHS), o_exact))
