"""Integration gates for the STOW kernel (SKILL.md) and its reference layer.

This module ties the kernel to ``references/*.md`` and to the machine-readable
rule registry. It is source-name-free: it names none of the external projects
the rules were derived from, so the whole repository stays clean when the
anti-leak gate scans it.

The registry is read with ruamel ``YAML(typ="safe")``. Gates enforced:

  1. Every predicate target named in the SKILL activation map resolves to an
     existing ``references/`` file.
  2. Activation-map targets resolve to ``references/`` paths only, never to a
     ``corpus/`` path (the corpus is reached indirectly, via the registry).
  3. No reference reproduces a registry ``wording.baseline_text`` string
     verbatim, and no reference exceeds a size cap (an E8 no-paraphrase proxy).
  4. Every reference either cites a ``corpus/`` path, is one of the STOW-native
     architecture references (which have no corpus provenance), or is the
     generated rule index (whose provenance is the registry).
  5. The kernel carries the exact "answer from this kernel alone" line and
     inlines no concrete ``corpus/`` module path.
  6. The kernel stays within its token budget (tiktoken ``o200k_base``).
"""

import importlib.util
import os
import re

import pytest
from ruamel.yaml import YAML

# --------------------------------------------------------------------------- #
# Paths (resolved from this file, independent of the working directory)
# --------------------------------------------------------------------------- #

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                            # repository root (tests/ is one level under it)
SKILL_DIR = os.path.join(REPO, "skills", "stow")       # .../skills/stow

SKILL_PATH = os.path.join(SKILL_DIR, "SKILL.md")
REFS_DIR = os.path.join(SKILL_DIR, "references")
REGISTRY_PATH = os.path.join(SKILL_DIR, "rules", "registry.yaml")

# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #

# Size cap for a single reference (E8 no-paraphrase proxy / anti-dump backstop).
# The largest legitimate reference is the architecture note
# activation-and-precedence.md (~10.9 kB); the cap sits above it with headroom.
# The primary anti-verbatim enforcement is the baseline_text scan below plus the
# committed provenance gate, so this only has to catch a gross corpus dump.
REF_MAX_CHARS = 12000

# Kernel token ceiling (tiktoken o200k_base).
SKILL_TOKEN_CEILING = 1500

# References that are STOW-native architecture and therefore need no corpus
# citation. These describe the kernel's own machinery, not a derived rule.
NATIVE_ARCH_REFS = frozenset({
    "protected-regions.md",
    "activation-and-precedence.md",
    "user-facing-output.md",
    "conformance.md",
    "format-json.md",
    "format-jsonl.md",
    "format-yaml.md",
    "format-markdown.md",
    # Profile architecture description; carries no rule content of its own.
    "technical-clarity.md",
})

# The exact greppable kernel line that forbids eager reference/corpus loading.
KERNEL_ALONE_LINE = (
    "Do not read every reference or corpus module. "
    "When no predicate is true, answer from this kernel alone."
)

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #

# A path token in the activation map (stops at whitespace or comma). "corpus/"
# followed by a space (e.g. "the cited corpus/ module") is NOT a path token.
PATH_TOKEN_RE = re.compile(r"(?:references|corpus|rules)/[^\s,]+")

# A references/<file>.md target.
REF_TARGET_RE = re.compile(r"references/([A-Za-z0-9_.-]+\.md)")

# A concrete corpus path: "corpus/" immediately followed by at least one path
# character. "corpus/ module" (space after the slash) does not match.
CORPUS_PATH_RE = re.compile(r"corpus/[\w.-]+")

# A full corpus module citation: the module path (with any subdirectories) and an
# optional #STOW-XXX-NNN section anchor. Used by the strengthened gate 4 to prove
# every cited corpus token resolves to a real module file after fragment strip.
CORPUS_CITATION_RE = re.compile(r"corpus/[\w./-]+\.md(?:#[\w-]+)?")

# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _load_registry():
    yaml = YAML(typ="safe")
    with open(REGISTRY_PATH, encoding="utf-8") as handle:
        return yaml.load(handle)


SKILL_TEXT = _read(SKILL_PATH)
REGISTRY = _load_registry()
RECORDS = REGISTRY["records"]

# id -> verbatim baseline_text (the protected source wording).
BASELINES = {r["id"]: r["wording"]["baseline_text"] for r in RECORDS}

# name -> text for every reference file.
REFERENCES = {
    name: _read(os.path.join(REFS_DIR, name))
    for name in sorted(os.listdir(REFS_DIR))
    if name.endswith(".md")
}


def _is_generated_index(text):
    """A generated index (e.g. the rule index) declares itself in its header
    and mechanically surfaces STOW-authored registry fields; it is not an
    authored paraphrase surface."""
    return "Generated from" in text and "Do not edit by hand" in text


def _activation_map_entries():
    """Return the bullet lines of the SKILL activation-map section that carry a
    predicate -> target mapping."""
    lines = SKILL_TEXT.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and "activation map" in line.lower():
            start = i
            break
    assert start is not None, "SKILL.md has no activation-map section"

    entries = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if "->" in line and line.lstrip().startswith("-"):
            entries.append(line)
    assert entries, "activation-map section has no predicate -> target bullets"
    return entries


