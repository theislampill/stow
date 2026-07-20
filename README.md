# STOW

STOW is a writing-discipline skill that governs what a model emits. It treats every reply as a set of typed regions (prose, procedure, structured data, code, quotes, identifiers) and applies a fixed rule set so each region stays correct for what it is.

## STOW in one minute

- **What it does.** STOW is designed to be selected on every user-facing turn; when the host invokes it, the compact kernel loads. The kernel classifies the reply into regions, applies always-on integrity and output-shaping checks to the prose, and pulls deeper references only when a named predicate is true.
- **What it governs.** User-facing prose (answers, explanations, procedures), agent-to-agent coordination artifacts (handoffs, plans, audits, runbooks, state records, task packets, event streams), and structured payloads (JSON, JSONL, YAML) held to a parse-and-validate contract.
- **What it protects.** Code, commands, paths, identifiers, quoted text, and data values are protected literals: they pass through byte-for-byte unchanged. **Executable source code is protected by default and is not STOW's primary writing target.** If you install STOW expecting it to restyle your source code, it will not, by design.
- **How always-on works.** Any user-facing prose turn loads the operational checks in `references/always-on.md`. Each check carries its rule id, its applicability condition, and its principal exception, and the module opens with a request-mode router: an informational question leads with the answer, an actionable task with the next bounded action, completed work with the result and no invented follow-up, a raw artifact with the raw artifact alone.
- **How profiles work.** Profiles only make rules stricter, and only where they apply. The default profile imposes no controlled punctuation, contraction, vocabulary, or sentence-length rules; the controlled profile activates them for executable procedures and safety instructions.
- **How meta-code fits.** Coordination artifacts are governed by schemas and templates, not by taste. The shipped validator checks any instance against its schema, and the documented loop is validate, repair, revalidate.

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

A clean install prints `VALID (json): some-file.json` and exits 0. The runtime never imports from the repository. `lint_prose.py` and `profiles.py` are standard-library only; `validate.py` additionally needs two ordinary packages on the host: `pip install ruamel.yaml jsonschema` (on Python 3.11, `jsonschema` also pulls `referencing` and `typing_extensions` transitively).

## Profiles at a glance

Profiles are declared in one shipped data file, `skills/stow/rules/profiles.json`, and resolved by one shipped module, `runtime/profiles.py`. The kernel's activation map, the prose linter, the generators, and the tests all consume the same declaration.

| Profile | Status | What it does |
|---|---|---|
| `stow-default` | Active by default for editable prose | Always-on integrity and user-facing output governance. Imposes no controlled punctuation, contraction, vocabulary, or sentence-length rules. |
| `technical-clarity` | Auto-active for technical and coordination prose | **Mechanical checks identical to `stow-default` by design.** Adds review-level terminology and wording-consistency guidance, stable names, bounded steps, explicit conditions, and evidence-aware claims; meta-code artifacts bind here; the linter tags its output with the profile. See `references/technical-clarity.md`. |
| `controlled-technical-guided` | Auto-active for executable procedures and safety instructions, or on request (alias: `controlled-technical`) | Applies the controlled-technical rule families as guidance: the semicolon, contraction, Latin-abbreviation, and sentence-length checks activate. Dictionary-dependent checks are reported as unavailable. |
| `controlled-technical-strict` | **LOCKED** | Full conformance to the controlled-technical writing profile. Not shipped and **must never be claimed**. Selecting it on the linter exits with an error naming the lock. |

Raw and protected artifacts are their own mode, not a profile: raw JSON, JSONL, YAML, code, quotations, identifiers, commands, and paths load no prose checks at all. The output ships byte-exact and only the applicable parser or schema validator runs.

When more than one profile matches, the declared auto-precedence decides: `controlled-technical-guided` over `technical-clarity` over `stow-default`. Punctuation across profiles: the em dash is banned in editable prose under every profile; the semicolon and contractions are permitted (never required) under `stow-default` and `technical-clarity` and prohibited under `controlled-technical-guided`, where the substitute for either banned character is a period, comma, colon, or two sentences.

