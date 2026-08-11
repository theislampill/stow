# STOW

STOW is a writing-discipline specification and packaged skill. When a host selects it, the guidance helps a model distinguish prose, procedures, structured data, code, quotations, and identifiers. Callable checkers decide only their closed input contracts; STOW does not universally control a model's final response.

## STOW in one minute

- **What it does.** When a host invokes STOW, the compact kernel supplies region and precedence guidance. Named predicates tell the model or host which cold reference is relevant; the repository does not contain a semantic request classifier that performs those reads automatically.
- **What it covers.** The guidance addresses user-facing prose, coordination artifacts, and structured payloads. Separate callable checkers cover specific parse, schema, term-map, and advisory prose contracts.
- **What it protects.** The generation guidance tells the writer not to alter supplied code, commands, paths, identifiers, quotations, or data values unless editing that literal is the task. The advisory linter masks a finite recognizable subset while scanning; STOW has no general final-output byte comparator.
- **How ordinary guidance works.** For editable user-facing prose, the activation map points to `references/always-on.md`. Its rule identifiers, applicability conditions, exceptions, and request-mode router remain instructions that a model or host must apply.
- **How profiles work.** `profiles.py` resolves an explicitly supplied identifier or defaults a missing identifier to `stow-default`; it does not infer a profile from request meaning. The `auto_contexts` and precedence data are routing cues for a model or host.
- **How meta-code fits.** Coordination artifacts have schemas and templates. `validate.py` can check a supplied instance, while any repair, recheck, and delivery decision belongs to the caller or host workflow.

## Measured operationalisation

STOW turns a model-memory cue into an operational workflow. In a
crosswalk-derived controlled-language benchmark using the same underlying
model, the exact candidate achieved the highest requirement-level result among
no conditioning, name-only conditioning, raw-source conditioning, and STOW.
The benchmark exposed semantic overreach in operation and force preservation;
that defect was repaired and regression-tested.

This supports more complete operationalisation on the bounded tested
requirement surface, not universal output superiority. Name-only conditioning
was cheaper in the measured trial, and cross-model durability remains unproved.

## Install

The built artifact `dist/STOW.skill` is a spec-compliant ZIP whose single top-level directory is `stow/`. Any standard unzip reads it. Install it into a host's skills directory so the skill resolves at `<skills-dir>/stow/SKILL.md`.

```
python tools/build_skill.py
mkdir -p ~/.claude/skills
unzip -o dist/STOW.skill -d ~/.claude/skills
```

Windows PowerShell (`Expand-Archive` wants a `.zip` suffix):

```
Copy-Item dist\STOW.skill dist\STOW.zip -Force
Expand-Archive -Path dist\STOW.zip -DestinationPath "$HOME\.claude\skills" -Force
```

