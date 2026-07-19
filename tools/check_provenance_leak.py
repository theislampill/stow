#!/usr/bin/env python3
"""Anti-leak gate for the STOW skill repository.

Two gates enforce that neither the repository nor its build artifact ever
contains a reference to the external source projects the rules were derived
from, nor any derivation trail (source file paths, source-file content hashes,
source URLs, licensing research).

Gate 1 -- the provenance gate -- runs over EVERY file and looks for hard
derivation markers: distinctive source-file basenames, source URLs, source-file
content hashes, uppercase licensing-verdict tokens, and the private marker
literal.

Gate 2 -- the source-name gate -- runs over STOW-authored surfaces only and
looks for source project / organisation / person names.

ALL pattern data is loaded at runtime from an UNCOMMITTED private file that
lives in the parent workspace (one level above the repository root). This module
hard-codes none of those strings, so it passes both of its own gates
(``--self-test``).

Modes:
  (default)      WEAK / CI backstop -- generic heuristics only (content-hash
                 shape + private marker). Needs no private pattern file.
  --local        FULL -- loads the private pattern file and applies every
                 detector. Hard-fails if the pattern file is absent, empty, or
                 carries fewer than the expected number of patterns.

Targets:
  --self-test    scan this module's own source (must pass both gates).
  --staged       scan the git staged snapshot.
  <paths...>     scan the given files.
  (none)         scan every tracked file.
"""

import argparse
import os
import re
import subprocess
import sys

PATTERNS_ENV = "STOW_LEAK_PATTERNS"
PATTERNS_BASENAME = "leak-patterns-private.yaml"
HASH_POSITIONS_BASENAME = "hash-positions.txt"

# Floor for how many individual pattern strings must load in full (--local) mode.
# Kept below the real file's own declared count so small edits do not trip it,
# but high enough that a truncated or wrong file is caught.
EXPECTED_N = 30

# Generic heuristics (need no private data, so they also run in weak mode).
HEX64_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
# Matches the private marker literal without itself containing that literal.
PRIVATE_MARKER_RE = re.compile(r"provenance[-_]private")

# A single line that opens or continues a protected baseline field.
BASELINE_KEY_RE = re.compile(r'^\s*baseline_[A-Za-z0-9_]*\s*:')
BASELINE_BLOCK_RE = re.compile(r'^(\s*)baseline_[A-Za-z0-9_]*\s*:\s*[|>][+-]?\s*(#.*)?$')
BASELINE_INLINE_RE = re.compile(r'["\'{,]\s*baseline_[A-Za-z0-9_]*\s*[:=]')

SKILL_PREFIXES = ("skills/stow/", "stow/")


# --------------------------------------------------------------------------- #
# Pattern loading
# --------------------------------------------------------------------------- #

def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_patterns_path():
    return os.path.abspath(os.path.join(repo_root(), os.pardir, PATTERNS_BASENAME))


def hash_positions_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        HASH_POSITIONS_BASENAME)


def resolve_patterns_path(explicit):
    return explicit or os.environ.get(PATTERNS_ENV) or default_patterns_path()


def load_patterns(path):
    """Load the private pattern file. Returns a dict, or None if absent/empty."""
    if not path or not os.path.isfile(path):
        return None
    try:
        from ruamel.yaml import YAML
        yaml = YAML(typ="safe")
        with open(path, encoding="utf-8") as fh:
            data = yaml.load(fh)
    except Exception:
        return None
    if not data:
        return None
    return data


class Patterns:
    """Compiled matchers built from the private pattern data."""

    _KEYS = ("source_basenames", "source_url_tokens", "source_sha256",
             "project_word_tokens", "project_phrase_tokens", "verdict_tokens",
             "literal_markers")

    def __init__(self, data):
        data = data or {}
        self.basenames = [str(x) for x in (data.get("source_basenames") or [])]
        self.url_tokens = [str(x) for x in (data.get("source_url_tokens") or [])]
        self.sha256 = [str(x).lower() for x in (data.get("source_sha256") or [])]
        self.word_tokens = [str(x) for x in (data.get("project_word_tokens") or [])]
        self.phrase_tokens = [str(x) for x in (data.get("project_phrase_tokens") or [])]
        self.verdict_tokens = [str(x) for x in (data.get("verdict_tokens") or [])]
        self.literal_markers = [str(x) for x in (data.get("literal_markers") or [])]
        self.expected_n = data.get("expected_n")
        self._compile()

    def _compile(self):
        self.basename_res = [
            re.compile(r"(?<![A-Za-z0-9_.\-])" + re.escape(b) + r"(:\d+)?(?![A-Za-z0-9_])")
            for b in self.basenames
        ]
        self.url_res = [re.compile(re.escape(u), re.IGNORECASE) for u in self.url_tokens]
        self.sha_set = set(self.sha256)
        self.word_res = [re.compile(r"\b" + re.escape(w) + r"\b") for w in self.word_tokens]
        self.phrase_res = []
        for phrase in self.phrase_tokens:
            body = re.escape(phrase).replace(r"\ ", r"\s+")
            self.phrase_res.append(
                re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE))
        # Verdict tokens: case-sensitive, uppercase, whole word.
        self.verdict_res = [re.compile(r"\b" + re.escape(v) + r"\b") for v in self.verdict_tokens]
        self.literal_res = [re.compile(re.escape(m)) for m in self.literal_markers]

    def count(self):
        return (len(self.basenames) + len(self.url_tokens) + len(self.sha256) +
                len(self.word_tokens) + len(self.phrase_tokens) +
                len(self.verdict_tokens) + len(self.literal_markers))


