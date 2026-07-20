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

tiktoken additionally pulls `requests` and `regex` transitively, and on Python
3.11 `jsonschema` pulls `referencing` and `typing_extensions`. The shipped
runtime needs only `ruamel.yaml` and `jsonschema` (for `validate.py`);
`lint_prose.py` and `profiles.py` are standard-library only, and tiktoken never
ships.

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

STOW is built so that the cost of a turn tracks what the turn needs. The
kernel is the only surface that is always resident; everything else is pulled in
on demand. Every figure below is a token count from `tools/measure_context.py`,
measured at version 0.3.5; other models tokenize differently, so treat them as a
calibrated proxy and leave headroom.

The two always-resident paths are measured in both of the tool's modes: the
exact tokenizer (`o200k_base`, used when its encoding is cached locally) and the
deterministic conservative fallback (`ceil(chars / 3.5)`, used on a cold host
with no cache). The fallback over-counts, so a path that fits under its fallback
figure also fits under its exact figure.

| Always-resident path | Exact tokenizer | Conservative fallback |
| --- | --- | --- |
| Kernel alone (`SKILL.md`) | 1059 | 1454 |
| Ordinary prose turn (kernel + `references/always-on.md`) | 2340 | 3053 |

The test suite pins both rows in both modes: the kernel ceiling and the
always-on and ordinary-turn caps are asserted under the exact tokenizer and
under the forced fallback (`tests/test_always_on.py`, `tests/test_cold_budget.py`).
A drift gate in `tests/test_cold_budget.py` re-measures the two rows and fails if
this table falls out of step with a fresh measurement, so the numbers cannot go
stale unnoticed.

The remaining load paths are exact-tokenizer point measurements of one specific
file set, not gated invariants. They drift when the underlying references grow,
so regenerate them with `tools/measure_context.py` after any reference change.

| Load path | Tokens (exact) | What is resident |
| --- | --- | --- |
| Technical-clarity turn | 2823 | the ordinary turn + `references/technical-clarity.md` |
| Raw JSON artifact | 3093 | kernel + `references/format-json.md` + `references/protected-regions.md` |
| Deep single-rule lookup | one grouped module or one anchored section | kernel + the routed grouped corpus module (largest just under fifteen kilobytes) or, via bounded reads, only the rule's anchored section |
| Procedure load path | 5219 | the ordinary turn + `references/procedures.md` + `references/action-shaping.md` |
| Procedure + safety | 5967 | the procedure load path + `references/safety-instructions.md` |

The intended load path for each:

- **Kernel alone.** The routing surface. It carries activation cues and pointers,
  not rule text, and sits under the 1500-token hard ceiling with room to spare.
- **Ordinary prose turn.** Any user-facing prose turn additionally loads the
  generated always-on reference, which is the full set of operational checks that
  apply to every such turn. This is the common case, and it is deliberately the
  second-cheapest path.
- **Raw JSON artifact.** A structured-output turn loads the format reference and
  the protected-regions reference and **no prose checks at all**. This is the
  point of splitting always-on out of the kernel: a machine-readable artifact
  never pays for prose guidance it must not apply. Zero prose checks are resident
  on this path.
- **Deep single-rule lookup.** When a specific rule needs its full text, worked
  examples, or baseline, the reader routes to one grouped corpus module (the
  largest is just under fifteen kilobytes) or, following the kernel's
  bounded-read instruction, reads only the rule's anchored section from that
  module. Corpus material is never resident by default.
- **Procedure / procedure + safety.** The most expensive paths. Procedure
  authoring pulls in the procedure and action-shaping surfaces; safety-critical
  procedure authoring adds the safety reference on top. Even the heaviest path
  stays well inside a normal working context.

These are single-tokenizer measurements, not a contract. The kernel and
always-on surfaces are additionally regenerated and checked mechanically
(`tools/gen_always_on.py --check`), so their content, and the caps above, cannot
drift silently.

## Enforcement reality

The rule registry carries two adjacent fields that are easy to conflate, so the
distinction is stated plainly here.

- **`enforcement.kind` is the *intended* mechanism.** It records how a rule
  *would* be enforced by a mechanical checker: what class of check applies, what
  it would key on. It is a design declaration.
- **`enforcement.status` is the *shipped* truth.** It records what runs
  today: **fourteen rules are callable**; the bulk of the remainder are planned,
  and the rest fall back to model review. The exact callable set is derived
  bidirectionally from the runtime's own `IMPLEMENTED_VALIDATORS` constant by
  `tests/test_enforcement_status.py`, so the registry can neither overclaim nor
  underclaim a validator.

Read together: the majority of rules are *not* mechanically enforced in this
release. Fourteen rules have callable checkers, and each callable checker runs
only where its owning rule is active: the profile resolver gates the
controlled-family checks (semicolon, contraction, Latin abbreviations, the two
sentence caps) behind `controlled-technical-guided`, exactly as the registry's
activation predicates declare. The planned rules have a specified mechanism that
is not implemented. Review-fallback is judgement, not verification.

