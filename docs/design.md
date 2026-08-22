# STOW design notes

## P0 -- environment and anti-leak gate

### v0.4.2 candidate verification toolchain

| Component | Version |
| --- | --- |
| CPython | 3.11.15 |
| pip installer | 26.2.1 (identity-gated; never upgraded in the workflow) |
| ruamel.yaml | 0.19.1 |
| tiktoken | 0.13.0 |
| pytest | 9.1.1 |
| jsonschema | 4.26.0 |
| Hosted platform | `ubuntu-24.04` |
| CI dependency lock | `requirements-ci.lock` (exact versions and SHA-256 hashes) |

`requirements-ci.lock` records the complete hosted-test dependency closure and
its hashes; the workflow installs it with `--require-hashes` and records the
interpreter, installer, installed set, lock digest, commit, and external-action
pins. This is a verification lock, not the user-facing runtime floor.

The shipped runtime needs only `ruamel.yaml` and `jsonschema` for
`runtime/validate.py`. `dictionary_lookup.py`, `lint_prose.py`, `profiles.py`,
`query_rules.py`, and `validate_terms.py` are standard-library only. `tiktoken`
is a repository measurement/test dependency and does not ship in the package.

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
- **Gate 2 (name gate)** runs over every file as well and flags source
  project, organisation, and person names. No surface is exempt: the public
  tree, including the corpus and the manifest, is fully STOW-native.

Modes:

- default -- weak / CI backstop: generic heuristics only, no private file needed.
- `--local` -- full: loads the private file and applies every detector;
  hard-fails if that file is absent, empty, or short.

The gate's own source passes both gates (`--self-test`), which is asserted by the
test suite and by continuous checks.

## Design notes

### Controlled-language boundary

The protected corpus carries rule material. A separate cold lexical index ships
for exact dictionary membership and explicitly listed-form lookup. It is loaded
only for controlled-technical work and returns sparse matched records; its full
contents are never placed in model context. Examples from the local source basis
are deliberately outside that lexical subset.

The **strict / fully conformant profile remains LOCKED**. Lexical membership does
not establish approved meaning in context, part of speech in context, a suitable
replacement, technical-noun or technical-verb authority, approved project
terminology, applicability, final-output validation, or delivery custody. STOW
therefore reports guided alignment and the exact checks performed, never a
certificate.

### The `.skill` artifact

The distributable artifact is an ordinary **spec-compliant ZIP** container that
is **renamed to `STOW.skill`**. There is no bespoke archive format: any
standard unzip reads it, and the anti-leak gate's post-extract scan treats the
extracted tree (`<tmp>/stow/...`, with no `skills/` segment) exactly like the
in-repo tree -- the corpus exemption keys on the `corpus/` path segment, so it
holds under both layouts.

### Unit-glyph anomaly

A small rendering anomaly is recorded here so nobody repairs it by editing the
corpus: **some unit glyphs render as empty parentheses** in certain viewers /
pipelines (the glyph fails to round-trip and collapses to `()`). The corpus and
manifest validators are designed to be indifferent to this: they **key on line
anchors** -- per-line, whitespace-normalised substring and drift-lock matching --
rather than on the exact code point of a unit symbol. A record whose example
contains such a glyph therefore still matches its baseline and its manifest
`required_substring`, because the matched anchor does not depend on the fragile
glyph. Do not repair an empty-parenthesis rendering in a corpus module; the
byte-exact source is intentional and the drift-lock protects it.

### What the drift-lock guarantees

Tier-3 matching is enforced **modulo trailing-whitespace stripping and LF
normalisation**: baseline text and its corpus module are compared after each
line is right-stripped and the text is split on `\n` (the shared `normalize()`
in `tests/test_corpus.py`, mirrored by the drift-lock hash). This is a safety
margin against editor- and platform-induced noise (stray trailing spaces,
CRLF), not a license to reflow content. On the real material this
normalisation is a measured no-op: the committed corpus already uses LF
(pinned by `.gitattributes`) and carries no trailing whitespace, so stripping
it changes nothing and the shipped bytes are what the lock covers.

What the lock claims, precisely: the PUBLIC corpus text is internally
consistent, hash-locked, and complete against the registry. Per-module wording
metadata in the manifest records which modules carry identity-neutralized
wording (retained guidance whose identifying wording was normalized to keep
the public package fully STOW-native, with meaning, scope, thresholds,
examples, and safety force preserved). For those modules the pre-normalization
baseline is preserved outside the public tree, and the governed comparative
rewrite gate still measures any future candidate against that preserved
baseline. The public tests gate public consistency and hashes; they make no
claim of byte-identity with any external source.

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

## Context budgets and load paths