# --------------------------------------------------------------------------- #
# Content-hash position specs
# --------------------------------------------------------------------------- #

def _key_leaf_regex(keypart):
    """Compile a whole-word matcher for a position key leaf, or None = whole file."""
    if keypart == "*WHOLEFILE*":
        return None
    leaf = keypart.rsplit(".", 1)[-1]
    body = re.escape(leaf).replace(r"\*", r"\w*")
    return re.compile(r"(?<![A-Za-z0-9_])" + body + r"(?![A-Za-z0-9_])")


def parse_hash_spec(spec):
    """Return (filepart, compiled_key_regex_or_None)."""
    if ":" in spec:
        filepart, keypart = spec.split(":", 1)
    elif spec.startswith("*."):
        filepart, keypart = spec, "*WHOLEFILE*"
    else:
        filepart, keypart = "*", spec
    return (filepart, _key_leaf_regex(keypart))


def load_hash_positions(path):
    specs = []
    if not path or not os.path.isfile(path):
        return specs
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            specs.append(parse_hash_spec(line))
    return specs


def _file_matches(filepart, path):
    norm_path = _norm(path)
    base = norm_path.rsplit("/", 1)[-1]
    if filepart == "*":
        return True
    if filepart.startswith("*."):
        return norm_path.endswith(filepart[1:])
    return base == filepart or norm_path.endswith("/" + filepart)


def hex_position_exempt(path, line, specs):
    for filepart, key_re in specs:
        if not _file_matches(filepart, path):
            continue
        if key_re is None:
            return True
        if key_re.search(line):
            return True
    return False


# --------------------------------------------------------------------------- #
# Path classification
# --------------------------------------------------------------------------- #

def _norm(path):
    return path.replace("\\", "/")


def _strip_skill_prefix(norm_path):
    for pre in SKILL_PREFIXES:
        if norm_path.startswith(pre):
            return norm_path[len(pre):]
    return norm_path


CORPUS_SEGMENT_RE = re.compile(r"(^|/)corpus/")


def is_corpus_path(path):
    """Content surface where source-derived text is allowed (Gate 2 exempt).

    The ``corpus/`` directory exists only under the skill root, so a
    ``corpus/`` path segment identifies it unambiguously. Matching the segment
    (rather than a leading skill prefix) keeps the exemption correct no matter
    how the path is expressed -- repo-relative ``skills/stow/corpus/x``,
    ``./skills/stow/corpus/x``, an absolute path, or the extracted artifact's
    ``<tmp>/stow/corpus/x``. ``corpus_manifest.yaml`` is matched by basename.
    """
    norm_path = _norm(path)
    if CORPUS_SEGMENT_RE.search(norm_path):
        return True
    base = norm_path.rsplit("/", 1)[-1]
    if base == "corpus_manifest.yaml":
        return True
    return False


# --------------------------------------------------------------------------- #
# Scanning
# --------------------------------------------------------------------------- #

class Finding:
    def __init__(self, path, line, gate, kind):
        self.path = path
        self.line = line
        self.gate = gate
        self.kind = kind

    def __repr__(self):
        return "%s:%d [%s] %s" % (self.path, self.line, self.gate, self.kind)


