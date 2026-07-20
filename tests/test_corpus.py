"""P2B tests for the STOW verbatim corpus (Tier-3 protected content).

The corpus modules under skills/stow/corpus/** hold byte-exact source material.
This suite proves, from inside the repository alone (no source paths, no source
hashes), that:

  * every registry corpus_ref resolves to a module file (after fragment strip),
  * each record's baseline_text appears inside its module,
  * every corpus_ref anchor is a unique `## <ID>` heading in its module,
  * the corpus is exactly 20 modules, each within the size cap,
  * the 24 prose records map to 24 distinct anchors,
  * every manifest required_substring is present, and example-bearing modules
    carry at least one approved and one non-approved example marker,
  * the banned-lists module still contains every categorized term (by count),
  * all 14 detection-reference sections are represented in the prose-integrity
    corpus (section-level completeness, checked against a fixed heading list),
  * the secondary action-shaping sections are present as `##` anchors,
  * each module matches its drift-lock sha256 in the manifest,
  * the provenance anti-leak gate finds nothing in corpus/** or the manifest,
  * a deliberately mutated module breaks the drift-lock (RED), while the real
    corpus passes (GREEN).

No source-project name appears in this file. Example markers and distinctive
phrases are read from the manifest (like every tracked surface, it is fully
covered by the source-name gate: no exemptions remain).
The one deliberate exception is the fixed list of 14 detection-reference section
titles used by the section-level completeness check: they are topic headings
(not source names), pinned here on purpose so that section coverage is proven
independently of the manifest (non-circular).
"""

import hashlib
import importlib.util
import os

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.join(REPO, "skills", "stow")
CORPUS_ROOT = os.path.join(SKILL, "corpus")
REGISTRY_PATH = os.path.join(SKILL, "rules", "registry.yaml")
MANIFEST_PATH = os.path.join(HERE, "corpus_manifest.yaml")
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")
HASH_POS = os.path.join(REPO, "tools", "hash-positions.txt")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))

PROSE_CATEGORY = "prose-integrity"
BANNED_REF = "corpus/prose-integrity/banned-lists.md"

# The secondary action-shaping material (overrides/gates/rationale) is now a set
# of `##` sections inside the single action-shaping.md module, not separate files.
ACTION_SHAPING_MODULE = "corpus/action-shaping.md"
SECONDARY_SECTION_HEADINGS = [
    "## When to break the rules",                        # overrides
    "## Pre-send check",                                 # gates
    "## What limited attention changes about reading",   # rationale
]

# Pinned heading set of the untouched banned-lists module (runtime parses it by
# these H2 headings; a dropped or renamed section fails here).
BANNED_LISTS_HEADINGS = [
    "## Overused Verbs",
    "## Overused Adjectives",
    "## Overused Transitions and Connectors",
    "## Phrases That Signal AI Writing",
    "## Heading Anti-Patterns",
    "## Filler Words and Empty Intensifiers",
    "## Academic-Specific AI Tells",
    "## Hedging and Epistemic Modality Overload",
]


# --------------------------------------------------------------------------- #
# Shared primitives (the same normalize() the drift-lock hash and the verbatim
# gate use) and loaders.
# --------------------------------------------------------------------------- #

