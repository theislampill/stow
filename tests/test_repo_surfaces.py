"""Tests for the repository working-rule surfaces: ``AGENTS.md`` and
``CHANGELOG.md``.

These two authored surfaces are governed like every other STOW-authored file:
they must exist, they must pass the source-name gate (Gate 2 of the anti-leak
checker), and they must carry the sections that make them useful. This module
also re-asserts count-leak safety directly on the two files, so a forbidden
partition size can never slip into them.

The source-name assertions load the private pattern file the same way
``test_provenance_leak.py`` does, and skip when it is absent (the weak/CI
environment). The existence, section, and count-leak assertions always run.

Run only this file: ``python -m pytest tests/test_repo_surfaces.py -q``.
"""

import importlib.util
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))

AGENTS = os.path.join(REPO, "AGENTS.md")
CHANGELOG = os.path.join(REPO, "CHANGELOG.md")

# Forbidden source-partition sizes; must never appear as a bare count on an
# authored surface. Adjacency to a digit, period, or hyphen is never a count
# (so version strings, dates, and hyphenated ids are exempt), matching the
# count-leak gate in test_count_leak.py.
FORBIDDEN_COUNTS = (53, 61, 11, 24)
_ALT = "|".join(str(n) for n in FORBIDDEN_COUNTS)
BARE_COUNT_RE = re.compile(r"(?<![\d.\-])(?:%s)(?![\d.\-])" % _ALT)


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_provenance_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_checker()
_data = mod.load_patterns(PATTERNS_PATH)

_needs_patterns = pytest.mark.skipif(
    _data is None, reason="private pattern file not present (weak/CI environment)")

if _data is not None:
    PATTERNS = mod.Patterns(_data)
    HASH_SPECS = mod.load_hash_positions(os.path.join(REPO, "tools", "hash-positions.txt"))


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------- #
# Existence
# --------------------------------------------------------------------------- #

def test_agents_md_exists():
    assert os.path.isfile(AGENTS), "AGENTS.md is missing"


def test_changelog_md_exists():
    assert os.path.isfile(CHANGELOG), "CHANGELOG.md is missing"


# --------------------------------------------------------------------------- #
# Required sections
# --------------------------------------------------------------------------- #

AGENTS_REQUIRED = (
    "# STOW working rules for agents",
    "## Repository map",
    "## Source-name-free surfaces",
    "### Count-leak scope",
    "## Two-gate leak model",
    "## Verbatim corpus and local provenance",
    "## The registry is canonical",
    "## Kernel budget and progressive disclosure",
    "## Build reproducibility",
)

# Content the working rules must actually state, not just head.
AGENTS_REQUIRED_CONTENT = (
    "primary_total",     # the invariant is named by its registry field
    "104",               # the allowed rule total
    "byte-exact",        # the byte-exact build line
    "Do not commit local files",
)

CHANGELOG_REQUIRED = (
    "# Changelog",
    "Keep a Changelog",
    "Semantic Versioning",
    "## [Unreleased]",
    "v0.2",
    "## [0.1.0]",
    "### Added",
    "### Known limitations",
)


def test_agents_has_required_sections():
    text = _read(AGENTS)
    missing = [s for s in AGENTS_REQUIRED if s not in text]
    assert missing == [], "AGENTS.md missing sections: %r" % missing


def test_agents_states_required_content():
    text = _read(AGENTS)
    missing = [s for s in AGENTS_REQUIRED_CONTENT if s not in text]
    assert missing == [], "AGENTS.md missing required content: %r" % missing


def test_changelog_has_required_sections():
    text = _read(CHANGELOG)
    missing = [s for s in CHANGELOG_REQUIRED if s not in text]
    assert missing == [], "CHANGELOG.md missing sections: %r" % missing


# --------------------------------------------------------------------------- #
# Count-leak safety (always runs; forbidden partition sizes must be absent)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", [AGENTS, CHANGELOG])
def test_surface_has_no_bare_forbidden_count(path):
    text = _read(path)
    hits = [(int(m.group()), m.start()) for m in BARE_COUNT_RE.finditer(text)]
    assert hits == [], "forbidden bare count in %s: %r" % (os.path.basename(path), hits)


# --------------------------------------------------------------------------- #
# Source-name gate (Gate 2) -- needs the private pattern file
# --------------------------------------------------------------------------- #

@_needs_patterns
@pytest.mark.parametrize("rel", ["AGENTS.md", "CHANGELOG.md"])
def test_surface_passes_full_leak_gate(rel):
    content = _read(os.path.join(REPO, rel))
    findings = mod.scan_file(rel, content, PATTERNS, True, HASH_SPECS)
    assert findings == [], "leak findings in %s: %r" % (rel, findings)


@pytest.mark.parametrize("rel", ["AGENTS.md", "CHANGELOG.md"])
def test_surface_passes_weak_leak_gate(rel):
    # The weak backstop needs no private data and must also be clean: no stray
    # content-hash-shaped token and no private marker literal.
    content = _read(os.path.join(REPO, rel))
    findings = mod.scan_file(rel, content, mod.Patterns({}), False, [])
    assert findings == [], "weak-gate findings in %s: %r" % (rel, findings)