ACTIVATION_ENTRIES = _activation_map_entries()


# --------------------------------------------------------------------------- #
# Sanity
# --------------------------------------------------------------------------- #

def test_fixtures_present():
    assert REFERENCES, "no reference files found"
    assert BASELINES, "registry produced no baseline_text values"
    assert all(v.strip() for v in BASELINES.values()), "empty baseline_text found"


# --------------------------------------------------------------------------- #
# Gate 1 -- every activation-map target resolves to an existing reference file
# --------------------------------------------------------------------------- #

def test_activation_targets_resolve_to_existing_reference_files():
    for entry in ACTIVATION_ENTRIES:
        named = REF_TARGET_RE.findall(entry)
        assert named, "activation entry names no references/ target: %r" % entry
        for filename in named:
            path = os.path.join(REFS_DIR, filename)
            assert os.path.isfile(path), \
                "activation target references/%s does not exist" % filename


# --------------------------------------------------------------------------- #
# Gate 2 -- activation-map targets are references/ paths, never corpus/ paths
# --------------------------------------------------------------------------- #

def test_activation_targets_are_references_never_corpus():
    for entry in ACTIVATION_ENTRIES:
        rhs = entry.split("->", 1)[1]
        tokens = PATH_TOKEN_RE.findall(rhs)
        assert tokens, "activation entry has no path target: %r" % entry

        primary = tokens[0]
        assert primary.startswith("references/"), \
            "activation target is not a references/ path: %r" % entry

        assert not CORPUS_PATH_RE.search(rhs), \
            "activation target points at a corpus/ path: %r" % entry


# --------------------------------------------------------------------------- #
# Gate 3 -- no verbatim baseline reproduction; size cap (E8 no-paraphrase proxy)
# --------------------------------------------------------------------------- #

def test_no_reference_reproduces_baseline_text_verbatim():
    for name, text in REFERENCES.items():
        # The generated rule index surfaces STOW-authored registry titles, which
        # already pass the source-name gate and may coincide with a baseline; it
        # is not an authored paraphrase surface, so it is exempt from this scan.
        if _is_generated_index(text):
            continue
        for rid, baseline in BASELINES.items():
            needle = baseline.strip()
            assert needle not in text, \
                "%s reproduces %s baseline_text verbatim" % (name, rid)


def test_no_reference_exceeds_size_cap():
    for name, text in REFERENCES.items():
        assert len(text) <= REF_MAX_CHARS, \
            "%s is %d chars, over the %d cap" % (name, len(text), REF_MAX_CHARS)


# --------------------------------------------------------------------------- #
# Gate 4 -- every reference has provenance (corpus citation, native, or index)
# --------------------------------------------------------------------------- #

def test_every_reference_has_provenance():
    for name, text in REFERENCES.items():
        cites_corpus = bool(CORPUS_PATH_RE.search(text))
        is_native = name in NATIVE_ARCH_REFS
        # The generated index's provenance is the registry (the index OF corpus).
        is_index = _is_generated_index(text) and "registry.yaml" in text
        assert cites_corpus or is_native or is_index, (
            "%s cites no corpus/ path and is neither a native architecture "
            "reference nor the generated registry index" % name)


def test_every_corpus_token_in_references_resolves_on_disk():
    """Strengthened gate 4: every corpus/ module citation in every reference must
    resolve to an on-disk module file after any #fragment (section anchor) is
    stripped. This is what makes the module#anchor citations trustworthy."""
    for name, text in REFERENCES.items():
        for token in CORPUS_CITATION_RE.findall(text):
            path = token.split("#", 1)[0]
            full = os.path.join(SKILL_DIR, *path.split("/"))
            assert os.path.isfile(full), \
                "%s cites %r which does not resolve to a module file" % (name, token)


# --------------------------------------------------------------------------- #
# Gate 5 -- kernel carries the exact line and inlines no corpus content
# --------------------------------------------------------------------------- #

def test_skill_has_exact_kernel_alone_line():
    assert KERNEL_ALONE_LINE in SKILL_TEXT.splitlines(), \
        "SKILL.md is missing the exact 'answer from this kernel alone' line"


def test_skill_inlines_no_concrete_corpus_path():
    match = CORPUS_PATH_RE.search(SKILL_TEXT)
    assert match is None, \
        "SKILL.md inlines a concrete corpus path: %r" % (
            match.group(0) if match else None)


# --------------------------------------------------------------------------- #
# Gate 6 -- kernel token budget
# --------------------------------------------------------------------------- #

def test_skill_within_token_budget():
    """Ceiling holds in both measurement modes: the estimate over-counts, so
    an estimate-mode pass implies a real-token pass."""
    spec = importlib.util.spec_from_file_location(
        "measure_context_for_references",
        os.path.join(REPO, "tools", "measure_context.py"))
    measure_context = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measure_context)
    tokens = measure_context.count_tokens(SKILL_TEXT)
    assert tokens <= SKILL_TOKEN_CEILING, \
        "SKILL.md is %d tokens, over the %d ceiling" % (tokens, SKILL_TOKEN_CEILING)