def scan_file(path, content, patterns, full_mode, hash_specs):
    """Return a list of Finding for one (path, content). Empty list == clean."""
    findings = []
    corpus = is_corpus_path(path)
    in_baseline_block = False
    baseline_indent = -1

    for lineno, line in enumerate(content.splitlines(), start=1):
        # ---- Gate 2 line-level baseline-field exemption bookkeeping ----------
        indent = len(line) - len(line.lstrip())
        gate2_line_exempt = False
        if in_baseline_block:
            if line.strip() == "" or indent > baseline_indent:
                gate2_line_exempt = True
            else:
                in_baseline_block = False
        if not gate2_line_exempt:
            if BASELINE_KEY_RE.match(line):
                gate2_line_exempt = True
                if BASELINE_BLOCK_RE.match(line):
                    in_baseline_block = True
                    baseline_indent = indent
            elif BASELINE_INLINE_RE.search(line):
                gate2_line_exempt = True

        # ---- Gate 1: private marker literal (generic, both modes) ------------
        if PRIVATE_MARKER_RE.search(line):
            findings.append(Finding(path, lineno, "gate1", "private marker literal"))

        # ---- Gate 1: content-hash / source-hash --------------------------- #
        for match in HEX64_RE.finditer(line):
            value = match.group(0).lower()
            exempt = hex_position_exempt(path, line, hash_specs)
            if full_mode and value in patterns.sha_set:
                findings.append(Finding(path, lineno, "gate1", "source-file hash value"))
            elif not exempt:
                findings.append(
                    Finding(path, lineno, "gate1", "unexpected content hash"))

        # ---- Gate 1: full-mode derivation markers (all files) ------------- #
        if full_mode:
            for rex in patterns.basename_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate1", "source basename"))
            for rex in patterns.url_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate1", "source url"))
            for rex in patterns.verdict_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate1", "licensing verdict token"))
            for rex in patterns.literal_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate1", "private marker literal"))

        # ---- Gate 2: source names (STOW-authored surfaces only) ----------- #
        if full_mode and not corpus and not gate2_line_exempt:
            for rex in patterns.word_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate2", "source name"))
            for rex in patterns.phrase_res:
                if rex.search(line):
                    findings.append(Finding(path, lineno, "gate2", "source name"))

    return findings


# --------------------------------------------------------------------------- #
# Target enumeration
# --------------------------------------------------------------------------- #

def _read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\x00" in raw:
        return None  # binary; skip
    return raw.decode("utf-8", errors="replace")


def _git(args):
    try:
        out = subprocess.run(["git"] + args, cwd=repo_root(),
                             capture_output=True, text=True)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def targets_self():
    path = os.path.abspath(__file__)
    rel = os.path.relpath(path, repo_root()).replace("\\", "/")
    content = _read_text(path)
    return [(rel, content)] if content is not None else []


def targets_staged():
    out = _git(["diff", "--cached", "--name-only", "-z"])
    result = []
    if not out:
        return result
    for name in out.split("\0"):
        if not name:
            continue
        blob = _git(["show", ":" + name])
        if blob is not None and "\x00" not in blob:
            result.append((name, blob))
    return result


def targets_tracked():
    out = _git(["ls-files", "-z"])
    result = []
    if not out:
        return result
    for name in out.split("\0"):
        if not name:
            continue
        content = _read_text(os.path.join(repo_root(), name))
        if content is not None:
            result.append((name, content))
    return result


def targets_paths(paths):
    result = []
    for p in paths:
        content = _read_text(p)
        if content is not None:
            rel = p.replace("\\", "/")
            result.append((rel, content))
    return result


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _banner(full_mode):
    if full_mode:
        print("=== STOW anti-leak gate :: FULL mode (local, all detectors) ===")
    else:
        print("=== STOW anti-leak gate :: WEAK mode "
              "(CI backstop -- content-hash shape + marker only) ===")


def run(argv=None):
    parser = argparse.ArgumentParser(
        description="Enforce that no source-project reference or derivation "
                    "trail leaks into the repository or its build artifact.")
    parser.add_argument("--local", action="store_true",
                        help="full mode: load the private pattern file")
    parser.add_argument("--staged", action="store_true",
                        help="scan the git staged snapshot")
    parser.add_argument("--self-test", dest="self_test", action="store_true",
                        help="scan this module's own source")
    parser.add_argument("--patterns", default=None,
                        help="override the private pattern file path")
    parser.add_argument("paths", nargs="*", help="explicit files to scan")
    args = parser.parse_args(argv)

    full_mode = args.local
    _banner(full_mode)

    if full_mode:
        patterns_path = resolve_patterns_path(args.patterns)
        data = load_patterns(patterns_path)
        if data is None:
            print("FAIL: private pattern file did not load: %s" % patterns_path,
                  file=sys.stderr)
            return 3
        patterns = Patterns(data)
        loaded = patterns.count()
        floor = EXPECTED_N
        if patterns.expected_n is not None:
            try:
                floor = max(floor, int(patterns.expected_n))
            except (TypeError, ValueError):
                pass
        if loaded < floor:
            print("FAIL: loaded %d patterns, expected at least %d"
                  % (loaded, floor), file=sys.stderr)
            return 4
        print("loaded %d patterns from %s" % (loaded, patterns_path))
    else:
        patterns = Patterns({})

    hash_specs = load_hash_positions(hash_positions_path())

    if args.self_test:
        targets = targets_self()
    elif args.staged:
        targets = targets_staged()
    elif args.paths:
        targets = targets_paths(args.paths)
    else:
        targets = targets_tracked()

    findings = []
    for path, content in targets:
        findings.extend(scan_file(path, content, patterns, full_mode, hash_specs))

    print("scanned %d file(s)" % len(targets))
    if findings:
        print("LEAK CHECK FAILED -- %d finding(s):" % len(findings))
        for f in findings:
            print("  %r" % f)
        return 1
    print("LEAK CHECK PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(run())
