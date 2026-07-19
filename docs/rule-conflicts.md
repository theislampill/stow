# Cross-rule conflict resolutions

GENERATED FILE -- do not edit. Source: `skills/stow/rules/conflicts.yaml`
via `tools/gen_rule_conflicts.py`; regenerate after any registry change.

Authority: entries marked *registry* mirror the per-record `conflicts[]`
edges in `skills/stow/rules/registry.yaml`, which stay canonical for those
pairs. Entries marked *composition* are canonical here. Every resolution is
terminal: it names the winning band, the losing behavior, and the permitted
substitute. `deterministic` means band order or an enumerated substitution
decides; `semantic-review` means the entry states the operational test a
reviewer applies.

## CFL-001 -- `STOW-WRD-011` vs `STOW-PRO-007`

- Origin: registry. Resolution kind: semantic-review.
- Fires when: A controlled-technical profile is active and recurring content tempts wording variation.
- Winner: band `profile` (`STOW-WRD-011`).
- Losing behavior: Varying the term used for one item or recurring step to satisfy the variation preference.
- Permitted substitute: Keep consistent terminology and wording for the same item or recurring step
- Registry resolution (canonical, verbatim): Keep consistent terminology and wording for the same item or recurring step. Domain terminology and the controlled-technical profile outrank the presentation-layer variation preference.
- Fixture (conforming): Step 2 names the drain valve. Step 5 must say drain valve again, not outlet tap.
- Fixture (violating): The prose reads repetitively, so alternate between drain valve and outlet tap for flow.
- Evidence: registry.yaml conflicts[] edges on STOW-WRD-011 and STOW-PRO-007.

## CFL-002 -- `STOW-STY-004` vs `STOW-PRO-007`

- Origin: registry. Resolution kind: semantic-review.
- Fires when: Recurring content repeats across a document while the variation preference is active.
- Winner: band `profile` (`STOW-STY-004`).
- Losing behavior: Rewording a recurring caution, step, or label between occurrences.
- Permitted substitute: Keep consistent terminology and wording for the same item or recurring step
- Registry resolution (canonical, verbatim): Keep consistent terminology and wording for the same item or recurring step. Domain terminology and the controlled-technical profile outrank the presentation-layer variation preference.
- Fixture (conforming): The same caution text appears before step 3 and step 9, word for word.
- Fixture (violating): Rephrase the second caution so the document does not repeat itself.
- Evidence: registry.yaml conflicts[] edges on STOW-STY-004 and STOW-PRO-007.

## CFL-003 -- `STOW-PRC-001` vs `STOW-PRO-007`

- Origin: registry. Resolution kind: deterministic.
- Fires when: A controlled-technical profile is active over procedural prose and sentence-length variation is preferred.
- Winner: band `profile` (`STOW-PRC-001`).
- Losing behavior: Letting a procedural sentence exceed the word cap to vary rhythm.
- Permitted substitute: Vary sentence length below the cap, never above it
- Registry resolution (canonical, verbatim): Sentence-length caps govern inside a controlled-technical profile. Vary sentence length below the cap, never above it; the profile outranks the presentation-layer variance preference.
- Fixture (conforming): Short step. Then a longer step that still stays under the cap. Then short again.
- Fixture (violating): For variety, one long flowing step of many clauses that runs past the cap.
- Evidence: registry.yaml conflicts[] edges on STOW-PRC-001 and STOW-PRO-007.

## CFL-004 -- `STOW-DSC-003` vs `STOW-PRO-007`

- Origin: registry. Resolution kind: deterministic.
- Fires when: A controlled-technical profile is active over descriptive prose and sentence-length variation is preferred.
- Winner: band `profile` (`STOW-DSC-003`).
- Losing behavior: Letting a descriptive sentence exceed the word cap to vary rhythm.
- Permitted substitute: Vary sentence length below the cap, never above it
- Registry resolution (canonical, verbatim): Sentence-length caps govern inside a controlled-technical profile. Vary sentence length below the cap, never above it; the profile outranks the presentation-layer variance preference.
- Fixture (conforming): The pump feeds the loop. The loop returns coolant to the tank through the heat exchanger.
- Fixture (violating): A single ornate descriptive sentence that sails far past the cap in the name of variety.
- Evidence: registry.yaml conflicts[] edges on STOW-DSC-003 and STOW-PRO-007.

## CFL-005 -- `STOW-PCT-001` vs `STOW-PRO-001`