The repository root also ships `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, so a host that consumes plugin marketplaces can install STOW by pointing at this repository instead of unzipping by hand.

Verify the install by running the packaged validator from the installed path:

```
python ~/.claude/skills/stow/runtime/validate.py --format json some-file.json
```

A clean install prints `VALID (json): some-file.json` and exits 0. The runtime never imports from the repository. `lint_prose.py`, `profiles.py`, `validate_terms.py`, and `dictionary_lookup.py` are standard-library only; `validate.py` additionally needs two ordinary packages on the host: `pip install ruamel.yaml jsonschema` (on Python 3.11, `jsonschema` also pulls `referencing` and `typing_extensions` transitively).

## Profiles at a glance

Profiles are declared in one shipped data file, `skills/stow/rules/profiles.json`, and resolved by one shipped module, `runtime/profiles.py`. The kernel's activation map, the prose linter, the generators, and the tests all consume the same declaration.

| Profile | Status | What it does |
|---|---|---|
| `stow-default` | Resolver default when the caller supplies no id | General integrity and user-facing output guidance. Imposes no controlled punctuation, contraction, vocabulary, or sentence-length rules. |
| `technical-clarity` | Available explicitly; routing cues name technical and coordination prose | **Mechanical checks identical to `stow-default` by design.** Adds review-level terminology and wording-consistency guidance, stable names, bounded steps, explicit conditions, and evidence-aware claims; the linter tags its output with the profile. See `references/technical-clarity.md`. |
| `controlled-technical-guided` | Available explicitly; routing cues name procedures and safety instructions (alias: `controlled-technical`) | Applies the available controlled-technical rule families as guidance: the semicolon, contraction, Latin-abbreviation, and sentence-length checks activate. A cold sparse dictionary lookup reports membership, alternatives, and listed forms without deciding sense or project terminology. |
| `controlled-technical-strict` | **LOCKED** | Full conformance to the controlled-technical writing profile. Not shipped and **must never be claimed**. Selecting it on the linter exits with an error naming the lock. |

Raw and protected artifacts are their own declared mode, not a profile. The guidance says to omit prose checks for raw JSON, JSONL, YAML, code, quotations, identifiers, commands, and paths. A host must identify the mode and retain custody of the candidate; the resolver does neither.

When a model or host finds more than one routing cue applicable, the declared precedence is `controlled-technical-guided` over `technical-clarity` over `stow-default`. For an explicitly resolved profile, the em-dash advisory runs for editable prose under every profile; the semicolon and contraction advisories are off under `stow-default` and `technical-clarity` and on under `controlled-technical-guided`.

The strict profile remains locked. The bundled dictionary lookup establishes only closed membership and listed-form facts. Full conformance also needs contextual meaning and part-of-speech decisions, approved project terminology, applicability, validation of the actual final output, and delivery custody. STOW reports guided, partial alignment and names which checks ran and which did not. Any claim of full conformance is an overclaim the conformance reference explicitly forbids.

## Rule classes at a glance

The current registry indexes 65 primary rules under STOW's own functional
taxonomy. The registry defines each active rule's operational metadata; the
audit ledger preserves the original reconciliation population and retired IDs.

<!-- RULE-CLASSES:BEGIN -->

| Rule class | What it governs |
|---|---|
| Action and task shaping | How a reply opens, closes, tracks progress, and stays actionable. |
| Prose integrity | No filler, no fabricated specificity, no synthetic voice. |
| Words and terminology | Word choice and consistent naming under the controlled profile. |
| Multi-word nouns | Length and clarity limits for noun clusters. |
| Verbs and voice | Verb forms, tense, and the active voice. |
| Sentences and paragraphs | Sentence completeness, length discipline, and paragraph focus. |
| Procedures | Instruction shape and sentence limits for executable steps. |
| Descriptive writing | Structure and length discipline for explanatory text. |
| Safety instructions | Complete, correctly formed warnings, cautions, and notes. |
| Punctuation and word counting | Punctuation limits and how words are counted against caps. |
| Writing style | Rewriting guidance when a word-for-word fix is not enough. |
| General writing practice | Cross-cutting recommendations for controlled technical text. |
<!-- RULE-CLASSES:END -->

## The complete primary-rule catalog

Every primary rule, exactly once, grouped by rule class. The one-sentence summaries are navigational, not authoritative: the registry (`skills/stow/rules/registry.yaml`) defines operational metadata, and each rule's corpus module carries the full statement, qualifications, and examples. Expand a class to see its rules.

Status meanings: **Callable** means a shipped validator checks it mechanically. **Planned** means the mechanism is specified but not implemented. **Review-fallback** means a model applies it by reading it; no program checks it.

<!-- CATALOG:BEGIN -->

<details>
<summary><b>Action and task shaping</b> (ACT-001 through ACT-011)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-ACT-001` | Action-first response opening | the request is an actionable task; exception: an informational request leads with the answer, per the request-mode router | Planned |
| `STOW-ACT-002` | Numbered steps for multi-step work | the work runs across multiple steps | Planned |
| `STOW-ACT-004` | Defer secondary issues | a secondary issue surfaces during the main task; exception: offer the deferred issue separately at the end rather than dropping it | Planned |
| `STOW-ACT-005` | Restate progress each turn | a multi-turn task is in progress; exception: a single-turn answer needs no progress ledger | Review-fallback |
| `STOW-ACT-006` | Concrete effort estimates | a defensible range exists for the estimate; exception: with no defensible range, omit the figure; accuracy outranks the preference | Review-fallback |
| `STOW-ACT-007` | Surface completed outcomes | work ran and produced a result this turn | Planned |
| `STOW-ACT-008` | Neutral error reporting | the turn reports an error | Planned |
| `STOW-ACT-011` | Lists, not tables, for action sequences | action sequences, not comparison data | Planned |

</details>

