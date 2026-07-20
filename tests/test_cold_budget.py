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

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.join(REPO, "skills", "stow", "SKILL.md")
ALWAYS_ON = os.path.join(REPO, "skills", "stow", "references", "always-on.md")
MEASURE = os.path.join(REPO, "tools", "measure_context.py")

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
