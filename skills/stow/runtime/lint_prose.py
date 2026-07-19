#!/usr/bin/env python3
"""Report-only prose linter.

This module is PACKAGED into the shipped skill. It is import-closed: it imports
only the Python standard library. It NEVER fails a run -- it always exits 0 and
prints advisories. Its job is to point at prose patterns a human may want to
reconsider, not to gate delivery.

The load-bearing behaviour is MASKING. Before any lexical scan, protected
regions are blanked out (replaced with spaces, preserving line and column
positions) so their contents are never flagged:

  * fenced code blocks (``` ... ``` or ~~~ ... ~~~),
  * inline code spans (`like this`),
  * block quotes (lines beginning with ``>``),
  * things that look like a URL, a filesystem path, or a code identifier.

Only the remaining prose is scanned for a small, deliberately generic advisory
set (an em-dash, a cluster of hedging words). The set is illustrative; the point
of this tool is the masking + report-only contract, not an exhaustive rulebook.
"""

import argparse
import re
import sys


# --------------------------------------------------------------------------- #
# Advisory
# --------------------------------------------------------------------------- #

class Advisory:
    def __init__(self, line, col, rule, message):
        self.line = line
        self.col = col
        self.rule = rule
        self.message = message

    def __repr__(self):
        return "Advisory(%d:%d [%s] %s)" % (self.line, self.col, self.rule, self.message)


# --------------------------------------------------------------------------- #
# Masking
# --------------------------------------------------------------------------- #

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_BLOCKQUOTE_RE = re.compile(r"^\s*>")

_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_URL_RE = re.compile(r"\b(?:https?://|ftp://|www\.)\S+", re.IGNORECASE)
# Filesystem-ish paths: posix (a/b/c, ./x, ../x, /x) and windows (C:\a\b).
_PATH_RE = re.compile(r"(?:[A-Za-z]:\\[^\s]+|(?:\.{0,2}/)[\w./\-]+|\b[\w\-]+(?:/[\w.\-]+)+)")
# Dotted / snake / underscore identifiers (module.attr, snake_case, a_b_c).
_IDENT_RE = re.compile(r"\b\w+(?:[._]\w+)+\b")
# camelCase identifiers.
_CAMEL_RE = re.compile(r"\b[a-z]+[A-Z]\w*\b")

_INLINE_MASKS = (_INLINE_CODE_RE, _URL_RE, _PATH_RE, _IDENT_RE, _CAMEL_RE)


def _blank(text):
    """A run of spaces the same length as ``text`` (preserves columns)."""
    return " " * len(text)


def _sub_blank(pattern, line):
    return pattern.sub(lambda m: _blank(m.group(0)), line)


def _mask_inline(line):
    for pattern in _INLINE_MASKS:
        line = _sub_blank(pattern, line)
    return line


def mask_protected(text):
    """Return ``text`` with all protected regions blanked to spaces.

    Line count and every column offset are preserved, so advisory positions
    computed on the masked text map straight back onto the original.
    """
    out = []
    in_fence = False
    fence_char = None
    for line in text.split("\n"):
        fence = _FENCE_RE.match(line)
        if in_fence:
            out.append(_blank(line))
            if fence and fence.group(1)[0] == fence_char:
                in_fence = False
                fence_char = None
            continue
        if fence:
            in_fence = True
            fence_char = fence.group(1)[0]
            out.append(_blank(line))
            continue
        if _BLOCKQUOTE_RE.match(line):
            out.append(_blank(line))
            continue
        out.append(_mask_inline(line))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Advisory rules (scanned over the MASKED text only)
# --------------------------------------------------------------------------- #

_EM_DASH_RE = re.compile("—")  # em dash
_HEDGE_RE = re.compile(
    r"\b(arguably|perhaps|maybe|possibly|presumably|apparently|seemingly|"
    r"somewhat|fairly|rather|quite|reportedly|allegedly)\b",
    re.IGNORECASE,
)


def lint(text):
    """Return the list of :class:`Advisory` for ``text`` (never raises)."""
    advisories = []
    masked = mask_protected(text)
    for lineno, line in enumerate(masked.split("\n"), start=1):
        for match in _EM_DASH_RE.finditer(line):
            advisories.append(Advisory(
                lineno, match.start() + 1, "em-dash",
                "em-dash (U+2014); consider a comma, colon, parentheses, or a rewrite"))
        hedges = list(_HEDGE_RE.finditer(line))
        if len(hedges) >= 2:
            words = ", ".join(sorted({h.group(0).lower() for h in hedges}))
            advisories.append(Advisory(
                lineno, hedges[0].start() + 1, "hedging",
                "hedging cluster (%s); consider stating the point plainly" % words))
    return advisories


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report (never fail on) advisory prose patterns. Exit 0 always.")
    parser.add_argument("file", help="path to the prose file to lint")
    args = parser.parse_args(argv)

    try:
        with open(args.file, "rb") as handle:
            text = handle.read().decode("utf-8", errors="replace")
    except OSError as exc:
        # Report-only: even an unreadable file is not a failure of the linter.
        print("lint_prose: cannot read %s: %s" % (args.file, exc))
        return 0

    advisories = lint(text)
    if not advisories:
        print("lint_prose: no advisories for %s" % args.file)
    else:
        print("lint_prose: %d advisory(ies) for %s (report only, exit 0)"
              % (len(advisories), args.file))
        for adv in advisories:
            print("  %d:%d [%s] %s" % (adv.line, adv.col, adv.rule, adv.message))
    return 0


if __name__ == "__main__":
    sys.exit(main())