<details>
<summary><b>Prose integrity</b> (PRO-001 through PRO-023)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-PRO-001` | Use em dashes only under an explicit style contract | an explicit style contract governs punctuation; exception: a deliberate house style that permits em dashes remains permitted | Review-fallback |
| `STOW-PRO-002` | Require attributable numbers | any numeric claim; exception: no attributable source: omit the number rather than invent one | Review-fallback |
| `STOW-PRO-005` | End claims on a concrete detail | factual claims in editable prose; exception: a conceptual definition satisfies this with a precise, checkable statement | Review-fallback |
| `STOW-PRO-006` | Functionless semantic repetition | a later statement repeats an earlier meaning without adding function; exception: functional repetition for correction, safety, navigation, emphasis, or stable terminology remains permitted | Review-fallback |
| `STOW-PRO-007` | Avoid mechanical repetition that obscures function | consecutive repeated structures obscure the function of the content; exception: preserve deliberate parallelism, recurring terminology, house style, and required layouts | Planned |
| `STOW-PRO-009` | Use urgency or intensified emphasis only when a decision-relevant reason is stated | urgency or intensified emphasis lacks a decision-relevant reason; exception: preserve a supported deadline-led command or requested functional emphasis | Review-fallback |
| `STOW-PRO-011` | Remove framing or process language only when it adds no information or decision value | framing or process language adds no information or decision value; exception: preserve a material limitation, method, audience, progress state, or requested voice | Review-fallback |
| `STOW-PRO-013` | Evidence-grounded requested voice | the response uses the default or explicitly requested voice; exception: the requested voice governs while factual claims remain evidence-grounded | Review-fallback |
| `STOW-PRO-015` | Grounded uncertainty | uncertainty appears without an evidence boundary; exception: justified uncertainty and bounded capability statements remain permitted | Review-fallback |
| `STOW-PRO-016` | Concrete, descriptive headings | Section headings | Planned |
| `STOW-PRO-017` | No fabricated scenarios | All prose (always on) | Review-fallback |
| `STOW-PRO-018` | No fabricated history | All prose (always on) | Review-fallback |
| `STOW-PRO-019` | No fabricated attributions | All prose (always on) | Review-fallback |
| `STOW-PRO-020` | Review formulaic lexical patterns | a listed pattern or corrective contrast may obscure its function or reject a characterization absent from the discourse; exception: ordinary connectors, technical uses, and a discourse-present correction naming the real differentiator remain permitted | Review-fallback |
| `STOW-PRO-023` | Quote sources accurately | Quoted sources | Review-fallback |

</details>

<details>
<summary><b>Words and terminology</b> (WRD-001 through WRD-014)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-WRD-001` | Use dictionary-approved words; admit technical nouns and technical verbs only under a defined category supplied by project authority, and prefer an approved dictionary verb when one exists | controlled vocabulary is requested and dictionary or project terminology authority is available; exception: unknown technical terms require external authority and are not rejected by lexical lookup alone | Review-fallback |
| `STOW-WRD-002` | Use each approved word only in its dictionary-specified part of speech and listed forms; a listed past participle can act as an adjective | Controlled profile | Planned |
| `STOW-WRD-003` | Use approved words only with their dictionary-approved, often restricted, meanings | an approved meaning is supplied for contextual review; exception: lexical membership and listed alternatives do not establish the intended sense or an equivalent action | Review-fallback |
| `STOW-WRD-007` | Do not use a technical noun as a verb; keep it a noun or adjectival modifier | Controlled profile | Planned |
| `STOW-WRD-008` | Prefer the technical noun already approved by your company, industry, or subject field | Controlled profile | Planned |
| `STOW-WRD-010` | Do not use regional, slang, or jargon words as technical nouns | Controlled profile | Review-fallback |
| `STOW-WRD-011` | Use one technical noun consistently for one item, preserve key words and key phrases that organize the logic, and reuse recurring wording for the same context | guidance-level under the technical-clarity profile; binding under the controlled profile | Planned |
| `STOW-WRD-014` | Use American English spelling unless another official directive overrides; do not change quoted-text spelling | Controlled profile | Planned |

</details>