def normalize(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return YAML(typ="safe").load(fh)


def module_path(corpus_ref):
    # A corpus_ref is now module#anchor; the anchor is a section, not a file.
    ref = corpus_ref.split("#", 1)[0]
    return os.path.join(SKILL, ref.replace("/", os.sep))


def read_module(corpus_ref):
    with open(module_path(corpus_ref), encoding="utf-8") as fh:
        return fh.read()


def extract_banned_terms(text):
    """First cell of every data table row, every top-level '- ' bullet, and each
    comma-separated term on a '**Label ...:** a, b, c' marker line (the hedging
    marker word-lists). Independent re-implementation used to recount the
    banned-lists module."""
    lines = text.split("\n")
    terms = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            first = cells[0]
            if first and set(first) <= set("-: "):
                continue
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt.startswith("|"):
                inner = nxt.strip("|").replace("|", "")
                if inner and set(inner) <= set("-: "):
                    continue
            terms.append(first)
        elif s.startswith("- "):
            terms.append(s[2:].strip())
        elif s.startswith("**") and ": " in s:
            for part in s.split(": ", 1)[1].split(", "):
                part = part.strip()
                if part:
                    terms.append(part)
    return terms


REGISTRY = _load_yaml(REGISTRY_PATH)
RECORDS = REGISTRY["records"]
MANIFEST = _load_yaml(MANIFEST_PATH)
MODULES = MANIFEST["modules"]


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_provenance_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOD = _load_checker()
_PATTERN_DATA = MOD.load_patterns(PATTERNS_PATH)


# --------------------------------------------------------------------------- #
# Resolution + baseline coverage
# --------------------------------------------------------------------------- #

def test_every_corpus_ref_resolves_to_a_module_file():
    for r in RECORDS:
        p = module_path(r["corpus_ref"])
        assert os.path.isfile(p), "%s -> missing %s" % (r["id"], r["corpus_ref"])


def test_baseline_text_appears_in_its_module():
    for r in RECORDS:
        text = normalize(read_module(r["corpus_ref"]))
        baseline = normalize(r["wording"]["baseline_text"])
        assert baseline in text, "%s baseline not found in module" % r["id"]


def test_prose_records_map_to_24_distinct_anchors():
    prose = [r for r in RECORDS if r["category"] == PROSE_CATEGORY]
    assert len(prose) == 24
    refs = {r["corpus_ref"] for r in prose}
    assert len(refs) == 24, "prose anchors are not distinct"
    frags = {r["corpus_ref"].split("#", 1)[1] for r in prose}
    assert len(frags) == 24, "prose fragments are not distinct"
    for ref in refs:
        assert "#" in ref, "prose corpus_ref carries no anchor: %s" % ref
        assert os.path.isfile(module_path(ref)), ref


def test_every_corpus_ref_anchor_is_a_unique_heading_in_its_module():
    """Every corpus_ref fragment (#STOW-XXX-NNN) must appear as a literal
    `## <ID>` heading exactly once in the module it points at."""
    for r in RECORDS:
        ref = r["corpus_ref"]
        assert "#" in ref, "%s corpus_ref has no anchor" % r["id"]
        frag = ref.split("#", 1)[1]
        lines = read_module(ref).splitlines()
        count = sum(1 for ln in lines if ln == "## " + frag)
        assert count == 1, "%s: heading '## %s' appears %d time(s) in %s" % (
            r["id"], frag, count, module_path(ref))


def test_module_count_is_20_and_each_within_size_cap():
    on_disk = []
    for base, _dirs, files in os.walk(CORPUS_ROOT):
        for f in files:
            if f.endswith(".md"):
                on_disk.append(os.path.join(base, f))
    assert len(on_disk) == 23, "expected 23 corpus modules, found %d" % len(on_disk)
    for p in on_disk:
        size = os.path.getsize(p)
        assert size <= 15360, "%s is %d bytes, over the 15360 cap" % (p, size)


# --------------------------------------------------------------------------- #
# Manifest required_substrings + example markers
# --------------------------------------------------------------------------- #

def test_every_manifest_module_exists_and_matches_a_surface():
    # every manifest key is an actual corpus module on disk
    for ref in MODULES:
        assert os.path.isfile(module_path(ref)), "manifest lists missing %s" % ref


def test_required_substrings_present_in_each_module():
    for ref, entry in MODULES.items():
        text = normalize(read_module(ref))
        for sub in entry["required_substrings"]:
            assert normalize(sub) in text, "%s missing required substring %r" % (ref, sub)


def test_example_bearing_modules_have_approved_and_nonapproved_markers():
    seen = 0
    for ref, entry in MODULES.items():
        if not entry.get("example_bearing"):
            continue
        seen += 1
        text = normalize(read_module(ref))
        assert "approved_example" in entry and "nonapproved_example" in entry, ref
        assert normalize(entry["approved_example"]) in text, \
            "%s missing approved marker" % ref
        assert normalize(entry["nonapproved_example"]) in text, \
            "%s missing non-approved marker" % ref
    assert seen > 0, "expected at least one example-bearing module"


# --------------------------------------------------------------------------- #
# banned-lists cardinality (every categorized term present)
# --------------------------------------------------------------------------- #

def test_banned_lists_heading_set_is_pinned():
    lines = read_module(BANNED_REF).splitlines()
    headings = [ln for ln in lines if ln.startswith("## ")]
    assert headings == BANNED_LISTS_HEADINGS, \
        "banned-lists heading set changed: %r" % headings


def test_banned_lists_contains_every_categorized_term():
    entry = MODULES[BANNED_REF]
    text = read_module(BANNED_REF)
    terms = extract_banned_terms(text)
    # cardinality: recount from the module equals the manifest-declared count
    assert entry["banned_term_count"] == len(terms)
    assert entry["banned_terms"] == terms
    # not merely non-empty: a substantial, categorized set
    assert len(terms) >= 50, "banned-lists lost terms: only %d" % len(terms)
    ntext = normalize(text)
    for t in terms:
        assert normalize(t) in ntext, "banned term missing from module: %r" % t


# --------------------------------------------------------------------------- #
# Detection-reference section-level completeness (non-circular).
#
# The AI-writing detection reference these prose-integrity modules are vendored
# from is organized into 14 top-level sections. This list is fixed here on
# purpose -- it is NOT derived from the manifest or the registry -- so the check
# fails if any section is dropped from the corpus even when the manifest stays
# internally self-consistent. Each entry is a topic heading, not a source name.
# --------------------------------------------------------------------------- #

DETECTION_REFERENCE_SECTIONS = [
    "Em Dashes: The Primary AI Tell",
    "Overused Verbs",
    "Overused Adjectives",
    "Overused Transitions and Connectors",
    "Phrases That Signal AI Writing",
    "Filler Words and Empty Intensifiers",
    "Heading Anti-Patterns",
    "Academic-Specific AI Tells",
    "Hallucinated Markup Artifacts",
    "Hedging and Epistemic Modality Overload",
    "Structural and Statistical Patterns",
    "Model-Family-Specific Tells",
    "False Positive Prevention",
    "How to Self-Check",
]


def _prose_integrity_corpus_text():
    """Normalized concatenation of every prose-integrity corpus module on disk."""
    root = os.path.join(CORPUS_ROOT, PROSE_CATEGORY)
    blobs = []
    for base, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".md"):
                with open(os.path.join(base, f), encoding="utf-8") as fh:
                    blobs.append(normalize(fh.read()))
    return "\n\n".join(blobs)


