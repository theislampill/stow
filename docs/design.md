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

## Context budgets and load paths

STOW is built so that the cost of a turn tracks what the turn actually needs. The
kernel is the only surface that is always resident; everything else is pulled in
on demand. The figures below are token measurements taken with
`tools/measure_context.py` (tokenizer `o200k_base`); other models tokenize
differently, so treat them as a calibrated proxy and leave headroom.

| Load path | Budget (tokens) | What is resident |
| --- | --- | --- |
| Kernel alone | 993 | `SKILL.md` only |
| Ordinary prose turn | 2325 | kernel + `references/always-on.md` (ids, conditions, exceptions, and the request-mode router included -- a deliberate, measured cost over the bare-title form it replaced) |
| Technical-clarity turn | 2827 | the ordinary turn + `references/technical-clarity.md` |
| Raw JSON artifact | 2854 | kernel + `references/format-json.md` + `references/protected-regions.md` |
| Deep corpus (one module) | ~1100 | kernel + the routed corpus module (varies by module) |
| Procedure load path | 6021 | the ordinary turn + procedure authoring surfaces |
| Procedure + safety | 6766 | the procedure load path + `references/safety-instructions.md` |

These figures are point-in-time measurements; regenerate them with
`tools/measure_context.py` after any kernel, always-on, or reference change.
The test suite pins the kernel ceiling and the always-on and ordinary-turn caps
in both measurement modes (exact tokenizer and conservative estimate).

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
- **Deep corpus.** When a specific rule needs its full text, worked examples, or
  baseline, exactly one corpus module is routed in on top of the kernel. Corpus
  material is never resident by default.
- **Procedure / procedure + safety.** The most expensive paths. Procedure
  authoring pulls in the procedure and action-shaping surfaces; safety-critical
  procedure authoring adds the safety reference on top. Even the heaviest path
  stays well inside a normal working context.

Two caveats on these numbers. First, they are single-tokenizer measurements, not
a contract. Second, the kernel and always-on figures are regenerated and checked
mechanically (`tools/gen_always_on.py --check`), whereas the composite profile
figures are point measurements of a load path, not a gated invariant -- if the
underlying references grow, the composite figures drift until someone re-measures.

## Enforcement reality

The rule registry carries two adjacent fields that are easy to conflate, so the
distinction is stated plainly here.

- **`enforcement.kind` is the *intended* mechanism.** It records how a rule
  *would* be enforced by a mechanical checker: what class of check applies, what
  it would key on. It is a design declaration.
- **`enforcement.status` is the *shipped* truth.** It records what actually runs
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

What is actually proven here, and what is not:

**Proven.** The install property is a real, gated, model-free end-to-end check.
`tests/test_install_smoke.py` builds the artifact, extracts it to a throwaway
directory, and drives the shipped runtime from the extracted tree with the
repository root off `sys.path` -- asserting extract shape, byte fidelity, import
closure, and validator accept/reject behaviour from the installed location. It
runs in CI as a hard gate. A package that would not work on a fresh install fails
the build.

**Unproven.** There is **no live-model harness in this repository.** Nothing here
executes a model against the shipped skill. Two properties therefore remain
**unverified claims, and are stated as such rather than asserted**:

- **Auto-selection** -- that a model presented with a given task will actually
  activate STOW, and will route to the correct reference or corpus module. The
  activation cues are authored and their *structure* is tested; their *effect* on
  a live model is not.
- **Live reference-loading behaviour** -- that the load paths described above are
  the paths a model actually takes at runtime. The budgets are measured over the
  file set each path *should* pull in; that the model pulls in exactly that set is
  not observed anywhere in this suite.

The behavioural and adversarial eval files in `tests/evals/` are authored
expectations and fixtures. They pin intended behaviour and catch regressions in
the authored material. They are not evidence that a live model behaves that way.
Closing this gap requires a model-in-the-loop harness, which is roadmap.

## Cross-harness scope

The interoperability claim is scoped to what actually ships. The **meta-code
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
named tokenizer cache and warms it in a single clearly named step whose failure
is tolerated because the estimator covers every gate.