<details>
<summary><b>Multi-word nouns</b> (MWN-001 through MWN-001)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-MWN-001` | Keep multi-word nouns to a maximum of three words and keep coined terms short and easy; for a longer approved noun, write it in full first, then use a declared short form, approved abbreviation, or clear hyphenation | Controlled profile | Planned |

</details>

<details>
<summary><b>Verbs and voice</b> (VRB-002 through VRB-007)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-VRB-002` | Use only the infinitive, imperative, simple present, simple past, simple future, and listed past participle; do not use perfect, progressive, or other complex constructions | controlled prose requires a bounded tense or aspect choice; exception: preserve a time relation when the source or procedure requires it | Planned |
| `STOW-VRB-005` | Use an -ing word only as a technical noun or as a modifier inside a technical noun | a word ending in ing appears outside a declared technical noun; exception: project authority can classify the form as a noun term or noun modifier | Review-fallback |
| `STOW-VRB-006` | Use active voice; passive is allowed only in descriptive writing when the agent is unknown | Controlled profile | Planned |
| `STOW-VRB-007` | Describe an action with an approved verb, not a nominalization; technical verbs stay verbs, except that a listed past participle can act as an adjective | Controlled profile | Planned |

</details>

<details>
<summary><b>Sentences and paragraphs</b> (SEN-002 through SEN-005)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-SEN-002` | Do not omit words or use contractions; write every word in full | Controlled profile | Review-fallback |
| `STOW-SEN-003` | Break complex text into a vertical list with the prescribed layout | Controlled profile | Planned |
| `STOW-SEN-004` | Use approved connecting words and phrases to link related sentences | Controlled profile | Planned |
| `STOW-SEN-005` | Use articles and demonstratives before nouns where grammatically correct | Controlled profile | Planned |

</details>

<details>
<summary><b>Procedures</b> (PRC-001 through PRC-005)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-PRC-001` | Limit each procedural sentence to a maximum of twenty words | Controlled profile | Callable |
| `STOW-PRC-002` | Write only one instruction per sentence unless actions occur at the same time | Controlled profile | Planned |
| `STOW-PRC-003` | Write instructions in the imperative command form | the source already authorizes a command rather than advice or a permission statement; exception: do not silently strengthen advice, permission, or uncertainty; preserve source force or request an authority decision | Planned |
| `STOW-PRC-004` | State a required condition first and separate it from the command with a comma | Controlled profile | Planned |
| `STOW-PRC-005` | A note in a controlled procedure gives information and does not introduce an action | a note is attached to a controlled procedure; exception: a higher-precedence literal or output contract takes priority | Planned |

</details>

<details>
<summary><b>Descriptive writing</b> (DSC-001 through DSC-006)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-DSC-001` | Introduce information gradually, one subject per sentence | Controlled profile | Review-fallback |
| `STOW-DSC-003` | Limit each descriptive sentence to a maximum of twenty-five words | Controlled profile | Callable |
| `STOW-DSC-004` | Group related information into paragraphs, each led by a topic sentence | Controlled profile | Review-fallback |
| `STOW-DSC-006` | Keep every paragraph to a maximum of six sentences | Controlled profile | Planned |

</details>

<details>
<summary><b>Safety instructions</b> (SAF-001 through SAF-003)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-SAF-001` | Label each safety instruction with a word that identifies the level of risk | Safety notices | Review-fallback |
| `STOW-SAF-002` | Begin a safety instruction with a clear, accurate command or condition | Safety notices | Planned |
| `STOW-SAF-003` | State the risk or the possible result of not obeying the safety instruction | Safety notices | Review-fallback |

</details>

<details>
<summary><b>Punctuation and word counting</b> (PCT-001 through PCT-007)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-PCT-001` | Do not use the semicolon; write two separate sentences instead | Controlled profile | Callable |
| `STOW-PCT-003` | Use parentheses only for references, item identifiers, step identifiers, abbreviations, singular/plural forms, explanations, or alternatives | parentheses appear in controlled prose; exception: protected text and the listed parenthetical purposes remain unchanged | Planned |
| `STOW-PCT-004` | In a vertical list, a colon counts as a period for word count and ends a sentence | Controlled profile | Planned |
| `STOW-PCT-005` | Parenthetical text counts as one word in the host sentence | Controlled profile | Planned |
| `STOW-PCT-006` | Count a number, number with unit, abbreviation, identifier, quoted text, title or label, or proper name as one word | Controlled profile | Planned |
| `STOW-PCT-007` | Use hyphens only between directly related words that operate as one unit; a hyphenated group counts as one word | Controlled profile | Planned |

</details>

<details>
<summary><b>Writing style</b> (STY-001 through STY-003)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-STY-001` | When a word-for-word replacement is insufficient, rewrite the sentence while preserving the meaning | Controlled profile | Review-fallback |
| `STOW-STY-003` | Do not combine approved words into unlisted phrasal verbs | Controlled profile | Planned |

