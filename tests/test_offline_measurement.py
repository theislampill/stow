"""Offline-hermeticity gates for the context-measurement tool.

The default test suite must perform no network request. tiktoken downloads a
missing encoding on first use, so tools/measure_context.py detects the local
cache itself and falls back to a deterministic conservative estimate
(ceil(chars / 3.5)) when the encoding is absent. These gates prove:

  * the fallback is deterministic and matches its stated formula;
  * a run with NO cache available completes, records its method, enforces the
    ceiling, and never attempts the network (a dead proxy would break any
    attempt loudly);
  * the measurement method is recorded in the output in both modes.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import importlib.util
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MEASURE = os.path.join(REPO, "tools", "measure_context.py")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


measure_context = _load("measure_context_offline", MEASURE)


def test_estimator_matches_its_stated_formula():
    for text in ("", "a", "abc", "word " * 100, "x" * 3500):
        assert measure_context.estimate_tokens(text) == \
            int(math.ceil(len(text) / 3.5))


def test_count_tokens_uses_the_estimator_when_no_encoder():
    text = "The cache is cold. Restart it."
    assert measure_context.count_tokens(text, encoder=None) == \
        measure_context.estimate_tokens(text)


def test_find_cached_encoding_honors_the_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_GYM_CACHE_DIR", str(tmp_path / "none"))
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path / "tmp"))
    assert measure_context.find_cached_encoding() is None


def _offline_env(tmp_path):
    """Environment with every cache candidate empty and the network dead."""
    env = dict(os.environ)
    env["TIKTOKEN_CACHE_DIR"] = str(tmp_path / "empty-cache")
    env["DATA_GYM_CACHE_DIR"] = str(tmp_path / "empty-gym")
    env["TMPDIR"] = env["TMP"] = env["TEMP"] = str(tmp_path / "empty-tmp")
    # A dead proxy makes any network attempt fail loudly instead of silently
    # succeeding on a machine that happens to be online.
    env["HTTPS_PROXY"] = env["HTTP_PROXY"] = "http://127.0.0.1:9"
    for directory in ("empty-cache", "empty-gym", "empty-tmp"):
        (tmp_path / directory).mkdir(exist_ok=True)
    return env


def test_offline_run_is_deterministic_and_never_networks(tmp_path):
    sample = tmp_path / "sample.md"
    body = "A short measured file.\n" * 20
    sample.write_bytes(body.encode("utf-8"))  # byte-exact: no newline translation

    proc = subprocess.run(
        [sys.executable, MEASURE, str(sample)],
        capture_output=True, text=True, env=_offline_env(tmp_path), cwd=REPO,
        timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "estimate-chars-3.5" in proc.stdout
    assert "no download attempted" in proc.stdout
    expected = int(math.ceil(len(body) / 3.5))
    assert ("tokens: %d" % expected) in proc.stdout
    assert "NOT EVALUATED" in proc.stdout          # band is tokenizer-only
    assert "hard ceiling 1500: OK" in proc.stdout  # ceiling enforced anyway


def test_offline_run_still_fails_an_over_ceiling_file(tmp_path):
    sample = tmp_path / "big.md"
    sample.write_text("word " * 3000, encoding="utf-8")  # est far over 1500

    proc = subprocess.run(
        [sys.executable, MEASURE, str(sample)],
        capture_output=True, text=True, env=_offline_env(tmp_path), cwd=REPO,
        timeout=60)
    assert proc.returncode != 0
    assert "EXCEEDED" in proc.stdout


def test_method_is_recorded_in_both_modes(tmp_path):
    sample = tmp_path / "sample.md"
    sample.write_text("A short measured file.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, MEASURE, str(sample)],
        capture_output=True, text=True, cwd=REPO, timeout=60)
    assert proc.returncode == 0
    assert "measurement: " in proc.stdout