The tables below measure declared file bundles, not live host context. They do
not establish which files a host read, or the resulting latency, tool calls,
memory, or repair work. Each figure comes from `tools/measure_context.py`; other
models can tokenize the same bytes differently.

The two common static bundles are measured in both tool modes: the `o200k_base`
tokenizer when its encoding is cached locally and the deterministic
`ceil(chars / 3.5)` estimator otherwise. The estimator over-counted the frozen
calibration files, but it is not an upper bound for arbitrary text or tokenizers.

| Declared file bundle | Exact tokenizer | Character estimate |
| --- | --- | --- |
| Kernel alone (`SKILL.md`) | 1130 | 1490 |
| Ordinary prose turn (kernel; no reference read) | 1130 | 1490 |

The test suite pins both rows in both modes: the kernel ceiling and the
always-on and ordinary-turn caps are asserted under the exact tokenizer and
under the forced fallback (`tests/test_always_on.py`, `tests/test_cold_budget.py`).
A drift gate in `tests/test_cold_budget.py` re-measures the two rows and fails if
this table falls out of step with a fresh measurement, so the numbers cannot go
stale unnoticed.

The remaining rows are sums of exact-tokenizer measurements for the named file
sets, not live read traces or gated invariants. They drift when references grow,
so regenerate them after a relevant file change.

| Load path | Tokens (exact) | What is resident |
| --- | --- | --- |
| Technical-clarity turn | 1684 | the kernel + `references/technical-clarity.md` |
| Public-documentation turn | 1864 | the kernel + one cold read of `references/public-documentation.md`; the reused `technical-clarity` profile does not add `references/technical-clarity.md` |
| Raw JSON artifact | 3020 | kernel + `references/format-json.md` + `references/protected-regions.md` |
| Deep single-rule lookup | one grouped module or one anchored section | kernel + the routed grouped corpus module (largest just under fifteen kilobytes) or, via bounded reads, only the rule's anchored section |
| Procedure load path | 3999 | the ordinary turn + `references/procedures.md` + `references/action-shaping.md` |
| Procedure + safety | 4792 | the procedure load path + `references/safety-instructions.md` |

The intended load path for each:

- **Kernel alone.** The smallest declared bundle carries routing cues and
  pointers rather than the full reference bodies.
- **Ordinary prose bundle.** The kernel carries the compact request router and
  descriptive digest. `references/always-on.md` remains a generated detail and
  audit surface, loaded only for an explicit applicability or rule-audit query.
- **Raw JSON bundle.** The intended route contains the kernel, the JSON format
  reference, and the protected-regions reference, without the prose digest.
  Actual host reads require telemetry from that host and run.
- **Deep single-rule lookup.** When a specific rule needs its full text, worked
  examples, or baseline, the guidance routes to one grouped corpus module (the
  largest is just under fifteen kilobytes) or, following the kernel's
  bounded-read instruction, reads only the rule's anchored section from that
  module. Corpus material is never resident by default.
- **Procedure / procedure + safety.** These are the largest declared bundles in
  the table. Whether a host reads them and what that costs is host-specific.

These are static measurements, not a turn-cost contract. Generator and budget
tests detect file and proxy-cap drift; they do not observe live runtime cost.

## Enforcement reality

The rule registry carries two adjacent fields that are easy to conflate, so the
distinction is stated plainly here.

- **`enforcement.kind` is the *intended* mechanism.** It records how a rule
  *would* be enforced by a mechanical checker: what class of check applies, what
  it would key on. It is a design declaration.
- **`enforcement.status` is the *shipped* truth.** It records what runs
  today: **four rules are callable compliance predicates**; ten advisory surface detectors
  support contextual G1 review; the remainder are
  planned or fall back to model review. The exact implemented set is derived
  bidirectionally from the runtime's own `IMPLEMENTED_VALIDATORS` constant by
  `tests/test_enforcement_status.py`, so the registry can neither overclaim nor
  underclaim a validator.

Read together: the majority of rules are *not* mechanically enforced in this
release. Four primary rules have callable compliance predicates. Ten further
matchers are advisory observations owned by G1 rules and do not establish their
contextual semantics. The profile resolver gates the semicolon, contraction,
Latin-abbreviation, and sentence-cap observations behind
`controlled-technical-guided`, exactly as the registry activation predicates
declare. Planned rules have no implemented validator. Review-fallback is
judgement, not verification.

The prose linters are **advisory / report-only**. `runtime/lint_prose.py` reports
findings and exits zero by design; it is wired into CI as a smoke invocation, not
as its own gate. Repository tests can assert that a selected advisory subset is
empty on named authored surfaces; those pytest assertions are G4 repository
gates and do not turn the linter into a G3 delivery gate. Other prose properties
that genuinely must hold use dedicated tests such as `tests/test_count_leak.py`.