</details>

<details>
<summary><b>General writing practice</b> (GEN-002 through GEN-007)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-GEN-002` | Rewrite a with phrase only when it has two plausible attachments | a with phrase has two plausible attachments; exception: leave a clear with phrase unchanged | Planned |
| `STOW-GEN-003` | Use only approved pronouns; replace an ambiguous pronoun with its noun | Controlled profile | Planned |
| `STOW-GEN-005` | Confirm a possible false friend against a supplied source-language meaning | a source-language form or intended English meaning is supplied for controlled review; exception: do not infer a false friend from spelling resemblance alone | Review-fallback |
| `STOW-GEN-006` | Avoid Latin abbreviations; use English words instead | Controlled profile | Callable |
| `STOW-GEN-007` | When gender is unknown or irrelevant, name the role or use an inclusive reference | a human role is named and gender is unknown or irrelevant; exception: preserve gender when it is a supplied fact or materially relevant | Planned |

</details>
<!-- CATALOG:END -->

## Secondary guidance

Retained material that supports the primary rules without joining the primary count:

- **Applicability overrides.** When acting on instructions would conflict with a rule, the override order is recorded rather than improvised.
- **Pre-send gates.** Final self-checks a reply runs before delivery.
- **Foundational rationale.** Why the action-shaping rules exist: what limited attention changes about reading.
- **False-positive guidance.** When a suspicious pattern is legitimate and must not be fixed.
- **Detection and review guidance.** How to recognize synthetic prose patterns, with worked examples and a self-check pass.
- **General recommendations.** Cross-cutting writing practice under the controlled profile.

These live as corpus modules and are covered by the same drift-locks as the primary rules.

## How overlapping rules compose

Related rules reinforce each other, narrow each other, apply in only one profile, create exceptions, yield to a higher-precedence contract, or prescribe a permitted substitute. Every declared collision has a terminal resolution in the machine-readable conflict registry (`skills/stow/rules/conflicts.yaml`), from which `docs/rule-conflicts.md` is generated. These are resolved compositions, not open contradictions.

| Context | Wins | Yields | Permitted substitute or exception |
|---|---|---|---|
| Informational question vs action-first opening | The answer leads | An unrequested next action opening | Lead with the next bounded action only for actionable tasks |
| Completed work vs required next action | The result, reported plainly | An invented follow-up step | Add a next action only when open work remains |
| Justified uncertainty vs anti-hedging | Calibrated uncertainty, stated once with its reason | Empty hedge words | Cut hedges that carry no information; keep load-bearing doubt |
| Material limitation vs no process narration | One clause disclosing what changes the answer | Exploration diary | State the limitation and its consequence; omit the search story |
| Sentence variation vs controlled sentence caps | The cap | Variation above the cap | Vary length below the cap, never above it |
| Consistent terminology vs stylistic variation | One term per concept | Synonym rotation for recurring items | Vary only non-recurring content |
| Em-dash avoidance vs semicolon permissions | Profile decides the substitute | A semicolon under the controlled profile | Default and technical-clarity permit semicolons; the controlled profile replaces either character with a period, comma, colon, or two sentences |
| Contractions, default vs controlled | The active profile's rule | A contraction inside controlled output | Contractions are permitted (never required) by default and prohibited under the controlled profile |
| Prose preferences vs raw or protected artifacts | The artifact, byte-exact | Any prose rule entering the region | Prose checks never load inside protected regions |
| Brevity vs safety completeness | Complete safety content, unshortened | Truncating hazards to fit a cap | Brevity shaping applies to everything except safety text |
| User-requested voice vs default register | The requested register | The default researcher tone | Accuracy and fabrication rules still apply to the requested voice |

## Functional examples

Short before/after pairs. Ungoverned halves are deliberately non-conforming; governed halves follow the shipped rules and, where marked, validate against the shipped runtime.

**Ordinary answer.** Ungoverned:

```
Great question! There are several angles worth unpacking here before we
get to the answer itself.
```

Governed:

```
The build fails because the lockfile pins a version the registry no longer
serves. Repin it, then rerun the build.
```

**Actionable task.** Governed replies lead with the next bounded action:

```
1. Revoke the leaked key in the provider console.
2. Issue a replacement key and store it in the secret manager.
3. Roll the deployment so every instance reads the new key.
```

**Completed task.** No invented follow-up:

```
The migration finished and all twelve checks pass. Nothing is left open.
```

**Justified uncertainty.** Kept, with its reason:

```
The fix removes the deadlock in every reproduction we have. The race window
under sustained load is untested; treat that path as unverified.
```

**Raw JSON.** The request said raw, so the artifact ships raw:

<!-- validate:json -->
```
{"service": "api", "status": "ok"}
```

**Technical procedure** (controlled profile: short imperative steps, no semicolons, no contractions):

```
1. Stop the host writes.
2. Replace the failed drive.
3. Start the rebuild from the controller menu.
```

**Agent handoff.** A machine-readable block that validates against the handoff schema ships inside the artifact; see `skills/stow/templates/HANDOFF.md` for the complete worked example, which the test suite validates through the real CLI.

**Validate-repair-revalidate.** The documented flow for any generated structured artifact:

```
python skills/stow/runtime/validate.py --schema handoff my-handoff.md
# fix each reported field
python skills/stow/runtime/validate.py --schema handoff my-handoff.md
```

The first run reports the violations its closed contract detects; the loop ends when the actual candidate prints `VALID`.

## Validators

**`runtime/validate.py`** is a G2 parser and schema detector with two mutually exclusive modes:

```
python skills/stow/runtime/validate.py --format {json,jsonl,yaml} <file>
python skills/stow/runtime/validate.py --schema <schema-id> <file>
```

Exit codes: `0` valid, `1` invalid (errors printed to stderr, one per line), `2` the file could not be read or is not valid UTF-8. An instance is JSON, YAML, a Markdown document (its single fenced yaml/json block is the instance), or a `.jsonl` stream validated per line. An evidence-record file can wrap several records as `{records: [...]}` and validates per record. Working instances of every schema live in `tests/fixtures/meta/`, and the shipped templates themselves are validated instances.

**`runtime/lint_prose.py`** is advisory and report-only. Findings never change the exit code; only an invalid invocation (an unknown or locked profile) exits nonzero.

```
python skills/stow/runtime/lint_prose.py <file> [--profile <id>] [--artifact-type prose|structured|raw]
```

The caller-supplied profile decides which checks run, exactly as the registry declares. A file with a structured extension receives no prose findings (use `validate.py` on it). Before scanning, the linter masks its finite recognized set of fenced blocks, inline code, block quotes, URLs, paths, and identifiers. Findings and zero findings remain advisory.

**`runtime/validate_terms.py`** is a G2 detector for an explicit closed term map and caller-labeled editable or protected segments. It cannot establish that those labels are semantically correct.

`runtime/validate.py` and `runtime/validate_terms.py` are G2 detectors, not delivery gates by themselves. A G3 host workflow must hold the actual final candidate, block invalid and unknown results, permit only authorized repairs, and revalidate before delivery.

**`runtime/query_rules.py`** is a packaged, standard-library-only lookup helper. Given a rule id it prints the registry record, the profiles that include the rule (by selector, category prefix, or guidance list), the per-record and composition conflicts that name it, and the anchored corpus section.

```
python skills/stow/runtime/query_rules.py STOW-PCT-006
```

It is an acceleration for manual rule lookups; no kernel path depends on it, and plain file reads remain the contract path.

## Architecture

Three tiers are available from most general to most specific. The kernel tells the model or host to use a cold reference only when its predicate applies; file presence does not prove a live read.

- **Kernel** (`skills/stow/SKILL.md`): precedence, the region model, the integrity rules, and the activation map.
- **References** (`skills/stow/references/`): cold mid-tier guidance, each with a named predicate.
- **Corpus** (`skills/stow/corpus/`): grouped conceptual modules holding the full guidance, where every rule is addressable through a stable `## STOW-XXX-NNN` heading anchor and is read only for a bounded audit or deep application.