The prose linters are **advisory / report-only**. `runtime/lint_prose.py` reports
findings and exits zero by design; it is wired into CI as a smoke invocation, not
as a gate. Nothing in this repository fails a build because prose violated a
style rule. Where a prose property genuinely must hold, it is enforced by a real
test (see `tests/test_count_leak.py`), not by the linter.

This is a deliberate v0.1 position, not an oversight: shipping a checker that
silently under-detects is worse than declaring the gap. `enforcement.status` is
the field to trust, and `tests/test_enforcement_status.py` keeps it honest.

## End-to-end reality

What is proven here, and what is not:

**Proven.** The install property is a real, gated, model-free end-to-end check.
`tests/test_install_smoke.py` builds the artifact, extracts it to a throwaway
directory, and drives the shipped runtime from the extracted tree with the
repository root off `sys.path` -- asserting extract shape, byte fidelity, import
closure, and validator accept/reject behaviour from the installed location. It
runs in CI as a hard gate. A package that would not work on a fresh install fails
the build.

**Evidenced on one host, not proven universally.** The repository includes a
non-hermetic enabled-versus-disabled evaluation harness: `tools/ab_eval_runner.py`
with the fixed prompts, frozen rubric, and mechanical validators under
`tests/evals/ab/`, documented in `docs/FUNCTIONAL-EVIDENCE.md`. It runs the
shipped package against a live host model in an enabled arm and a disabled arm,
grades the outputs with the packaged validators and blind reviewers, and records
the deltas. This supplies useful single-host evidence for two properties the
hermetic suite cannot reach:

- **Auto-selection** -- that a model presented with a given task activates STOW
  and routes to the correct reference or corpus module. The evaluation observed
  the skill auto-selecting and loading the kernel-predicted references on the
  measured host; the activation cues' structure is also tested hermetically.
- **Live reference-loading behaviour** -- that the load paths described above are
  the paths a model takes at runtime. The evaluation recorded per-file read
  telemetry on the measured host.

What the harness does not establish is universal cross-host behaviour. It ran on
one pinned host model per round, invocation is telemetry rather than forced, and
the evaluators share a model family with the generators, so the result is a set
of deltas on a single host, not a guarantee that every model and harness behaves
the same way. The behavioural and adversarial eval files in `tests/evals/` remain
authored expectations and fixtures that pin intended behaviour and catch
regressions in the authored material; on their own they are not live-model
evidence.

## Cross-harness scope

The interoperability claim is scoped to what ships. The **meta-code
surface** -- `skills/stow/schemas/*.schema.json`, `skills/stow/templates/*`, the
meta-code reference set, and `runtime/validate.py --schema <id>` -- is concrete,
committed, and tested. Any agent or harness that can read a JSON Schema and a
template can consume it, and the validator is a standalone script with no
dependency on this repository's layout. That much is real.

**Broader multi-harness interop is roadmap, not shipped.** Nothing here has been
exercised against a second harness. Claims beyond "the artefacts are portable and
the validator runs standalone" -- negotiated handoffs, cross-harness state
continuity, live agent-to-agent exchange -- describe an intended direction. The
templates for those flows exist and validate against their schemas; the flows
themselves are untested across harnesses.

## Profile resolution

One shipped data file, `skills/stow/rules/profiles.json`, declares every
profile: id, aliases, lock state, auto-activation contexts, the registry
selector for its included rules, its review-level guidance rules, and the map
of profile-gated lint checks. One shipped module, `runtime/profiles.py`,
resolves names (alias-aware, lock-refusing) and answers "does this check run
under this profile". Every consumer -- the linter, the generators, the kernel's
activation map, and the tests -- reads the same declaration, which ends the
earlier state where profile semantics were re-encoded independently across a
dozen surfaces and the runtime honored the gate for only one of the four
profile-band checks it implemented.

The activation contract the resolver enforces: the always-on families
(action-shaping and unconditional prose-integrity) govern every editable prose
turn under every profile; the controlled-technical families bind only under
`controlled-technical-guided`; `technical-clarity` adds review-level guidance
without changing the mechanical check set; `controlled-technical-strict` is
locked and refuses resolution. A drift test asserts the resolver's
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

`tools/measure_context.py` records its measurement method in every output and
never performs a network request. When the `o200k_base` encoding is already in
a local tiktoken cache directory it reports exact counts; otherwise it falls
back to a deterministic conservative estimate, `ceil(chars / 3.5)`, which
over-counted every shipped file it was calibrated on (by 8-38%), so a hard
ceiling that passes in estimate mode also holds in exact tokens. Band-style
targets (two-sided) are evaluated only in exact mode; the offline gates in
`tests/test_offline_measurement.py` prove the fallback's determinism and prove
a fully offline run completes with the ceilings still enforced. CI restores a
named tokenizer cache and warms it in a single named step whose failure
is tolerated because the estimator covers every gate.
