# STOW

STOW is a writing-discipline skill that governs what a model *emits*. It treats every reply as a set of typed regions (prose, procedure, structured data, code, quotes, identifiers) and applies a fixed rule set so each region stays correct for what it is.

## What STOW governs

STOW governs three things:

1. **User-facing output.** The prose, procedures, explanations, and answers a model returns to a person. Result first, no filler, no fabricated specificity, stable terminology, errors reported as cause, effect, and correction.
2. **Agent-to-agent meta-code.** The coordination artifacts actors write *about* the work rather than as the work: handoffs, plans, audits, runbooks, state records, task packets, event streams, and the interchange envelope that carries them between a user, an agent, a model, and a harness. These are governed by schemas and templates, not by taste.
3. **Structured control artifacts.** The JSON, JSONL, and YAML payloads that pass between tools and agents, held to a parse-and-validate contract before delivery.

**Executable source code is protected by default and is not the primary target.** Code, commands, paths, identifiers, quoted text, and data values are *protected literals*: they pass through byte-for-byte unchanged. No prose rule may enter a code region and no formatting rule may rewrite an identifier. If you install STOW expecting it to restyle your source code, it will not, by design.

STOW is self-contained. It ships as a single skill with its own rule registry, runtime validators, schemas, templates, references, and corpus. Nothing in the packaged skill points outward at the material the rules were distilled from.

## Install

The built artifact `dist/STOW.skill` is a spec-compliant ZIP whose single top-level directory is `stow/`. Any standard unzip reads it. Install it into a host's skills directory so the skill resolves at `<skills-dir>/stow/SKILL.md`.

### Build the artifact

```
python tools/build_skill.py
```

This writes `dist/STOW.skill`, a `.sha256` sidecar, and `dist/manifest.json` listing every packaged entry. The build is deterministic: two clean builds of the same tree produce the same bytes. Tests, caches, and repository tooling are excluded; only the skill payload ships.

### Install into a skills directory

POSIX shell:

```
mkdir -p ~/.claude/skills
unzip -o dist/STOW.skill -d ~/.claude/skills
```

Windows PowerShell (`Expand-Archive` wants a `.zip` suffix):

```
Copy-Item dist\STOW.skill dist\STOW.zip -Force
Expand-Archive -Path dist\STOW.zip -DestinationPath "$HOME\.claude\skills" -Force
```

Either route yields `~/.claude/skills/stow/SKILL.md` plus `references/`, `corpus/`, `rules/`, `runtime/`, `schemas/`, and `templates/` beside it.

### Install as a plugin