- Origin: registry. Resolution kind: deterministic.
- Fires when: An em dash would be replaced while a controlled-technical profile bans the semicolon.
- Winner: band `profile` (`STOW-PCT-001`).
- Losing behavior: Replacing a banned em dash with a semicolon under the controlled profile.
- Permitted substitute: Replace with a period, comma, colon, or two sentences
- Registry resolution (canonical, verbatim): Use neither character. Replace with a period, comma, colon, or two sentences; the active controlled-technical profile decides the substitute and outranks the presentation-layer preference.
- Fixture (conforming): The valve sticks. Replace the seal. (Two sentences, no em dash, no semicolon.)
- Fixture (violating): The valve sticks; replace the seal, written under the controlled profile.
- Evidence: registry.yaml conflicts[] edges on STOW-PCT-001 and STOW-PRO-001. Outside the controlled profile the semicolon stays permitted and is never required.

## CFL-006 -- `STOW-WRD-014` vs `STOW-PRO-021`

- Origin: registry. Resolution kind: deterministic.
- Fires when: A banned or non-preferred token sits inside code, a quoted span, or an identifier.
- Winner: band `literals` (`STOW-WRD-014`).
- Losing behavior: Respelling or replacing a token inside a protected region to satisfy a lexical preference.
- Permitted substitute: Do not rename keys or identifiers and do not edit quoted text
- Registry resolution (canonical, verbatim): Protected regions are immutable. Do not rename keys or identifiers and do not edit quoted text; serialization validity and protected literals outrank presentation-layer lexical preferences, which skip protected regions.
- Fixture (conforming): The config key `colour_mode` keeps its spelling; the surrounding prose uses color.
- Fixture (violating): Rename the `colour_mode` key to `color_mode` in the quoted config for spelling consistency.
- Evidence: registry.yaml conflicts[] edges on STOW-WRD-014 and STOW-PRO-021.

## CFL-007 -- `STOW-PCT-006` vs `STOW-PRO-021`

- Origin: registry. Resolution kind: deterministic.
- Fires when: A lexical preference would touch punctuation or wording inside a protected region.
- Winner: band `literals` (`STOW-PCT-006`).
- Losing behavior: Editing quoted text or literal punctuation to satisfy a lexical preference.
- Permitted substitute: Do not rename keys or identifiers and do not edit quoted text
- Registry resolution (canonical, verbatim): Protected regions are immutable. Do not rename keys or identifiers and do not edit quoted text; serialization validity and protected literals outrank presentation-layer lexical preferences, which skip protected regions.
- Fixture (conforming): The quoted error message keeps its exact wording, including the words it uses.
- Fixture (violating): Clean up the quoted error message so it reads better in the report.
- Evidence: registry.yaml conflicts[] edges on STOW-PCT-006 and STOW-PRO-021.

## CFL-008 -- `STOW-ACT-006` vs `STOW-PRO-002`

- Origin: registry. Resolution kind: semantic-review.
- Fires when: An effort estimate is requested or expected and no defensible range exists.
- Winner: band `accuracy` (`STOW-PRO-002`).
- Losing behavior: Inventing a concrete time or effort figure to satisfy the estimate preference.
- Permitted substitute: Give an effort estimate only when a defensible range exists; otherwise omit it
- Registry resolution (canonical, verbatim): Give an effort estimate only when a defensible range exists; otherwise omit it. Factual accuracy outranks the presentation-layer estimate preference, and an unsupported number must not be presented as fact.
- Tie-break: Both records carry presentation precedence; the resolution appeals to the accuracy band, which outranks presentation. The accuracy appeal is the recorded winner, not the record tags.
- Fixture (conforming): Reindexing takes 10 to 15 minutes on this data set, measured on the last three runs.
- Fixture (violating): This will take exactly 7 minutes, stated with no measurement behind it.
- Evidence: registry.yaml conflicts[] edges on STOW-ACT-006 and STOW-PRO-002.

## CFL-009 -- `STOW-ACT-001` vs kernel-duty `result-first`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: The request is an informational question or explanation rather than an actionable task.
- Winner: band `contract` (`result-first`).
- Losing behavior: Opening an informational answer with a next action the reader did not ask for.
- Permitted substitute: Lead with the answer or result; lead with the next bounded action only when the request is an actionable task.
- Fixture (conforming): Q: why did the job fail? A: the token expired at 09:14; renew it to resume.
- Fixture (violating): Q: why did the job fail? A: first, open the dashboard and click the retry button.
- Evidence: Request intent decides the opening. The intent router in references/always-on.md carries the mode table; the output contract band outranks presentation shaping.