Precedence guidance uses eight bands, highest to lowest: system directives, output contract, serialization, protected literals, accuracy, terminology, writing profile, user-facing presentation. It instructs lower-band shaping to yield to a higher band.

Measure static file-bundle footprints with `python tools/measure_context.py <file>`. The result is not live-host telemetry for reads, latency, tool calls, or repair work.

## Extension and governance

The registry is canonical. Add or change a rule there, then regenerate the derived surfaces and verify nothing drifted:

```
python tools/gen_rule_index.py
python tools/gen_always_on.py
python tools/gen_rule_conflicts.py
python tools/gen_readme_catalog.py
python -m pytest tests/ -q
python tools/check_provenance_leak.py --local
```

`generated_counts.primary_total` must equal the current active record population.
The audit ledger, not dead registry rows, preserves each starting ID and its
`KEEP`, `SIMPLIFY`, `MERGE`, `MOVE`, or `DROP` disposition. Until comparative
rewrite work runs, treat protected baseline wording as fixed.

## Known limitations

- **Prose linters are advisory and report-only.** `lint_prose.py` exits 0 on findings and even treats unreadable input as no blocking prose verdict. The structured and term checkers can return nonzero G2 verdicts, but only a host workflow can make either one a delivery gate.
- **Most registry rules are not mechanically decided.** Four rules have callable compliance validators today. Ten advisory surface detectors supply bounded
  observations for G1 semantics; they do not decide contextual compliance. The
  remainder are review-fallback or planned. A rule being in the registry does
  not mean a program checks it.