The repository root ships `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, a single-plugin marketplace whose source is the repository root. Point a host that consumes plugin marketplaces at this repository to install STOW that way instead of unzipping by hand.

### Verify the install

Run the validator that shipped inside the artifact, from the installed path:

```
python ~/.claude/skills/stow/runtime/validate.py --format json some-file.json
```

A clean install prints `VALID (json): some-file.json` and exits 0. The runtime never imports from the repository, so it runs from the extracted tree with nothing else on the import path. `lint_prose.py` and `profiles.py` are standard-library only; `validate.py` additionally needs two ordinary packages on the host: `pip install ruamel.yaml jsonschema` (on Python 3.11, `jsonschema` also pulls `referencing` and `typing_extensions` transitively).

## Two-minute quick start

1. Build and install the artifact with the commands above.
2. Confirm the skill is present: `ls ~/.claude/skills/stow/SKILL.md`.
3. Ask the host any ordinary question. The kernel loads on that turn, classifies the reply into regions, and applies the always-on checks to the prose. You should see the answer first, no preamble, no closing pleasantry, and no invented figures.
4. Ask for a raw artifact: *"Return only the JSON, no fence, no commentary."* The output contract outranks presentation, so you get the bare artifact.
5. Validate a structured file end to end:

```
python skills/stow/runtime/validate.py --format json tests/fixtures/json/valid.json
python skills/stow/runtime/validate.py --format json tests/fixtures/json/dup_key.json
```

The first prints `VALID` and exits 0. The second exits 1 with `JSON parse error: duplicate object key: 'a'`, which is the contract doing its job.

## Before and after

### Raw artifact contract

Ungoverned:

````
Great question! Here's the JSON you asked for:

```json
{"status": "ok"}
```

Let me know if you'd like me to adjust anything!
````

Governed:

```
{"status": "ok"}
```

The request said *raw*. A fence, a preamble, and a closer all violate the output contract, which sits near the top of the precedence order.

### Result first

Ungoverned:

```
That's a really interesting problem, and there are a few different angles
worth considering here. Let's dive in and unpack what's going on under the
hood before we get to the answer.
```

Governed:

```
The build fails because the lockfile pins a version the registry no longer
serves. Repin it, then rerun the build.
```

### Protected literals

Ungoverned (an identifier "tidied" while explaining it):

```
Call the getUserData() helper, or as it's more properly written,
get_user_data().
```

Governed:

```
Call getUserData(). It returns the cached record.
```

The identifier is a protected literal. Presentation never edits it.

### Completeness over convenience

Ungoverned:

```
The supported formats are JSON, YAML, and a few others.
```

Governed:

```
The supported formats are JSON, JSONL, and YAML.
```

An exhaustive list is delivered exhaustively. "A few others" is a dropped requirement, not a stylistic choice.

## How always-on behavior works

Always-on is an *invocation* policy, not a load-everything policy.

- The **kernel** (`skills/stow/SKILL.md`) loads on every turn.
- Any user-facing **prose** turn additionally routes to `skills/stow/references/always-on.md`, the operational checks distilled from the always-on rule families. Each check carries its rule id, its applicability condition, and its principal exception, so a conditional rule is never presented as an unconditional imperative. The module opens with a **request-mode router**: an informational question leads with the answer, an actionable task with the next bounded action, completed work with the result and no invented follow-up, a raw artifact with the raw artifact alone.
- **Raw JSON, JSONL, YAML, and code artifacts load none of the always-on checks.** Protected regions are excluded by construction, so a raw artifact turn stays at kernel cost.
- Every other reference loads only when its named predicate is true. A YAML contract pulls the YAML reference and nothing else. A rule audit pulls the rule index and the one cited corpus module.

Measure the current footprints with `python tools/measure_context.py skills/stow/SKILL.md` (and any other file); the tool records its measurement method in the output. With a locally cached tokenizer it reports exact `o200k_base` counts; without one it reports a deterministic conservative estimate and never downloads anything. The kernel is held under a hard ceiling of 1500 tokens in both modes, and the test suite pins the kernel, always-on, and combined ordinary-turn budgets. Other models tokenize differently, so leave headroom.

## Profiles

Profiles are declared in one shipped data file, `skills/stow/rules/profiles.json`, and resolved by one shipped module, `runtime/profiles.py`. The kernel's activation map, the prose linter, the generators, and the tests all consume the same declaration, so a profile cannot mean different things on different surfaces.

| Profile | Status | What it does |
|---|---|---|
| `stow-default` | Active by default for editable prose | Always-on integrity and user-facing output governance. Imposes no controlled punctuation, contraction, vocabulary, or sentence-length rules. |
| `technical-clarity` | Auto-active for technical and coordination prose | **Mechanical checks identical to `stow-default` by design.** Adds review-level terminology and wording-consistency guidance, stable names, bounded steps, explicit conditions, and evidence-aware claims; meta-code artifacts bind here; the linter tags its output with the profile and the guidance rules. See `references/technical-clarity.md`. |
| `controlled-technical-guided` | Auto-active for executable procedures and safety instructions, or on request (alias: `controlled-technical`) | Applies the controlled-technical rule families as *guidance*: the semicolon, contraction, Latin-abbreviation, and sentence-length checks activate. Dictionary-dependent checks are reported as unavailable. |
| `controlled-technical-strict` | **LOCKED** | Full conformance to the controlled-technical writing standard. Not shipped and **must never be claimed**. Selecting it on the linter exits with an error naming the lock. |

When more than one profile matches, the declared auto-precedence decides: `controlled-technical-guided` over `technical-clarity` over `stow-default`. Punctuation across profiles: the em dash is banned in editable prose under every profile; the semicolon and contractions are permitted (never required) under `stow-default` and `technical-clarity` and prohibited under `controlled-technical-guided`, where the substitute for either banned character is a period, comma, colon, or two sentences.

The strict profile is locked because the inputs it needs (the controlled dictionary, the approved terminology set, the official directives, and the full validation suite) are out of scope for this release. STOW therefore reports *guided, partial* alignment and names which checks ran and which did not. Any statement that output fully conforms to the controlled-technical writing standard is an overclaim the conformance reference explicitly forbids. See `skills/stow/references/conformance.md`.

Cross-rule collisions (a banned character's substitute, a cap against a contract-required exhaustive list, hedging against justified uncertainty, and the rest) are declared in `skills/stow/rules/conflicts.yaml`, each with a winner, the losing behavior, the permitted substitute, and fixtures; `docs/rule-conflicts.md` is generated from it.

## Meta-code

The meta-code layer governs artifacts one actor writes to another about the work. Eight schema files ship under `skills/stow/schemas/`; the first five are the interchange meta-contracts recorded in the registry catalog, and the last three are validator schemas for the remaining template classes:

| Schema id | Artifact |
|---|---|
| `output-contract` | Output contract / cross-harness interchange envelope |
| `handoff` | Control transfer between actors |
| `task-packet` | Machine-readable payload dispatched to and returned by a subagent |
| `evidence-record` | Claim plus resolvable locator |
| `state` | Durable continuity record |
| `event` | One event-stream line (validated per line over a `.jsonl` stream) |
| `plan` | Implementation-plan task DAG |
| `runbook` | Operator step list with verify/rollback per step |

Seven authoring templates ship under `skills/stow/templates/`: `HANDOFF.md`, `PLAN.md`, `AUDIT.md`, `RUNBOOK.md`, `STATE.md`, `task-packet.yaml`, and `event-stream.jsonl`. **Every template validates against its schema through the shipped validator**, and the test suite enforces that property, so the worked examples cannot drift from their contracts. Instances carry an optional `schema_version` (currently 1; evolution is additive-only within a version) and an optional `profile` binding; meta-code artifacts bind to `technical-clarity`, and an executable procedure or safety instruction promotes to `controlled-technical-guided`. Status vocabularies are closed cores with an `x-` prefix escape, because the executing harness owns lifecycle semantics and STOW owns only the representation.

### Use cases

- **Control transfer.** Agent A finishes a phase and hands to agent B. The handoff states what is done with evidence pointers, what is not done, the binding constraints, and the single next action. B needs no transcript history to act.
- **Dispatch and return.** An orchestrator sends a task packet carrying the goal, inputs, permissions, expected output, and acceptance predicates. The subagent fills the return block with a status and one evidence entry per acceptance predicate.
- **Cross-harness contract stability.** The interchange envelope carries a payload between harnesses whose prose conventions differ, with the payload's identifiers and values preserved exactly across the hop.
- **Audit trails.** An evidence record binds a claim to a locator that a reader can resolve independently, so a finding survives the session that produced it.

The acceptance test for the whole layer is the **cold-reader rule**: every field a fresh reader needs is carried in the artifact, and nothing depends on transcript state the artifact does not itself state.

### Validate a meta-code artifact

```
python skills/stow/runtime/validate.py --schema handoff tests/fixtures/meta/handoff.json
```

```
VALID (schema:handoff): tests/fixtures/meta/handoff.json
```

The `--schema` id is the bare filename stem of a file in `skills/stow/schemas/`. Path separators and dots are rejected, so the id cannot traverse out of the schema directory. Instances may be JSON, YAML, a Markdown document (its single fenced yaml/json block is the instance), or a `.jsonl` stream (validated per line, e.g. `--schema event`). An evidence-record file may wrap several records as `{records: [...]}` and validates per record.

Working instances of every schema live in `tests/fixtures/meta/`, and the shipped templates themselves are validated instances. Use either as the reference shape when authoring your own.

## Structured output contracts

**JSON.** A raw JSON artifact ships raw: no fence, no wrapper, no trailing prose. Duplicate object keys are rejected rather than silently last-wins. A leading byte-order mark, a trailing comma, and non-finite numbers (`NaN`, `Infinity`) are all invalid.

```
{"id": "TP-001", "status": "done", "evidence": ["registry.yaml"]}
```

**JSONL.** One complete value per line, one line per record, no blank lines, no fence.

```
{"ts": "2026-07-19T14:30:00Z", "actor": "orchestrator", "type": "phase_start", "phase": "build"}
{"ts": "2026-07-19T14:41:12Z", "actor": "orchestrator", "type": "phase_done", "phase": "build", "result": "ok"}
```

**YAML.** Duplicate keys are rejected, including keys that differ in spelling but resolve to the same scalar (`0x10` and `16`, `1` and `1.0`). Custom tags and aliases are flagged. Scalars that look like numbers or booleans coerce unless quoted.

```
packet_id: TP-001
status: done
evidence:
  - locator: skills/stow/rules/registry.yaml
    result: registry parses and schema-checks