The strict profile is locked because the inputs it needs (the controlled dictionary, the approved terminology set, and the full validation suite) are out of scope for this release. STOW reports guided, partial alignment and names which checks ran and which did not. Any claim of full conformance is an overclaim the conformance reference explicitly forbids.

## Rule classes at a glance

The registry indexes 96 primary rules under STOW's own functional taxonomy. The registry defines each rule's operational metadata; the corpus module behind it carries the full guidance.

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
| `STOW-ACT-002` | Numbered steps for multi-step work | All prose (always on) | Planned |
| `STOW-ACT-003` | Close with a single concrete next step | open work remains when the turn ends; exception: when the work is complete, report the result and invent no follow-up step | Review-fallback |
| `STOW-ACT-004` | Defer secondary issues | a secondary issue surfaces during the main task; exception: offer the deferred issue separately at the end rather than dropping it | Planned |
| `STOW-ACT-005` | Restate progress each turn | a multi-turn task is in progress; exception: a single-turn answer needs no progress ledger | Review-fallback |
| `STOW-ACT-006` | Concrete effort estimates | a defensible range exists for the estimate; exception: with no defensible range, omit the figure; accuracy outranks the preference | Review-fallback |
| `STOW-ACT-007` | Surface completed outcomes | work ran and produced a result this turn | Planned |
| `STOW-ACT-008` | Neutral error reporting | All prose (always on) | Planned |
| `STOW-ACT-009` | Bound action lists to five items | All prose (always on) | Callable |
| `STOW-ACT-010` | No preamble, recap, or sign-off | All prose (always on) | Planned |
| `STOW-ACT-011` | Lists, not tables, for action sequences | All prose (always on) | Planned |

</details>

<details>
<summary><b>Prose integrity</b> (PRO-001 through PRO-024)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-PRO-001` | Ban the em dash | editable prose under every profile; exception: under the controlled profile the semicolon is also banned; use a period, comma, colon, or two sentences | Callable |
| `STOW-PRO-002` | Require attributable numbers | any numeric claim; exception: no attributable source: omit the number rather than invent one | Review-fallback |
| `STOW-PRO-003` | No parentheticals in headings | Section headings | Planned |
| `STOW-PRO-004` | No empty intensifiers | All prose (always on) | Callable |
| `STOW-PRO-005` | End claims on a concrete detail | factual claims in editable prose; exception: a conceptual definition satisfies this with a precise, checkable statement | Review-fallback |
| `STOW-PRO-006` | No repeated points | All prose (always on) | Review-fallback |
| `STOW-PRO-007` | Vary structure | several consecutive blocks share one layout; exception: never vary above a length cap or across recurring terminology | Planned |
| `STOW-PRO-008` | Reference without narrating | All prose (always on) | Planned |
| `STOW-PRO-009` | No urgency without a reason | All prose (always on) | Review-fallback |
| `STOW-PRO-010` | No scare quotes on ordinary words | All prose (always on) | Callable |
| `STOW-PRO-011` | No filler phrases | All prose (always on) | Callable |
| `STOW-PRO-012` | Ban the whether-you-are opener | All prose (always on) | Callable |
| `STOW-PRO-013` | Write like a researcher | the default register; exception: an explicitly requested casual or creative voice governs; facts stay real | Review-fallback |
| `STOW-PRO-014` | No synthetic enthusiasm | All prose (always on) | Planned |
| `STOW-PRO-015` | No weasel words | All prose (always on) | Callable |
| `STOW-PRO-016` | Concrete, descriptive headings | Section headings | Planned |
| `STOW-PRO-017` | No fabricated scenarios | All prose (always on) | Review-fallback |
| `STOW-PRO-018` | No fabricated history | All prose (always on) | Review-fallback |
| `STOW-PRO-019` | No fabricated attributions | All prose (always on) | Review-fallback |
| `STOW-PRO-020` | No AI transition phrases | All prose (always on) | Callable |
| `STOW-PRO-021` | No AI verbs | All prose (always on) | Callable |
| `STOW-PRO-022` | No academic AI tells | All prose (always on) | Callable |
| `STOW-PRO-023` | Quote sources accurately | Quoted sources | Review-fallback |
| `STOW-PRO-024` | No research-process narration | process diary that changes no conclusion; exception: a limitation or failed verification that changes the answer is disclosed in one clause | Review-fallback |

</details>

<details>
<summary><b>Words and terminology</b> (WRD-001 through WRD-014)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-WRD-001` | Restrict vocabulary to dictionary-approved words plus admissible technical nouns and technical verbs | Controlled profile | Review-fallback |
| `STOW-WRD-002` | Use each approved word only in its dictionary-specified part of speech | Controlled profile | Planned |
| `STOW-WRD-003` | Use approved words only with their dictionary-approved, often restricted, meanings | Controlled profile | Review-fallback |
| `STOW-WRD-004` | Use only the verb and adjective forms the dictionary lists for that word | Controlled profile | Planned |
| `STOW-WRD-005` | Admit non-dictionary words when they fit one of the technical-noun categories | Controlled profile | Review-fallback |
| `STOW-WRD-006` | Allow an unapproved word only when it is part of a technical noun | Controlled profile | Review-fallback |
| `STOW-WRD-007` | Do not use a technical noun as a verb; keep it a noun or adjectival modifier | Controlled profile | Planned |
| `STOW-WRD-008` | Prefer the technical noun already approved by your company, industry, or subject field | Controlled profile | Planned |
| `STOW-WRD-009` | When coining a technical noun, keep it short and easy to understand | Controlled profile | Planned |
| `STOW-WRD-010` | Do not use regional, slang, or jargon words as technical nouns | Controlled profile | Review-fallback |
| `STOW-WRD-011` | Use one technical noun consistently for one item; do not switch synonyms mid-text | guidance-level under the technical-clarity profile; binding under the controlled profile | Planned |
| `STOW-WRD-012` | Admit verbs that fit a technical-verb category, but prefer an approved dictionary verb when one exists | Controlled profile | Review-fallback |
| `STOW-WRD-013` | Do not nominalize a technical verb; its past participle may act as an adjective | Controlled profile | Planned |
| `STOW-WRD-014` | Use American English spelling unless another official directive overrides; do not change quoted-text spelling | Controlled profile | Planned |