## CFL-010 -- `STOW-ACT-003` vs `STOW-ACT-007`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: The turn ends with no work left open.
- Winner: band `presentation` (`STOW-ACT-007`).
- Losing behavior: Fabricating a next step to close a turn whose work is complete.
- Permitted substitute: Report the completed result; add a next action only when open work remains.
- Tie-break: Same band. The closing-step rule fires only on its own condition (open work remains); completed work satisfies it vacuously, so the completed-work rule governs the closing.
- Fixture (conforming): The migration finished and all twelve checks pass. Nothing is left open.
- Fixture (violating): The migration finished and all checks pass. Next, you could consider exploring the codebase.
- Evidence: The closing-step rule's own applicability condition (open work remains) resolves the pair; the condition is carried in the always-on module.

## CFL-011 -- `STOW-ACT-009` vs band `contract`

- Origin: composition. Resolution kind: deterministic.
- Fires when: The output contract requires an exhaustive or complete list longer than the action cap.
- Winner: band `contract` (`contract`).
- Losing behavior: Trimming, grouping, or splitting a contract-required exhaustive list to fit the five-item cap.
- Permitted substitute: Ship the complete list; the cap advisory is suppressed by the exhaustive-list permission (runtime flag --exhaustive-list-ok).
- Fixture (conforming): The audit record lists all nine findings because the contract requires every finding.
- Fixture (violating): Only the top five findings are shown to keep the list short; four are omitted from the audit record.
- Evidence: The cap shapes action queues; it never truncates evidence, reference material, or contract-required output. Band 2 outranks presentation.

## CFL-012 -- `STOW-PRO-015` vs band `accuracy`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: A claim carries justified uncertainty while the anti-hedging rule is active.
- Winner: band `accuracy` (`accuracy`).
- Losing behavior: Flattening justified uncertainty into false confidence to avoid hedging language.
- Permitted substitute: Cut empty hedges; keep load-bearing uncertainty stated once, with its reason.
- Fixture (conforming): The fix removes the deadlock in every reproduction we have; the race window under load is untested.
- Fixture (violating): The fix definitely removes the deadlock in all cases, asserted without testing the load path.
- Evidence: The accuracy band keeps justified uncertainty; the anti-hedging rule targets empty qualifiers, not calibrated claims.

## CFL-013 -- `STOW-PRO-024` vs band `accuracy`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: A source limitation, failed verification, or unavailable tool materially changes the answer.
- Winner: band `accuracy` (`accuracy`).
- Losing behavior: Silently omitting a limitation the reader needs, to avoid narrating process.
- Permitted substitute: Disclose the material limitation in one clause bound to its consequence; omit exploration narration that changes nothing.
- Tie-break: Operational test: state is a past-tense outcome bound to a reader-checkable artifact or gate; diary is exploration narration that produces no reader-checkable state change. A mixed sentence keeps the outcome clause and drops the exploration clause.
- Fixture (conforming): The vendor changelog is unavailable, so the fix version is unconfirmed; treat 2.4.1 as unverified.
- Fixture (violating): I searched several pages and could not find much, then I tried another query, and eventually gave up.
- Expected rewrite of the violation: The fix version is unconfirmed because the vendor changelog is unavailable.
- Evidence: Report-what-you-can-support suppresses diary narration, not disclosures that change the answer. Accuracy outranks presentation.

## CFL-014 -- `STOW-PRO-005` vs band `contract`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: The request asks for a conceptual or definitional explanation with no natural number, name, or date.
- Winner: band `contract` (`contract`).
- Losing behavior: Deleting a correct conceptual sentence because it lacks a concrete figure, or padding it with an irrelevant one.
- Permitted substitute: A precise, verifiable statement of the concept satisfies the concrete-detail requirement; the detail is precision, not a numeral.
- Fixture (conforming): Idempotency means running the migration twice leaves the schema in the same state as running it once.
- Fixture (violating): Idempotency is a powerful property that many modern systems embrace in various ways.
- Evidence: The concrete-detail rule kills hollow claims; a conceptual explanation is not hollow when it is precise and checkable.