```

Every fixture behind these rules is under `tests/fixtures/`, one file per failure mode.

## Validators

Two runtime tools ship inside the skill.

**`runtime/validate.py`** is the delivery gate. It has two mutually exclusive modes:

```
python skills/stow/runtime/validate.py --format {json,jsonl,yaml} <file>
python skills/stow/runtime/validate.py --schema <schema-id> <file>
```

Exit codes: `0` valid, `1` invalid (errors printed to stderr, one per line), `2` the file could not be read or is not valid UTF-8. Warnings print to stdout and do not change the exit code.

**`runtime/lint_prose.py`** is advisory and report-only. Findings never change the exit code; only an invalid invocation (an unknown or locked profile) exits nonzero.

```
python skills/stow/runtime/lint_prose.py <file> [--profile <id>] [--artifact-type prose|structured|raw] [--exhaustive-list-ok]
```

`--profile` takes any id or alias from `rules/profiles.json` (default `stow-default`); the profile decides which checks run, exactly as the registry declares — the semicolon, contraction, Latin-abbreviation, and sentence-length checks fire only under `controlled-technical-guided`. A file with a structured extension (`.json`, `.jsonl`, `.yaml`, `.yml`) is treated as a structured artifact and receives **no prose findings** (use `validate.py` on it; `--artifact-type prose` overrides the sniff for a prose file with a data extension). `--exhaustive-list-ok` records the contract's permission for a complete list and suppresses the list-length advisory. The output names the resolved profile and any review-level guidance rules it activates.

Before it scans anything it **masks** protected regions (fenced blocks, inline code spans, block quotes, and anything shaped like a URL, path, or identifier), replacing them with spaces so positions are preserved and their contents are never flagged. Only the remaining prose is scanned. The masking contract is the load-bearing behavior; the advisory set itself is deliberately small.

## Architecture

Three tiers, loaded from most general to most specific. A response is answered from the kernel alone unless a predicate calls for more.

**Kernel** (`skills/stow/SKILL.md`). The always-on core. Defines the precedence order, the region model, the integrity rules, the shape of user-facing output, and the activation map that decides when anything deeper loads.

**References** (`skills/stow/references/`). Mid-tier guidance, each file loaded only when its predicate is true: the format contracts, the procedure and description profiles, safety instructions, protected regions, conformance, the meta-code hub and its siblings, and the generated always-on checks.

**Corpus** (`skills/stow/corpus/`). One module per rule, grouped by category, carrying the full statement, rationale, and examples. Loaded last, only when a rule audit or deep application cites a specific rule.

### Precedence

Eight bands, highest to lowest: system directives, output contract, serialization, protected literals, accuracy, terminology, writing profile, user-facing presentation. The invariant is that a lower band never corrupts a higher one. Presentation never edits a literal, terminology never breaks serialization, the profile never softens a safety instruction. When two bands conflict, the higher wins and the lower yields.

### The rule registry

Every rule lives in `skills/stow/rules/registry.yaml`, which indexes 96 primary rules validated against `registry.schema.json`. Each record carries a stable id, title, category, precedence band, region scope, an activation predicate, an enforcement block, and a pointer to its corpus module. The registry is the single source of truth: the human-readable rule index, the always-on checks, and the corpus modules are all keyed to it, so a rule traces from its id to its full text and back.

## Extension and governance

**The registry is canonical.** Add or change a rule there, never in the derived surfaces.

1. Add or edit the record in `skills/stow/rules/registry.yaml`. Every field the schema requires must be present, including the enforcement block and the `corpus_ref`.
2. Write the corpus module the `corpus_ref` points at.
3. Regenerate the derived surfaces:

```
python tools/gen_rule_index.py
python tools/gen_always_on.py
python tools/gen_rule_conflicts.py
```

4. Verify nothing drifted, in this repository, before pushing:

```
python tools/gen_rule_index.py --check
python tools/check_provenance_leak.py --local
python -m pytest tests/ -q
```

`generated_counts.primary_total: 96` is an invariant asserted by the test suite. Changing it is a deliberate versioned decision, not an edit.

**Rewriting is deferred.** Rules are added and their enforcement posture is sharpened, but rewriting existing rule wording is deferred to a governed comparative phase where a candidate wording is measured against the retained baseline before it can replace it. Until that phase runs, treat shipped rule text as fixed.

## Known limitations

Read this section before you rely on STOW for anything load-bearing.

- **Prose linters are advisory and report-only.** `lint_prose.py` always exits 0. Nothing in the toolchain mechanically blocks prose that violates a prose rule. The structured-output validator is the only hard gate.
- **Most registry rules are not callable.** Each record declares an enforcement status. Fourteen rules have callable validators today. The large majority are either *review-fallback* (a model applies them by reading them) or *planned* (the validator does not exist yet). A rule being in the registry does not mean a program checks it.
- **Lexical advisories ignore a requested register.** When a user explicitly asks for a casual or creative voice, that request governs the register (it is part of the output contract), but the linter's lexical advisories still fire on the result; advisories never override the contract band. See `CFL-015` in the conflict registry.
- **There is no live-model conformance harness.** Every behavioral claim in this document rests on **structural contracts** (schema validation, registry invariants, generated-surface drift checks, install smoke) and **fixture contracts** (detector cases with known-good and known-bad inputs). No test drives a live model and grades its output. Treat the before-and-after examples as the specified contract, not as measured model behavior.
- **The strict profile is locked** and must never be claimed. See Profiles above.
- **The full anti-leak gate runs locally, not in CI.** The strong mode needs a private pattern file that is deliberately not committed. Continuous integration runs a weaker heuristic backstop. The authoritative gate is `python tools/check_provenance_leak.py --local`, and it must be green before pushing.
- **The checked-in `dist/STOW.skill` is machine-checked against the tree.** A test rebuilds the artifact and fails when the committed archive, checksum sidecar, or manifest differs from a fresh build, so a stale committed artifact cannot pass the suite.

## Roadmap

- Promote review-fallback rules to callable validators, starting with the ones whose checks are purely structural.
- Add a repeatable live-model evaluation suite (host-native, with a with/without-skill comparison arm) so behavioral claims rest on measured output rather than fixtures alone.
- Import the controlled dictionary and the approved terminology set, which is the precondition for unlocking the strict profile.
- Run the governed comparative rewrite phase for rule wording.
- Widen the meta-code schema catalog as new coordination artifact classes prove out.

## Troubleshooting

**The skill never seems to activate.** Confirm the layout is `<skills-dir>/stow/SKILL.md`, with `stow/` as a directory directly inside the skills directory. A common failure is unzipping into a nested folder, which yields `<skills-dir>/STOW/stow/SKILL.md` and does not resolve.

**The validator rejects JSON that looks fine.** Check, in order: a leading byte-order mark, a duplicate object key, a trailing comma, a `NaN` or `Infinity` literal, or a code fence that was pasted in with the content. Each has a fixture under `tests/fixtures/json/` reproducing it in isolation.

**YAML values changed type.** Unquoted scalars coerce. `no` becomes a boolean, `1.0` becomes a float, `0x10` becomes an integer. Quote any scalar whose string form matters. Two keys that coerce to the same scalar are a duplicate-key error even when spelled differently.

**`--schema` says the schema is unknown.** The id is a bare filename stem, not a path and not a filename. Use `handoff`, not `handoff.schema.json` and not `schemas/handoff.schema.json`.

**STOW edited my source code.** It should not. Code is a protected literal that passes through unchanged. If a code region was altered, that is a precedence violation worth reporting, not intended behavior.

**A generated file keeps coming back changed.** `references/rule-index.md` and `references/always-on.md` are generated from the registry, and `docs/rule-conflicts.md` from the conflict registry. Edit the source and regenerate; do not hand-edit a generated file.

## Repository layout

```
skills/stow/
  SKILL.md              kernel: precedence, region model, integrity rules
  references/           mid-tier guidance, loaded by predicate
  corpus/               one module per rule, grouped by category
  rules/registry.yaml   the rule registry (96 rules) and its schema
  runtime/              validators and prose lint used before delivery
  schemas/              meta-code artifact schemas
  templates/            meta-code authoring templates
docs/                   design notes, evaluation results, rule conflicts
tests/                  test suite, evals, and fixtures
tools/                  build, generation, and check tooling
dist/                   built artifact, checksum, and entry manifest
```
