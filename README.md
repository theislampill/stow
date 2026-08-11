# STOW

**Focused writing governance for LLM output: anti-synthetic prose discipline, action-oriented responses, protected literals, and controlled technical writing when the task requires it.**

STOW (Standardising Technical Output Writing) is a public writing specification and packaged Agent Skill. It helps a model produce clear user-facing prose, procedures, coordination artefacts, and structured output without turning every task into controlled English or an expensive validation workflow.

STOW is not an AI-authorship detector, a generic “sound human” style randomiser, or a universal final-response enforcement layer. Most of its writing rules are contextual guidance. Its callable tools decide only closed properties at their declared input boundaries.

Current release: **[v0.4.0](https://github.com/theislampill/stow/releases/tag/v0.4.0)**.

## Why STOW?

A repository instruction that only names a controlled-language standard can be a useful and inexpensive model-memory cue. It still leaves the model to reconstruct the standard, decide what applies, remember the dictionary and exceptions, preserve project terminology, and distinguish contextual judgement from mechanical checks.

STOW externalises that work and adds a broader writing policy:

| Need | A name-only instruction | STOW |
|---|---|---|
| Anti-synthetic prose | Outside the named controlled-language standard | Context-bounded guidance for filler, hollow evaluation, fabricated specificity, formulaic transitions, needless process narration, and related pathologies |
| Focused output | Depends on the model's general habits | Action shaping, result-first reporting, bounded steps, tangent control, and explicit state |
| Controlled technical writing | Reconstructed from latent knowledge | Issue 9-derived rules, sparse dictionary access, project terminology authority, profiles, and explicit limitations |
| Protected content | Ad hoc | Precedence guidance for code, commands, paths, identifiers, quotations, and data values |
| Mechanical checking | Usually unspecified | Closed validators for the few properties that are genuinely mechanical |
| Inspectability | The operative policy remains mostly latent | Rules, applicability, exceptions, profiles, conflicts, evidence boundaries, and generated catalogues are public |

The measured single-task advantage over name-only conditioning was small, not dramatic. STOW's larger distinction is that the writing policy is versioned, inspectable, testable, and reusable instead of existing only as a sentence in context.

## Scope

STOW has four related operating surfaces:

| Surface | Primary job | What normally loads |
|---|---|---|
| Ordinary prose | Remove recurrent model-writing pathologies, preserve requested voice, and keep the answer focused | Compact kernel only |
| Technical and coordination prose | Add stable terminology, explicit conditions, evidence boundaries, bounded steps, and clear status | One matching cold reference when needed |
| Controlled technical writing | Apply the supported controlled-language rules, dictionary records, project terminology, procedure, description, safety, punctuation, and counting guidance | Controlled profile plus bounded cold references; sparse lookup only when a lexical question arises |
| Structured or protected content | Preserve raw data and validate closed formats or schemas | Raw/protected mode or an explicitly invoked validator |

STOW is suited to README and documentation work, technical explanations, maintenance procedures, safety text, repository status updates, agent handoffs, and structured artefacts. It can also govern ordinary conversational prose when the user wants a more direct and less synthetic response.

STOW is not intended to replace a creative style guide, infer project terminology without authority, certify strict controlled-language conformance, or guarantee that a host will select the skill automatically.

## Design genealogy

STOW is an independent synthesis, not a dependency bundle or a one-to-one copy of any source.

<!-- PUBLIC-GENEALOGY:BEGIN -->
| Source | Contribution to STOW | Boundary |
|---|---|---|
| [ASD-STE100 Simplified Technical English, Issue 9](https://www.asd-ste100.org/) | The controlled-technical lineage: bounded vocabulary, technical nouns and verbs, sentence and procedure constraints, safety writing, descriptions, punctuation, and the principle of specifying observable linguistic behaviour instead of saying only “write clearly” | ASD-STE100 is owned and maintained by ASD. STOW is independent, is not endorsed by ASD, and keeps strict conformance locked |
| [`realrossmanngroup/no_ai_slop_writing_rules`](https://github.com/realrossmanngroup/no_ai_slop_writing_rules) | Observable anti-synthetic patterns, worked contrasts, structural repetition, filler, hollow claims, dramatic headings, corrective contrasts, and false-positive safeguards | STOW does not import the excluded voice profile or treat statistical AI tells as universal bans; a pattern survives only when it identifies an independent writing problem and a legitimate countercontext |
| [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd) | General focus and runtime mechanisms: action-first output, visible progress, bounded steps, tangent deferral, explicit exceptions, progressive disclosure, and pre-send discipline | STOW adopts only those transferable output-design mechanisms; it does not add a source-themed mode or a universal step cap |
<!-- PUBLIC-GENEALOGY:END -->

The resulting product is broader than controlled technical language and narrower than a universal prose normaliser:

```text
anti-synthetic prose discipline
+ focused action and status shaping
+ evidence and semantic preservation
+ controlled technical writing when applicable
+ closed validation only where the property is closed
```

## What STOW changes

These examples are illustrative. They show the intended behaviour, not a guarantee that every model will make the same edit.

### Ordinary prose: remove functionless framing

Before:

```text
Great question! There are several angles worth unpacking here before we get to the answer itself.
```

After:

```text
The build fails because the lockfile pins a version the registry no longer serves. Repin it, then rerun the build.
```

### Focused work: expose the next bounded actions

Before:

```text
First open the file, find the function, swap it out, then run the tests and check whether anything else broke.
```

After:

```text
1. Open `src/auth.ts`.
2. Replace `verifyToken`.
3. Run `npm test -- auth.spec.ts`.
```

### Controlled technical writing: apply the narrow route

Source:

```text
Prior to commencement, utilize the approved bonding agent on SEAL_A; if ERR-17 occurs, terminate the operation.
```

Controlled-guided rewrite:

```text
Before the operation, apply the approved bonding agent to SEAL_A.
If ERR-17 occurs, stop the operation.
```

STOW must preserve source force. Advice, permission, uncertainty, and an authorised command are not interchangeable merely because an imperative is shorter.

### Protected output: leave the artefact alone

When the requested result is raw JSON, code, a command, a path, an identifier, or quoted text, lower-precedence prose preferences yield:

<!-- validate:json -->
```json
{"service":"api","status":"ok"}
```

## Quick start

### Install

Download `STOW.skill` from the [latest release](https://github.com/theislampill/stow/releases/latest), or build it from the repository:

```bash
python tools/build_skill.py
mkdir -p ~/.claude/skills
unzip -o dist/STOW.skill -d ~/.claude/skills
```

Windows PowerShell (`Expand-Archive` requires a `.zip` suffix):

```powershell
Copy-Item dist\STOW.skill dist\STOW.zip -Force
Expand-Archive -Path dist\STOW.zip -DestinationPath "$HOME\.claude\skills" -Force
```

The expected layout is:

```text
<skills-dir>/stow/SKILL.md
```

These commands write or replace the `stow` directory under the selected skills directory. Back up local modifications before reinstalling; remove that directory to uninstall the skill.

The repository also includes Claude plugin manifests. Hosts that consume compatible skill or plugin packages can install from the repository instead of extracting the archive manually.

### Invoke

Invoke STOW explicitly when host selection matters. For example:

```text
Use STOW to rewrite this README section. Preserve every technical claim, command, path, identifier, and quotation.
```

For controlled technical work:

```text
Use STOW under the controlled-technical-guided profile. Rewrite this procedure, preserve source force and protected literals, and do not claim strict conformance.
```

Automatic skill selection is host-dependent. Installation alone does not prove that a particular host or task loaded STOW.

### Smallest working flow

1. Invoke STOW explicitly and name the output type or profile when it matters.
2. Supply the draft or task plus the facts, literals, terminology authority, and voice that must survive.
3. Review the returned candidate. Invoke a runtime helper only for a closed check that the task needs; advisory findings do not block delivery by themselves.

STOW reads no repository files and runs no helper merely because it is installed. A host or agent performs only the reference reads and explicit tool calls required by the selected route. Unknown project terms remain unresolved unless the caller supplies an approved terminology surface.

### Validate a structured artefact

```bash
python ~/.claude/skills/stow/runtime/validate.py --format json some-file.json
python ~/.claude/skills/stow/runtime/validate.py --schema handoff my-handoff.md
```

A valid instance exits `0`. A validator result applies only to the supplied candidate; STOW does not automatically intercept or approve a host's final response.

## How STOW works

STOW uses progressive disclosure rather than one always-hot rule dump.

| Layer | Purpose | Normal runtime role |
|---|---|---|
| Kernel (`skills/stow/SKILL.md`) | Request mode, precedence, protected regions, ordinary prose discipline, and bounded routing | Loaded when the skill is selected |
| References (`skills/stow/references/`) | Technical, controlled, safety, procedure, format, and other predicate-specific guidance | Read only when one named predicate applies; normal generation should not walk neighbouring files |
| Corpus (`skills/stow/corpus/`) | Full rule statements, qualifications, examples, and audit anchors | Deep application, review, and maintenance; not a normal-turn payload |
| Runtime (`skills/stow/runtime/`) | Parsers, schema checks, term-map checks, dictionary lookup, advisory lint, profile resolution, and rule queries | Invoked explicitly when its closed contract is useful; normal prose generation must not probe `--help`, create temporary candidates, or run advisory lint by default |

### Architecture at a glance

The v0.4.0 registry contains **65 active canonical rules**. That number is an implementation shape, not a coverage target.

- **Sixty-one G1 semantic owners** provide model-mediated guidance.
- **Ten G1 owners** are compacted into the ordinary kernel.
- **Fifty-one G1 owners** are cold or predicate-loaded.
- **Four G2 predicates** decide closed properties at declared input boundaries.
- **Ten advisory signals** report surface patterns; they do not decide contextual compliance.
- **57 G1 owners** have qualifying behavioural evidence.
- `STOW-PRO-005` remains an open contextual limitation.
- `STOW-WRD-001` terminates at an external project-authority boundary.
- `STOW-WRD-003` and `STOW-VRB-005` are explicit contextual deferrals.

The original audit population was 96 rule IDs. The governed reconciliation record preserves how those IDs became the current 65-rule architecture; retired IDs do not remain active merely for traceability.

### Profiles

| Profile | Use | Mechanical behaviour |
|---|---|---|
| `stow-default` | Ordinary user-facing prose, focus, evidence, and protected-content guidance | No controlled punctuation, contraction, vocabulary, or sentence-length rules |
| `technical-clarity` | Technical explanations and coordination prose that need stable names, explicit conditions, bounded steps, and evidence-aware claims | Same mechanical prose checks as `stow-default`; adds contextual technical guidance |
| `controlled-technical-guided` | Procedures, safety instructions, and controlled technical writing | Activates the supported controlled rule families, sparse dictionary access, and the semicolon, contraction, Latin-abbreviation, and sentence-length checks |
| `controlled-technical-strict` | Strict conformance | **Locked.** STOW does not ship or claim this capability |

Raw and protected artefacts are a mode, not another profile. A host must identify the task and retain custody of the actual candidate.

## Callable tools

The tools are optional accelerators with explicit evidence ceilings.

| Tool | What it can establish | What it cannot establish |
|---|---|---|
| `runtime/validate.py` | Whether the supplied JSON, JSONL, YAML, or schema instance satisfies its closed parser/schema contract | That the model's final response was the validated candidate, or that a host will block delivery |
| `runtime/lint_prose.py` | Advisory surface findings under a caller-supplied profile | Contextual writing quality or compliance; findings do not make the command fail |
| `runtime/validate_terms.py` | Compliance with an explicit closed term map over caller-labelled editable/protected segments | That the segment labels are semantically correct or that an unknown term is authorised |
| `runtime/dictionary_lookup.py` | Fixed dictionary membership, listed alternatives, and listed forms from the bundled projection | Intended sense, part of speech in context, or project-specific terminology authority |
| `runtime/query_rules.py` | The public registry record, applicable profiles, conflicts, and corpus anchor for a rule ID | Automatic semantic routing or live host activation |

`validate.py` requires `ruamel.yaml` and `jsonschema`; the other listed runtime helpers are standard-library only.

## Evidence

### Controlled-language benchmark

A frozen, crosswalk-derived comparison used the same Luna Max model across no conditioning, a name-only controlled-language instruction, raw Issue 9 source conditioning, and STOW. The benchmark accounted for **sixty-one top-level requirements plus 25 explicit child requirements**.

| Arm | PASS | FAIL | NOT_SCORED |
|---|---:|---:|---:|
| Name-only | 78 | 6 | 2 |
| STOW | 80 | 4 | 2 |

STOW uniquely passed three rows involving paragraph grouping, an ambiguous `with` relation, and paragraph sentence count. Name-only uniquely passed one procedure row because STOW distorted advisory force. The operation/force defect was subsequently narrowed and passed a targeted Luna Max regression; the complete four-arm trial was not rerun.

This supports a bounded claim: STOW operationalised more of the tested requirement surface on that model and corpus. It does **not** establish universal output superiority, strict conformance, cross-model proof, or long-thread durability. Complete accounting is not complete behavioural compliance.

The current v0.4.0 result is summarised here and in [`CHANGELOG.md`](CHANGELOG.md). [`docs/FUNCTIONAL-EVIDENCE.md`](docs/FUNCTIONAL-EVIDENCE.md) preserves the earlier enabled-versus-disabled programme, and [`docs/evaluation-results.md`](docs/evaluation-results.md) documents the fixture and detector baseline; neither is presented as the owner of Trial 2.

### Normal runtime instrumentality

A separate one-host probe measured cumulative logical input for normal installed-skill use after removing an overengineered runtime path that had caused reference walks, helper discovery, `--help` probes, temporary candidates, advisory lint calls, and repeated model turns.

| Task | Post-fix STOW / name-only logical input |
|---|---:|
| Ordinary README edit | 3.2044× |
| Technical documentation edit | 3.1848× |
| Controlled procedure edit | 5.7776× |
| Two-turn repository workflow | 1.5651× |
| Second turn only | 1.0651× |

These are **logical-input ratios, not billing multipliers**. The STOW arms had higher cache-hit fractions, but the Pro-plan receipts did not expose an authoritative cached-input price, so monetary cost was not derived. Controlled use remains materially more expensive at cold start; repeated use in the measured established thread was close to name-only input.

The result is bounded to one Codex host. Cross-host economics, cross-model behaviour, and the hypothesis that externalised governance degrades less over long or compacted conversations remain unproved.

This README is the public owner of the v0.4.0 normal-runtime summary. [`docs/design.md`](docs/design.md) supplies deeper architecture detail; the README keeps the measured ratios and their evidence limits together so a reader does not mistake logical input for billing cost.

## Rule classes at a glance

The current registry indexes 65 primary rules under STOW's own functional
taxonomy. The registry defines each active rule's operational metadata; the
governed reconciliation record preserves the original population and retired IDs.

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

The table is the landing-page summary. Exact rule wording, applicability, exceptions, and status remain generated from the registry; the complete generated catalogue is retained as an appendix below and the rule index remains the stronger navigation owner.

## Important boundaries

- **Contextual guidance is not deterministic.** G1 rules can fail even when read. `STOW-PRO-005` remains open because a measured model twice preserved unsupported evaluative labels.
- **Only closed properties get G2 claims.** Four rules have callable compliance predicates. Advisory surface matches do not prove contextual harm.
- **No final-output custody ships.** A host must hold the actual final candidate, run any required checks, block invalid or unknown results, authorise repairs, and revalidate before delivery.
- **Automatic activation is not guaranteed.** Installed skill availability, host selection, and actual reads are separate facts.
- **Strict controlled-language conformance is locked.** Dictionary lookup, contextual guidance, project terminology, and bounded validators do not establish full conformance.
- **Project terminology needs authority.** Unknown words are not self-authorising technical terms. A caller or repository must supply an approved terminology surface.
- **Dictionary facts have limits.** The bundled 2,198-record projection can expose membership, forms, and alternatives. It cannot decide the intended sense or grammatical role by itself.
- **Protected-region handling is bounded.** Guidance and advisory masking cover declared or recognisable regions; STOW has no universal byte comparator for final output.
- **Runtime evidence is local.** The measured token ratios come from one Codex/Luna Max environment. Billing cost, cross-host parity, cross-model parity, and long-run durability were not established.
- **STOW is not an AI detector.** It suppresses specified writing pathologies without claiming to identify the author of a text.

## Documentation map

| Need | Public owner |
|---|---|
| Full active rule catalogue | Generated appendix below; authoritative navigation in [`skills/stow/references/rule-index.md`](skills/stow/references/rule-index.md) |
| Rule conflicts and precedence | [`docs/rule-conflicts.md`](docs/rule-conflicts.md) |
| Current v0.4.0 product/evidence summary | This README and [`CHANGELOG.md`](CHANGELOG.md) |
| Architecture and profile model | [`docs/design.md`](docs/design.md) |
| Earlier enabled-versus-disabled evidence | [`docs/FUNCTIONAL-EVIDENCE.md`](docs/FUNCTIONAL-EVIDENCE.md) |
| Fixture and detector baseline | [`docs/evaluation-results.md`](docs/evaluation-results.md) |
| Rule usability and implementation status | [`docs/RULE-USABILITY.md`](docs/RULE-USABILITY.md) |
| Package and install evidence | [`docs/INITIAL-PACKAGE-HEALTH.md`](docs/INITIAL-PACKAGE-HEALTH.md) |
| Self-dogfood and public-claim checks | [`docs/SELF-DOGFOOD.md`](docs/SELF-DOGFOOD.md) |
| Historical rewrite-readiness checkpoint | [`docs/REWRITE-READINESS.md`](docs/REWRITE-READINESS.md) |
| Source skill contract | [`skills/stow/SKILL.md`](skills/stow/SKILL.md) |

## The complete primary-rule catalog

Every primary rule, exactly once, grouped by rule class. The one-sentence summaries are navigational, not authoritative: the registry (`skills/stow/rules/registry.yaml`) defines operational metadata, and each rule's corpus module carries the full statement, qualifications, and examples. Expand a class to see its rules.

Status meanings: **Callable** means a shipped validator checks it mechanically. **Planned** means the mechanism is specified but not implemented. **Review-fallback** means a model applies it by reading it; no program checks it.

These statuses describe the **mechanical implementation route**, not whether the semantic guidance exists or has behavioural evidence. `Planned` does not mean that the rule is absent from the writing specification; it means that no callable checker implements the stated mechanism.

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
| `STOW-PRO-017` | No fabricated scenarios | Conditional | Review-fallback |
| `STOW-PRO-018` | No fabricated history | Conditional | Review-fallback |
| `STOW-PRO-019` | No fabricated attributions | Conditional | Review-fallback |
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

## Contributing and regeneration

The registry is canonical. Change the owned source, regenerate derived public surfaces, and run the checks:

```bash
python tools/gen_rule_index.py
python tools/gen_always_on.py
python tools/gen_rule_conflicts.py
python tools/gen_readme_catalog.py
python -m pytest tests/ -q
python tools/check_provenance_leak.py --local
```

Do not hand-edit generated regions such as `references/rule-index.md`, `references/always-on.md`, or `docs/rule-conflicts.md`.

## Troubleshooting

**The skill does not activate.** Confirm that the install resolves to `<skills-dir>/stow/SKILL.md`. A nested `<skills-dir>/STOW/stow/SKILL.md` layout will not resolve correctly. Then invoke STOW explicitly; automatic selection is host-dependent.

**The strict profile fails.** That is intentional. `controlled-technical-strict` is locked because STOW does not have the authority, contextual decisions, final-output validation, and delivery custody required for a strict conformance claim.

**A validator rejects JSON that looks valid.** Check for a byte-order mark, duplicate key, trailing comma, `NaN`, `Infinity`, or a pasted code fence.

**YAML values changed type.** Quote scalars whose string form matters. Keys that coerce to the same scalar are duplicate keys even when their spelling differs.

**STOW edited code or a literal.** That is a precedence violation unless editing the literal was the task. G1 guidance and the advisory linter cannot prove final byte identity; use an independent comparison when exact preservation is required.

**A generated documentation file returns after editing.** Change the registry or conflict owner and regenerate. Do not hand-edit generated output.

**Upgrading.** Remove the previous `<skills-dir>/stow/` directory and extract the new release artefact in its place. Verify the installed payload against the release you intended to install.

## Repository layout

```text
skills/stow/
  SKILL.md              compact kernel and source skill contract
  references/           predicate-loaded public guidance and generated indexes
  corpus/               full rule modules and stable audit anchors
  rules/                registry, profiles, conflicts, dictionary data, and schemas
  runtime/              bounded validators, lookup helpers, lint, and profile resolution
  schemas/              structured artefact schemas
  templates/            worked structured artefact templates
docs/                   design, evidence, package health, readiness, self-dogfood, and conflicts
tests/                  test suite, evaluations, and fixtures
tools/                  builders, generators, measurements, and checks
dist/                   built skill archive, checksum, and manifest
```
