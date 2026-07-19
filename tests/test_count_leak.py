"""Count-leak gate for the human-facing PROSE surfaces (``README.md`` and
``docs/*.md``).

The size of the rule set can be reconstructed from how its total splits across
the upstream partitions the rules were distilled from. Publishing those
partition sizes as bare counts -- or spelling the split out as a multi-way
breakdown -- therefore leaks provenance just as surely as naming a source. This
gate keeps the prose surfaces free of that leak.

Forbidden partition sizes (as BARE COUNTS): 53, 61, 11, 24.
Explicitly allowed: 8 -- it names the precedence bands and is a structural,
non-provenance figure, so it never trips the gate.

Two rules are enforced per document:

1. Bare count. A forbidden integer must not appear as a standalone integer
   token. "Standalone" excludes any digit adjacent to a period, a hyphen, or
   another digit, so version strings ("Python 3.11", "0.1.0"), dates
   ("(2024)"), toolchain versions ("0.13.0"), platform strings
   ("Windows-10-10.0.26200-SP0"), and hyphenated ids ("CA-11", "STOW-PRO-011")
   never count as bare occurrences. A period-adjacent form is treated as a
   version/decimal segment, not a count, by design.

2. Three-way breakdown phrasing. A single line must not lay the partition out:
   three or more distinct forbidden sizes together on one line is a breakdown,
   and so is two of them alongside partition vocabulary (baseline / controlled /
   split / derived / ...). Because the real surfaces carry none of the forbidden
   sizes, this rule never fires on legitimate lines that merely happen to hold
   several unrelated integers (e.g. "17 + 10 + 6 = 33").

Run only this file: ``python -m pytest tests/test_count_leak.py -q``.
"""

import glob
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Partition sizes that must never surface as bare counts.
FORBIDDEN_COUNTS = (53, 61, 11, 24)
# Names the precedence bands; a structural figure, explicitly permitted.
ALLOWED_COUNT = 8

# A forbidden size matches only as a STANDALONE integer: the character
# immediately before and after must not be a digit, a period, or a hyphen.
# That single adjacency rule is what exempts every version string, decimal,
# date, and hyphenated identifier from the gate.
_ALT = "|".join(str(n) for n in FORBIDDEN_COUNTS)
BARE_COUNT_RE = re.compile(r"(?<![\d.\-])(?:%s)(?![\d.\-])" % _ALT)

# Vocabulary that marks a line as a rule-partition sentence. Combined with two
# or more forbidden sizes it constitutes a breakdown even without a third size.
PARTITION_WORDS_RE = re.compile(
    r"\b(?:baseline|controlled|profile|partition|split|breakdown|derived|"
    r"distilled|comprise[sd]?|of\s+which|drawn?\s+from)\b",
    re.IGNORECASE,
)


def find_bare_counts(text):
    """Return ``[(value, offset), ...]`` for every forbidden bare count."""
    return [(int(m.group()), m.start()) for m in BARE_COUNT_RE.finditer(text)]


def line_is_breakdown(line):
    """True when a single line lays out the source partition."""
    distinct = {int(v) for v in BARE_COUNT_RE.findall(line)}
    if len(distinct) >= 3:
        return True
    if len(distinct) >= 2 and PARTITION_WORDS_RE.search(line):
        return True
    return False


def scan_prose_text(text):
    """Return a list of finding strings for one document's text.

    Empty list == clean. Both a bare-count finding and a breakdown finding may
    fire on the same line; both are reported.
    """
    findings = []
    for value, offset in find_bare_counts(text):
        findings.append("bare-count %d at offset %d" % (value, offset))
    for lineno, line in enumerate(text.splitlines(), 1):
        if line_is_breakdown(line):
            findings.append("3-way breakdown at line %d: %r" % (lineno, line.strip()))
    return findings


def prose_files():
    """The real prose surfaces scanned by the gate: README + docs/*.md."""
    paths = [os.path.join(REPO, "README.md")]
    paths += sorted(glob.glob(os.path.join(REPO, "docs", "*.md")))
    return [p for p in paths if os.path.isfile(p)]


# --------------------------------------------------------------------------- #
# Numeric-match fixtures -- PASS (a digit adjacent to '.', '-', or a digit is
# never a bare count).
# --------------------------------------------------------------------------- #

def test_version_string_python_311_passes():
    assert scan_prose_text("Built and tested on Python 3.11 only.") == []


def test_semver_0_1_0_passes():
    assert scan_prose_text("The plugin manifest declares version 0.1.0.") == []


def test_year_in_parens_passes():
    # The trailing 24 in 2024 is digit-adjacent, so it is not a bare count.
    assert scan_prose_text("Quoted from the spec revision (2024) verbatim.") == []


def test_hyphenated_ids_pass():
    assert scan_prose_text("Case CA-11 and rule STOW-PRO-011 are ids, not counts.") == []


def test_platform_string_passes():
    assert scan_prose_text("Recorded on Windows-10-10.0.26200-SP0 at bootstrap.") == []


def test_dotted_toolchain_versions_pass():
    assert scan_prose_text("ruamel.yaml 0.19.1, tiktoken 0.13.0, pytest 9.1.1.") == []


def test_allowed_precedence_band_count_passes():
    # 8 is explicitly allowed; it never appears in the forbidden set.
    assert scan_prose_text("Precedence resolves through 8 bands, highest to lowest.") == []


def test_unrelated_integer_arithmetic_line_passes():
    # A line dense with unrelated integers is not a breakdown: none are forbidden.
    assert scan_prose_text("Detector split (17 + 10 + 6 = 33) across the catalog.") == []


# --------------------------------------------------------------------------- #
# Numeric-match fixtures -- FAIL (standalone forbidden integer == bare count).
# --------------------------------------------------------------------------- #

def test_comprises_11_rules_fails():
    findings = scan_prose_text("The registry comprises 11 rules in that category.")
    assert findings != []
    assert any("bare-count 11" in f for f in findings)


def test_bare_24_fails():
    findings = scan_prose_text("There are 24 of them, all told.")
    assert findings != []
    assert any("bare-count 24" in f for f in findings)


def test_bare_53_and_61_fail():
    for value in (53, 61):
        findings = scan_prose_text("exactly %d rules ship" % value)
        assert findings != [], "bare %d should be flagged" % value
        assert any("bare-count %d" % value in f for f in findings)


# --------------------------------------------------------------------------- #
# Breakdown-phrasing fixtures.
# --------------------------------------------------------------------------- #

def test_three_way_breakdown_line_fails():
    line = "The set draws 53 from one source, 8 shared, 11 from another, and 24 from a third."
    findings = scan_prose_text(line)
    assert findings != []
    # It is caught specifically as a breakdown, not only as loose bare counts.
    assert any("breakdown" in f for f in findings)


def test_two_way_breakdown_with_vocabulary_fails():
    line = "Of the total, 61 are baseline rules and 24 belong to the controlled profile."
    findings = scan_prose_text(line)
    assert findings != []
    assert any("breakdown" in f for f in findings)


# --------------------------------------------------------------------------- #
# The real prose surfaces must be clean.
# --------------------------------------------------------------------------- #

def test_prose_surfaces_discovered():
    names = {os.path.basename(p) for p in prose_files()}
    assert "README.md" in names
    assert "design.md" in names


def test_real_prose_surfaces_have_no_count_leak():
    offenders = {}
    for path in prose_files():
        with open(path, encoding="utf-8") as fh:
            findings = scan_prose_text(fh.read())
        if findings:
            offenders[os.path.relpath(path, REPO).replace("\\", "/")] = findings
    assert offenders == {}, "count leak in prose surfaces: %r" % offenders