## CFL-015 -- `STOW-PRO-013` vs band `contract`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: The user explicitly requests a casual, creative, or organizational voice.
- Winner: band `contract` (`contract`).
- Losing behavior: Overriding the requested register to keep the researcher tone.
- Permitted substitute: Write in the requested register; fabrication, accuracy, and protected-literal rules still apply. Not runtime-enforceable; the lexical advisories still fire regardless of register and never override the contract band.
- Fixture (conforming): User asked for a playful release note; the note is playful and every fact in it is real.
- Fixture (violating): User asked for a playful release note; the reply is a formal technical memo instead.
- Evidence: An explicit register request is part of the output contract. Band 2 outranks presentation tone rules; it never unlocks fabrication.

## CFL-016 -- `STOW-PRO-017` vs band `contract`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: The user requests a hypothetical example or scenario.
- Winner: band `contract` (`contract`).
- Losing behavior: Refusing a requested hypothetical, or presenting an invented scenario as a real event.
- Permitted substitute: Provide the scenario clearly labeled as hypothetical; never present invented events as history.
- Fixture (conforming): Hypothetical: suppose the primary region fails during the batch window; the runbook fails over in stage 2.
- Fixture (violating): Last spring an unnamed customer lost their primary region during the batch window, told as fact without a source.
- Evidence: The fabrication ban targets invented events presented as real; a labeled, requested hypothetical is neither.

## CFL-017 -- `STOW-PRO-021` vs band `terminology`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: A banned-lexicon term is used in its legitimate technical sense or is the domain's established name.
- Winner: band `terminology` (`terminology`).
- Losing behavior: Replacing a domain term with a synonym that changes or blurs the technical meaning.
- Permitted substitute: Keep the technical sense (financial leverage, literal navigation, a quoted API name); avoid the term only in its inflated metaphorical sense.
- Fixture (conforming): The fund's leverage ratio doubled last quarter, in the financial sense of leverage.
- Fixture (violating): We leverage our leverage to leverage synergies, three metaphorical uses in one sentence.
- Evidence: Terminology consistency and protected literals outrank the lexical ban; the linter already masks quoted and identifier uses, and prose uses in a technical sense are review-level.

## CFL-018 -- `STOW-WRD-014` vs band `contract`

- Origin: composition. Resolution kind: deterministic.
- Fires when: An explicit user or organizational style directive sets a different regional spelling.
- Winner: band `contract` (`contract`).
- Losing behavior: Forcing the default regional spelling against an explicit style directive.
- Permitted substitute: Follow the explicit directive; the default applies only in its absence. The rule's own wording carries this exception.
- Fixture (conforming): The org style guide mandates British spelling, so the document uses colour throughout.
- Fixture (violating): The org style guide mandates British spelling, but the document silently switches to American spelling.
- Evidence: The regional-spelling rule defers to other official directives by its own baseline text; an explicit directive is band 2.

## CFL-019 -- `STOW-ACT-005` vs `STOW-PRO-024`

- Origin: composition. Resolution kind: semantic-review.
- Fires when: A multi-turn task turn must restate progress while process narration is suppressed.
- Winner: band `presentation` (`STOW-ACT-005`).
- Losing behavior: Suppressing the progress ledger as forbidden narration, or padding it with exploration diary.
- Permitted substitute: Restate task state as outcomes (done, open, blocked, each bound to an artifact or gate); omit the story of how the turn went.
- Tie-break: Same band. Operational test as CFL-013: progress state is outcome-shaped and reader-checkable; narration is exploration-shaped. The progress rule owns state; the narration rule owns everything else.
- Fixture (conforming): Done: schema migrated (checksum verified). Open: backfill job. Blocked: vendor key rotation.
- Fixture (violating): First I looked at the schema, then I wondered about the backfill, then I poked at the key rotation for a while.
- Expected rewrite of the violation: Done: schema migrated (checksum verified). Open: backfill job. Blocked: vendor key rotation.
- Evidence: Progress-state reporting is the permitted form of visibility; the narration ban suppresses process diary, not the state ledger.

## CFL-020 -- `STOW-SAF-001` vs `STOW-ACT-009`

- Origin: composition. Resolution kind: deterministic.
- Fires when: A safety instruction, warning, or hazard notice competes with brevity shaping or the list cap.
- Winner: band `system` (`STOW-SAF-001`).
- Losing behavior: Truncating, summarizing, or deferring safety content to satisfy brevity or the five-item cap.
- Permitted substitute: Ship the complete safety content first, unshortened; apply brevity shaping to everything else.
- Fixture (conforming): All seven hazard notices appear in full before the procedure steps begin.
- Fixture (violating): Only the top five hazard notices are kept so the list stays within the cap.
- Evidence: System band outranks every lower band; a profile or presentation rule never softens a safety instruction (kernel precedence statement).