- **Host-dependent skill selection.** Historical evidence from one pinned host per round observed invocation on some task-shaped, technical, and meta-code turns and skips on some short prompts. It does not establish selection behavior for another prompt, model, or host.
- **Live-model compliance is not guaranteed.** Live outputs under the skill still show occasional rule violations, which the advisory linter reports and nothing blocks. Behavioral evidence is measured and documented, not promised.
- **Lexical advisories ignore a requested register.** An explicitly requested casual or creative voice governs the register, but lexical advisories still fire on the result; advisories never override the contract band.
- **The strict profile is locked** and must never be claimed.
- **Generated structured artifacts need host custody.** A caller can run validate, perform an authorized repair, and revalidate; STOW does not itself intercept the final response or perform the repair.
- **No general delivery integration ships.** STOW has no repository-owned integration that universally intercepts and accepts or rejects a host's final response.
- **Static budget figures are proxies.** They measure declared files with one tokenizer or a character formula, not live host reads, tokens, latency, tool calls, or repair cost.
- **Portability is file-level.** The packaged schemas, templates, and scripts use ordinary formats; live behavior on a second agent harness remains unverified.

## Troubleshooting

**The skill never seems to activate.** Confirm the layout is `<skills-dir>/stow/SKILL.md`, with `stow/` directly inside the skills directory. A common failure is unzipping into a nested folder, which yields `<skills-dir>/STOW/stow/SKILL.md` and does not resolve.

**The validator rejects JSON that looks fine.** Check, in order: a leading byte-order mark, a duplicate object key, a trailing comma, a `NaN` or `Infinity` literal, or a pasted code fence. Each has a fixture under `tests/fixtures/json/`.

**YAML values changed type.** Unquoted scalars coerce. Quote any scalar whose string form matters. Two keys that coerce to the same scalar are a duplicate-key error even when spelled differently.

**`--schema` says the schema is unknown.** The id is a bare filename stem: `handoff`, not `handoff.schema.json` and not a path.

**STOW edited my source code.** G1 guidance tells the writer not to edit code unless that is the task, and the G2 linter excludes recognized code spans from its advisory scan. Neither mechanism proves that final bytes match the source. If fidelity is required, a named host must compare the actual final candidate with the authoritative source and block a mismatch. An unintended code change is a precedence violation worth reporting.

**A generated file keeps coming back changed.** `references/rule-index.md`, `references/always-on.md`, `docs/rule-conflicts.md`, and the README catalog sections are generated. Edit the registry or the conflict registry and regenerate; do not hand-edit a generated region.

**Upgrading.** Rebuild the artifact from the tagged tree you want (`python tools/build_skill.py`), remove the old `<skills-dir>/stow/` directory, and unzip the new artifact in its place. The manifest records the product version and the archive digest.

## Repository layout

```
skills/stow/
  SKILL.md              kernel: precedence, region model, integrity rules
  references/           mid-tier guidance, loaded by predicate
  corpus/               grouped modules, every rule at a ## STOW-XXX-NNN anchor
  rules/                registry, profiles, conflicts, and their schemas
  runtime/              validators, prose lint, and the profile resolver
  schemas/              meta-code artifact schemas
  templates/            meta-code authoring templates
docs/                   design notes, evidence reports, generated conflict doc
tests/                  test suite, evals, and fixtures
tools/                  build, generation, and check tooling
dist/                   built artifact, checksum, and entry manifest
```