</details>

<details>
<summary><b>Multi-word nouns</b> (MWN-001 through MWN-002)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-MWN-001` | Keep multi-word nouns to a maximum of three words | Controlled profile | Planned |
| `STOW-MWN-002` | For a technical noun longer than three words, write it in full first, then shorten or hyphenate | Controlled profile | Planned |

</details>

<details>
<summary><b>Verbs and voice</b> (VRB-001 through VRB-007)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-VRB-001` | Use only the verb forms the dictionary provides for each approved verb | Controlled profile | Planned |
| `STOW-VRB-002` | Use only the approved verb forms and tenses; no perfect, progressive, or complex constructions | Controlled profile | Planned |
| `STOW-VRB-003` | Use the past participle only as an adjective, and only if it is in the dictionary | Controlled profile | Planned |
| `STOW-VRB-004` | Do not use auxiliary verbs to build perfect, progressive, or passive complex constructions | Controlled profile | Planned |
| `STOW-VRB-005` | Use an -ing word only as a technical noun or as a modifier inside a technical noun | Controlled profile | Planned |
| `STOW-VRB-006` | Use active voice; passive is allowed only in descriptive writing when the agent is unknown | Controlled profile | Planned |
| `STOW-VRB-007` | Describe an action with an approved verb, not a nominalization or other part of speech | Controlled profile | Planned |

</details>