This is a deliberate v0.1 position, not an oversight: shipping a checker that
silently under-detects is worse than declaring the gap. `enforcement.status` is
the field to trust, and `tests/test_enforcement_status.py` keeps it honest.

## End-to-end reality

What is proven here, and what is not:

**G4 package evidence.** The install property is a gated, model-free check.
`tests/test_install_smoke.py` builds the artifact, extracts it to a throwaway
directory, and drives sampled shipped runtime paths from the extracted tree with the
repository root off `sys.path` -- asserting extract shape, byte fidelity, import
closure, and selected accept/reject behavior from the installed location. It
runs in CI as a hard gate over those enumerated checks. It does not establish
semantic prose behavior or every host environment.

**Evidenced on one host, not proven universally.** The repository includes a
non-hermetic enabled-versus-disabled evaluation harness: `tools/ab_eval_runner.py`
with the fixed prompts, frozen rubric, and mechanical validators under
`tests/evals/ab/`, documented in `docs/FUNCTIONAL-EVIDENCE.md`. It runs the
shipped package against a live host model in an enabled arm and a disabled arm,
grades the outputs with the packaged validators and blind reviewers, and records
the deltas. This supplies useful single-host evidence for two properties the
hermetic suite cannot reach:

- **Observed selection** -- telemetry recorded whether the measured host invoked
  STOW for a given task. Availability did not force invocation, and the result
  does not establish semantic routing on other prompts or hosts.
- **Observed reads** -- where the governed run captured file-read telemetry, it
  describes that measured host and run only. Static bundle tables are not a
  substitute for those observations.

What the harness does not establish is universal cross-host behaviour. It ran on
one pinned host model per round, invocation is telemetry rather than forced, and
the evaluators share a model family with the generators, so the result is a set
of deltas on a single host, not a guarantee that every model and harness behaves
the same way. The behavioural and adversarial eval files in `tests/evals/` remain
authored expectations and fixtures that pin intended behaviour and catch
regressions in the authored material; on their own they are not live-model
evidence.

## Cross-harness scope

The interoperability claim is scoped to packaged file formats. The meta-code
schemas, templates, references, and standalone checker are concrete committed
files with repository and install tests.

Packaged schemas, templates, and file formats are portable inputs; live
cross-harness behavior remains unverified until a second harness is exercised.
Negotiated handoffs, cross-harness state continuity, and live agent exchange
remain outside the current evidence.

## Profile resolution

One shipped data file, `skills/stow/rules/profiles.json`, declares every
profile: id, aliases, lock state, model or host routing cues, the registry
selector for its included rules, its review-level guidance rules, and the map
of profile-gated lint checks. One shipped module, `runtime/profiles.py`,
resolves names (alias-aware, lock-refusing) and answers "does this check run
under this explicitly resolved profile". It never reads request text or infers
intent. The linter, generators, kernel activation map, and tests read the same declaration, which ends the
earlier state where profile semantics were re-encoded independently across a
dozen surfaces and the runtime honored the gate for only one of the four
profile-band checks it implemented.

For a supplied profile, the resolver applies the declared check map: the
controlled-family checks run under `controlled-technical-guided`,
`technical-clarity` adds review guidance without changing the mechanical set,
and `controlled-technical-strict` refuses resolution. A drift test asserts the resolver's
controlled-family selector matches the set of registry records whose activation
predicate names the controlled profile, and a scope-fidelity test proves each
gated callable check silent outside its owning profile on a tripping fixture.

## Conflict registry

`skills/stow/rules/conflicts.yaml` is the machine-readable record of every
cross-rule collision: participants, an observable activation predicate, the
winning band, the losing behavior, the permitted substitute, deterministic vs
semantic-review resolution, and paired conforming/violating fixtures. The eight
pairs already declared inside `registry.yaml` are imported with their
resolutions verbatim (a test asserts string equality both directions and that
the enrichment never extends a registry resolution); the composition pairs
added by the hardening pass are canonical in the conflict registry itself.
`docs/rule-conflicts.md` is generated from it by `tools/gen_rule_conflicts.py`
and drift-checked in CI.

## Context measurement method

`tools/measure_context.py` records its method. When the `o200k_base` encoding is
already present in the selected local cache it uses that tokenizer; when the
named cache file is absent it does not call tiktoken and uses
`ceil(chars / 3.5)`. A corrupt present cache can still trigger behavior inside
tiktoken and is outside the offline precheck. The estimator is deterministic
for its formula and was conservative on the historical calibration set, but it
is not a universal upper bound. Two-sided bands are reported only in tokenizer
mode; estimate-mode ceilings are repository proxy gates, not claims about live
host tokens.