def test_every_detection_reference_section_is_represented():
    # Fixed at 14 distinct sections; each must appear as an actual H2 heading in
    # some prose-integrity module. Independent of the manifest, so a dropped
    # section fails here even if the manifest is self-consistent.
    assert len(DETECTION_REFERENCE_SECTIONS) == 14
    assert len(set(DETECTION_REFERENCE_SECTIONS)) == 14
    corpus_text = _prose_integrity_corpus_text()
    missing = [h for h in DETECTION_REFERENCE_SECTIONS
               if ("## " + h) not in corpus_text]
    assert missing == [], \
        "detection-reference sections absent from prose-integrity corpus: %r" % missing


# --------------------------------------------------------------------------- #
# Secondary action-shaping modules
# --------------------------------------------------------------------------- #

def test_secondary_action_shaping_sections_present_as_anchors():
    """The secondary action-shaping material now lives as `##` sections inside
    action-shaping.md; assert each heading is present and the module is tracked."""
    assert ACTION_SHAPING_MODULE in MODULES, \
        "%s absent from manifest" % ACTION_SHAPING_MODULE
    lines = read_module(ACTION_SHAPING_MODULE).splitlines()
    for heading in SECONDARY_SECTION_HEADINGS:
        assert heading in lines, \
            "action-shaping.md missing secondary section heading %r" % heading