<details>
<summary><b>Sentences and paragraphs</b> (SEN-001 through SEN-005)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-SEN-001` | Write short, clear, concrete sentences suited to procedures or descriptions | Controlled profile | Review-fallback |
| `STOW-SEN-002` | Do not omit words or use contractions; write every word in full | Controlled profile | Planned |
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
| `STOW-PRC-003` | Write instructions in the imperative command form | Controlled profile | Planned |
| `STOW-PRC-004` | State a required condition first and separate it from the command with a comma | Controlled profile | Planned |
| `STOW-PRC-005` | Notes give information only, with a maximum of twenty-five words per sentence | Controlled profile | Planned |

</details>

<details>
<summary><b>Descriptive writing</b> (DSC-001 through DSC-006)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-DSC-001` | Introduce information gradually, one subject per sentence | Controlled profile | Review-fallback |
| `STOW-DSC-002` | Use consistent key words and phrases to give the text a logical structure | Controlled profile | Review-fallback |
| `STOW-DSC-003` | Limit each descriptive sentence to a maximum of twenty-five words | Controlled profile | Callable |
| `STOW-DSC-004` | Group related information into paragraphs, each led by a topic sentence | Controlled profile | Review-fallback |
| `STOW-DSC-005` | Give each paragraph exactly one topic | Controlled profile | Review-fallback |
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
| `STOW-PCT-002` | Use hyphens to join words that are directly related | Controlled profile | Planned |
| `STOW-PCT-003` | Use parentheses only for the approved purposes | Controlled profile | Planned |
| `STOW-PCT-004` | In a vertical list, a colon counts as a period for word count and ends a sentence | Controlled profile | Planned |
| `STOW-PCT-005` | Parenthetical text counts as one word in the host sentence | Controlled profile | Planned |
| `STOW-PCT-006` | Count numbers, identifiers, quoted text, titles, and proper nouns each as one word | Controlled profile | Planned |
| `STOW-PCT-007` | A hyphenated group of words counts as one word | Controlled profile | Planned |

</details>

<details>
<summary><b>Writing style</b> (STY-001 through STY-004)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-STY-001` | When a word-for-word replacement is insufficient, rewrite the sentence while preserving the meaning | Controlled profile | Review-fallback |
| `STOW-STY-002` | Use each approved word with its correct restricted meaning and part of speech | Controlled profile | Review-fallback |
| `STOW-STY-003` | Do not combine approved words into unlisted phrasal verbs | Controlled profile | Planned |
| `STOW-STY-004` | Use a consistent style: reuse the same terminology and wording for recurring content | guidance-level under the technical-clarity profile; binding under the controlled profile | Planned |

</details>

<details>
<summary><b>General writing practice</b> (GEN-001 through GEN-008)</summary>

| Rule | Summary | Applies when | Status |
|---|---|---|---|
| `STOW-GEN-001` | Prefer keeping the conjunction that to mark the clause boundary | Controlled profile | Planned |
| `STOW-GEN-002` | Check the preposition with for ambiguity and rewrite when unclear | Controlled profile | Planned |
| `STOW-GEN-003` | Use only approved pronouns; replace an ambiguous pronoun with its noun | Controlled profile | Planned |
| `STOW-GEN-004` | Make sure the pronoun this has an unambiguous referent | Controlled profile | Planned |
| `STOW-GEN-005` | Avoid false friends; confirm the English meaning of the word | Controlled profile | Review-fallback |
| `STOW-GEN-006` | Avoid Latin abbreviations; use English words instead | Controlled profile | Callable |
| `STOW-GEN-007` | Use gender-neutral, inclusive language | Controlled profile | Planned |
| `STOW-GEN-008` | Use the possessive correctly; if unsure, avoid it | Controlled profile | Planned |

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
| Contract-required exhaustive list vs the five-item cap | The complete list | Trimming to fit the cap | The cap advisory is suppressed for exhaustive content (`--exhaustive-list-ok`) |
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

The first run names every violation; the loop ends when the run prints `VALID`.

## Validators

**`runtime/validate.py`** is the delivery gate. Two mutually exclusive modes:

```
python skills/stow/runtime/validate.py --format {json,jsonl,yaml} <file>
python skills/stow/runtime/validate.py --schema <schema-id> <file>
```

Exit codes: `0` valid, `1` invalid (errors printed to stderr, one per line), `2` the file could not be read or is not valid UTF-8. An instance is JSON, YAML, a Markdown document (its single fenced yaml/json block is the instance), or a `.jsonl` stream validated per line. An evidence-record file can wrap several records as `{records: [...]}` and validates per record. Working instances of every schema live in `tests/fixtures/meta/`, and the shipped templates themselves are validated instances.

**`runtime/lint_prose.py`** is advisory and report-only. Findings never change the exit code; only an invalid invocation (an unknown or locked profile) exits nonzero.

```
python skills/stow/runtime/lint_prose.py <file> [--profile <id>] [--artifact-type prose|structured|raw] [--exhaustive-list-ok]
```

The profile decides which checks run, exactly as the registry declares. A file with a structured extension receives no prose findings (use `validate.py` on it). Before scanning, the linter masks protected regions (fenced blocks, inline code, block quotes, URLs, paths, identifiers) so their contents are never flagged.

**`runtime/query_rules.py`** is a packaged, standard-library-only lookup helper. Given a rule id it prints the registry record, the profiles that include the rule (by selector, category prefix, or guidance list), the per-record and composition conflicts that name it, and the anchored corpus section.

```
python skills/stow/runtime/query_rules.py STOW-PCT-006
```

It is an acceleration for manual rule lookups; no kernel path depends on it, and plain file reads remain the contract path.

## Architecture

Three tiers, loaded from most general to most specific. A response is answered from the kernel alone unless a predicate calls for more.

- **Kernel** (`skills/stow/SKILL.md`): precedence, the region model, the integrity rules, and the activation map.
- **References** (`skills/stow/references/`): mid-tier guidance, each file loaded only when its predicate is true.
- **Corpus** (`skills/stow/corpus/`): grouped conceptual modules holding the full guidance, where every rule is addressable through a stable `## STOW-XXX-NNN` heading anchor; loaded only when a rule audit or deep application cites it.

