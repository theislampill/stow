# STOW design notes

## P0 -- environment and anti-leak gate

### Toolchain (recorded at bootstrap)

| Component | Version |
| --- | --- |
| Python | 3.11.9 |
| ruamel.yaml | 0.19.1 |
| tiktoken | 0.13.0 |
| pytest | 9.1.1 |
| jsonschema | 4.26.0 |
| Platform | Windows-10-10.0.26200-SP0 |
| git `core.autocrlf` | false |

Packaged skill files are pinned to LF via `.gitattributes` (`skills/stow/** text
eol=lf`) so line endings stay stable regardless of a contributor's autocrlf
setting.

### Anti-leak gate

`tools/check_provenance_leak.py` is the mechanical gate that keeps the repository
and its build artifact free of any reference to the external material the rules
were derived from, and free of any derivation trail. It hard-codes none of that
data: every pattern is loaded at runtime from an uncommitted private file kept
one level above the repository root. The committed `tools/hash-positions.txt`
lists the content-hash field positions that are allowed to hold a 64-hex value.

Two gates:

- **Gate 1 (derivation gate)** runs over every file. It flags distinctive source
  basenames, source URLs, source-file content hashes, uppercase
  licensing-verdict tokens, and the private marker literal. A content hash sitting
  at one of the allowed positions is exempt from the generic 64-hex heuristic but
  is still compared for exact equality against the known source hashes, so a
  planted source hash is caught anywhere.
- **Gate 2 (name gate)** runs over authored surfaces only and flags source
  project, organisation, and person names. Corpus surfaces, the registry baseline
  fields, and the corpus manifest are exempt, because those legitimately quote
  derived content.

Modes:

- default -- weak / CI backstop: generic heuristics only, no private file needed.
- `--local` -- full: loads the private file and applies every detector;
  hard-fails if that file is absent, empty, or short.

The gate's own source passes both gates (`--self-test`), which is asserted by the
test suite and by continuous checks.

## Design notes

### v0.1 corpus boundary

The v0.1 corpus is deliberately narrow: it carries **Part-1 rule material only**.
Everything downstream of the rules -- most notably the controlled dictionary
(and the approved terminology set and directives that travel with it) -- is
**out of scope for v0.1** and does not ship. Because those inputs are absent, the
**strict / fully conformant profile is LOCKED**: STOW gives *guided* alignment
against the Part-1 rules and never certifies full conformance. Dictionary-
dependent checks are reported as *unavailable* rather than passed. This boundary
is what keeps the shipped surface small and honest; widening it (importing the
dictionary, unlocking the strict profile) is explicitly a post-v0.1 decision, not
a gap to be quietly filled.

### The `.skill` artifact

The distributable artifact is an ordinary **spec-compliant ZIP** container that
is simply **renamed to `STOW.skill`**. There is no bespoke archive format: any
standard unzip reads it, and the anti-leak gate's post-extract scan treats the
extracted tree (`<tmp>/stow/...`, with no `skills/` segment) exactly like the
in-repo tree -- the corpus exemption keys on the `corpus/` path segment, so it
holds under both layouts.

### Unit-glyph anomaly

A small rendering anomaly is recorded here so nobody "fixes" it by editing the
corpus: **some unit glyphs render as empty parentheses** in certain viewers /
pipelines (the glyph fails to round-trip and collapses to `()`). The corpus and
manifest validators are designed to be indifferent to this: they **key on line
anchors** -- per-line, whitespace-normalised substring and drift-lock matching --
rather than on the exact code point of a unit symbol. A record whose example
contains such a glyph therefore still matches its baseline and its manifest
`required_substring`, because the matched anchor does not depend on the fragile
glyph. Do not "repair" an empty-parenthesis rendering in a corpus module; the
byte-exact source is intentional and the drift-lock protects it.

### What "verbatim" means in practice

Verbatim (Tier-3) matching is enforced **modulo trailing-whitespace stripping and
LF normalisation**: baseline text and its corpus module are compared after each
line is right-stripped and the text is split on `\n` (the shared `normalize()` in
`tests/test_corpus.py`, mirrored by the drift-lock hash). This is a safety margin
against editor- and platform-induced noise (stray trailing spaces, CRLF), not a
license to reflow content. On the **real material this normalisation is a measured
no-op**: the committed corpus already uses LF (pinned by `.gitattributes`) and
carries no trailing whitespace, so stripping it changes nothing and the raw bytes
are what ship.

### CI-vs-local leak-enforcement residual

There is a deliberate, documented residual between what CI enforces and what a
local pre-push run enforces. The **full-pattern leak gate is local-only**: it
needs the uncommitted private pattern file (kept one directory above the repo
root) and runs as `check_provenance_leak.py --local`. CI cannot see that file, so
`.github/workflows/verify.yml` runs the gate in **default / weak mode** -- a
heuristic backstop over the whole tree (content-hash shape plus the private-marker
literal) -- and the private-pattern-dependent unit tests skip themselves there
(`tests/test_provenance_leak.py`, and the Gate-2 name checks in
`tests/test_corpus.py`). The consequence: Gate-2 source-name detection and exact
source-hash comparison are verified **locally before every push**, not in CI. The
weak CI run catches the generic shapes; the strong local run is the authoritative
gate and must be green before pushing.