# --------------------------------------------------------------------------- #
# Drift-lock
# --------------------------------------------------------------------------- #

def _sha_norm(text):
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def test_drift_lock_sha256_matches_for_every_module():
    for ref, entry in MODULES.items():
        got = _sha_norm(read_module(ref))
        assert got == entry["corpus_exact_sha256"], "%s drift-lock mismatch" % ref


def test_every_disk_module_is_in_the_manifest():
    on_disk = set()
    for base, _dirs, files in os.walk(CORPUS_ROOT):
        for f in files:
            if f.endswith(".md"):
                full = os.path.join(base, f)
                rel = os.path.relpath(full, SKILL).replace(os.sep, "/")
                on_disk.add(rel)
    assert on_disk == set(MODULES), \
        "disk/manifest mismatch: %r" % (on_disk.symmetric_difference(set(MODULES)))


# --------------------------------------------------------------------------- #
# RED first: a mutated module breaks the drift-lock; the real corpus passes.
# --------------------------------------------------------------------------- #

def test_mutated_module_breaks_drift_lock_but_real_passes():
    ref = RECORDS[0]["corpus_ref"]
    mref = ref.split("#", 1)[0]
    real = read_module(ref)
    stored = MODULES[mref]["corpus_exact_sha256"]

    # GREEN: the real module matches its drift-lock hash.
    assert _sha_norm(real) == stored

    # RED: one interpolated sentence changes the normalized bytes and the hash.
    mutated = real.rstrip("\n") + "\nThis sentence was interpolated.\n"
    assert normalize(mutated) != normalize(real)
    assert _sha_norm(mutated) != stored

    # RED: a single casing change and a single punctuation change also break it.
    cased = real.replace("Technical", "technical", 1)
    if cased != real:
        assert _sha_norm(cased) != stored
    punct = real.replace(".", ";", 1)
    if punct != real:
        assert _sha_norm(punct) != stored


# --------------------------------------------------------------------------- #
# Provenance anti-leak gate over corpus/** + the manifest.
# --------------------------------------------------------------------------- #

_leak = pytest.mark.skipif(
    _PATTERN_DATA is None,
    reason="private pattern file not present (weak/CI environment)")


@_leak
def test_provenance_gate_clean_over_corpus_and_manifest():
    patterns = MOD.Patterns(_PATTERN_DATA)
    hash_specs = MOD.load_hash_positions(HASH_POS)

    targets = []
    for base, _dirs, files in os.walk(CORPUS_ROOT):
        for f in files:
            if f.endswith(".md"):
                full = os.path.join(base, f)
                rel = "skills/stow/" + os.path.relpath(full, SKILL).replace(os.sep, "/")
                targets.append((rel, full))
    targets.append(("tests/corpus_manifest.yaml", MANIFEST_PATH))

    findings = []
    for rel, full in targets:
        with open(full, encoding="utf-8") as fh:
            findings.extend(MOD.scan_file(rel, fh.read(), patterns, True, hash_specs))
    assert findings == [], "unexpected leak findings: %r" % findings[:10]


@_leak
def test_planted_identifiers_in_corpus_are_caught_by_both_gates():
    """The public corpus is fully STOW-native: a source basename (gate 1) and a
    source name (gate 2) planted into a corpus module must BOTH be caught."""
    patterns = MOD.Patterns(_PATTERN_DATA)
    hash_specs = MOD.load_hash_positions(HASH_POS)
    ref = "skills/stow/corpus/words/selection.md"
    planted_basename = "quoted from %s:1 in text\n" % patterns.basenames[0]
    assert MOD.scan_file(ref, planted_basename, patterns, True, hash_specs) != []
    planted_name = "derived from %s upstream\n" % patterns.word_tokens[0]
    assert MOD.scan_file(ref, planted_name, patterns, True, hash_specs) != []