Precedence runs in eight bands, highest to lowest: system directives, output contract, serialization, protected literals, accuracy, terminology, writing profile, user-facing presentation. A lower band never corrupts a higher one.

Measure current context footprints with `python tools/measure_context.py <file>`; the tool records its measurement method and never downloads anything.

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

`generated_counts.primary_total: 96` is an invariant asserted by the test suite. Rewriting existing rule wording is deferred to a governed comparative phase; until that phase runs, treat shipped rule text as fixed.

## Known limitations

- **Prose linters are advisory and report-only.** `lint_prose.py` always exits 0 on findings. The structured-output validator is the only hard gate.
- **Most registry rules are not callable.** Fourteen rules have callable validators today. The large majority are either review-fallback (a model applies them by reading them) or planned (the validator does not exist yet). A rule being in the registry does not mean a program checks it.
- **Host-dependent skill selection.** The skill is invoked per turn by the host model. Live evidence shows it selects on task-shaped, technical, and meta-code turns and can skip trivial or raw one-liners; on a non-invoked turn, only the external parser and schema gates apply.
- **Live-model compliance is not guaranteed.** Live outputs under the skill still show occasional rule violations, which the advisory linter reports and nothing blocks. Behavioral evidence is measured and documented, not promised.
- **Lexical advisories ignore a requested register.** An explicitly requested casual or creative voice governs the register, but lexical advisories still fire on the result; advisories never override the contract band.
- **The strict profile is locked** and must never be claimed.
- **Generated structured artifacts need the validate-repair-revalidate loop.** Models approximate schemas from prose; the shipped validator is the ground truth, and the documented loop closes the gap.

## Troubleshooting

**The skill never seems to activate.** Confirm the layout is `<skills-dir>/stow/SKILL.md`, with `stow/` directly inside the skills directory. A common failure is unzipping into a nested folder, which yields `<skills-dir>/STOW/stow/SKILL.md` and does not resolve.

**The validator rejects JSON that looks fine.** Check, in order: a leading byte-order mark, a duplicate object key, a trailing comma, a `NaN` or `Infinity` literal, or a pasted code fence. Each has a fixture under `tests/fixtures/json/`.

**YAML values changed type.** Unquoted scalars coerce. Quote any scalar whose string form matters. Two keys that coerce to the same scalar are a duplicate-key error even when spelled differently.

**`--schema` says the schema is unknown.** The id is a bare filename stem: `handoff`, not `handoff.schema.json` and not a path.

**STOW edited my source code.** It should not. Code is a protected literal that passes through unchanged. If a code region was altered, that is a precedence violation worth reporting, not intended behavior.

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
