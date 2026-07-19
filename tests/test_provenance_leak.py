"""Tests for the anti-leak gate.

Every negative fixture (one that must FAIL the gate) is synthesised in memory
from tokens loaded out of the UNCOMMITTED private pattern file. This test module
therefore hard-codes no source-project strings and stays clean when the whole
repository is scanned.
"""

import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))


def _load_module():
    spec = importlib.util.spec_from_file_location("check_provenance_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()
_data = mod.load_patterns(PATTERNS_PATH)

pytestmark = pytest.mark.skipif(
    _data is None, reason="private pattern file not present (weak/CI environment)")

# Derived only when the private file is present; skipped tests never touch these.
if _data is not None:
    PATTERNS = mod.Patterns(_data)
    HASH_SPECS = mod.load_hash_positions(os.path.join(REPO, "tools", "hash-positions.txt"))

    DISTINCTIVE_BASENAME = PATTERNS.basenames[0]
    SHARED_PREFIX = os.path.commonprefix(PATTERNS.basenames)
    SOURCE_SHA = PATTERNS.sha256[0]
    VERDICT = PATTERNS.verdict_tokens[0]
    MULTIWORD_NAME = next(p for p in PATTERNS.phrase_tokens if " " in p)
    HYPHEN_NAME = next(p for p in PATTERNS.phrase_tokens if "-" in p and " " not in p)

CORPUS = "skills/stow/corpus/evals.jsonl"
REGISTRY = "skills/stow/registry.yaml"
BENIGN_HEX = "deadbeef" * 8  # 64 hex chars, not any source hash


def _scan(path, content):
    return mod.scan_file(path, content, PATTERNS, True, HASH_SPECS)


def _passes(path, content):
    return _scan(path, content) == []


def _fails(path, content):
    return _scan(path, content) != []


# --------------------------------------------------------------------------- #
# Gate 1 over corpus surfaces
# --------------------------------------------------------------------------- #

def test_generic_pathline_in_corpus_passes():
    assert _passes(CORPUS, "context references src/auth.ts:42 in a snippet")


def test_distinctive_basename_with_line_in_corpus_fails():
    assert _fails(CORPUS, "quoted from %s:1455 verbatim" % DISTINCTIVE_BASENAME)


def test_shared_prefix_image_path_in_corpus_passes():
    image = SHARED_PREFIX + "images/imageFile77.png"
    assert _passes(CORPUS, "asset path %s appears in prose" % image)


def test_lowercase_verdict_word_in_corpus_passes():
    assert _passes(CORPUS, "the term (restricted meaning) is fine here")


def test_uppercase_verdict_token_in_corpus_fails():
    assert _fails(CORPUS, "leaked verdict line says %s" % VERDICT)


def test_identifying_phrase_in_corpus_passes():
    assert _passes(CORPUS, "written in %s style, quoted content" % MULTIWORD_NAME)


# --------------------------------------------------------------------------- #
# Gate 1 content-hash position value check
# --------------------------------------------------------------------------- #

def test_source_hash_in_baseline_position_fails():
    assert _fails(REGISTRY, "  baseline_text_sha256: %s" % SOURCE_SHA)


def test_benign_hash_in_baseline_position_passes():
    assert _passes(REGISTRY, "  baseline_text_sha256: %s" % BENIGN_HEX)


def test_unexpected_hash_outside_exempt_position_fails():
    assert _fails("README.md", "random blob %s in prose" % BENIGN_HEX)


# --------------------------------------------------------------------------- #
# Gate 2 source-name gate
# --------------------------------------------------------------------------- #

def test_source_name_on_scanned_surface_fails():
    assert _fails("README.md", "these rules are derived from %s upstream" % HYPHEN_NAME)


def test_source_name_inside_corpus_passes():
    assert _passes(CORPUS, "these rules are derived from %s upstream" % HYPHEN_NAME)


def test_source_name_inside_corpus_passes_absolute_path():
    # The post-extract scan (P7/P9) sees absolute paths; the exemption must hold.
    p = "C:/workspace/ai/stow/stow/skills/stow/corpus/descriptions/x.md"
    assert _passes(p, "these rules are derived from %s upstream" % HYPHEN_NAME)


def test_source_name_inside_corpus_passes_dot_prefixed_path():
    assert _passes("./skills/stow/corpus/x.md",
                   "these rules are derived from %s upstream" % HYPHEN_NAME)


def test_source_name_inside_extracted_artifact_corpus_passes():
    # Extracted artifact layout: <tmp>/stow/corpus/... (no skills/ segment).
    assert _passes("/tmp/build/stow/corpus/x.md",
                   "these rules are derived from %s upstream" % HYPHEN_NAME)


def test_whole_word_abbreviation_not_matched_inside_words():
    assert _passes("README.md", "follow these steps in the system carefully")


# --------------------------------------------------------------------------- #
# Self-test: the checker's own source must pass both gates
# --------------------------------------------------------------------------- #

def test_checker_source_passes_full_mode():
    with open(CHECKER, encoding="utf-8") as fh:
        source = fh.read()
    assert _passes("tools/check_provenance_leak.py", source)


def test_checker_source_passes_weak_mode():
    with open(CHECKER, encoding="utf-8") as fh:
        source = fh.read()
    findings = mod.scan_file("tools/check_provenance_leak.py", source,
                             mod.Patterns({}), False, HASH_SPECS)
    assert findings == []


# --------------------------------------------------------------------------- #
# --local hard-fail behaviour (run via the CLI entry point)
# --------------------------------------------------------------------------- #

def test_local_missing_pattern_file_nonzero(tmp_path):
    missing = tmp_path / "absent.yaml"
    assert mod.run(["--local", "--self-test", "--patterns", str(missing)]) != 0


def test_local_empty_pattern_file_nonzero(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("# comment only\n", encoding="utf-8")
    assert mod.run(["--local", "--self-test", "--patterns", str(empty)]) != 0


def test_local_short_pattern_file_nonzero(tmp_path):
    short = tmp_path / "short.yaml"
    short.write_text("expected_n: 99\nsource_basenames:\n  - only_one.md\n",
                     encoding="utf-8")
    assert mod.run(["--local", "--self-test", "--patterns", str(short)]) != 0


def test_local_self_test_passes():
    assert mod.run(["--local", "--self-test"]) == 0


def test_weak_self_test_passes():
    assert mod.run(["--self-test"]) == 0
