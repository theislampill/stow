# Activation and precedence

STOW governs one model response by reading it as a set of output regions and
applying each rule only inside the region it owns, at the precedence band where
it sits. This page is the map that ties those two ideas together: the precedence
ladder, how a response is split into regions, and how the registry's
`precedence` field lands on the ladder.

This is a scanned surface, not rule text. It names rules by their registry id
and title (both STOW-authored) and points to each rule's `corpus_ref`; it never
restates a rule's normative wording. For what a rule says, open its
corpus file. For the masking mechanism that keeps a rule off the regions it does
not own, see the companion page `skills/stow/references/protected-regions.md`.

Shared entry shape below, matching the sibling references: the observable
**trigger**, the output **region** it governs, **how STOW checks it** (the
registry `enforcement` mechanism), and the `corpus_ref` citation.

## The precedence ladder

Bands, highest to lowest:

1. **System / safety / legal / platform.** Non-negotiable constraints and any
   safety notice.
2. **User output contract.** An explicit format the user pinned (a required
   schema, a template, "answer in one line"). Host-supplied, not a registry
   record.
3. **Serialization / schema validity.** The output must still parse: valid JSON,
   YAML, well-formed markup.
4. **Protected literals / identifiers.** Quoted text, keys, file paths, URLs,
   code-like tokens reproduced byte-for-byte.
5. **Factual accuracy + calibrated uncertainty.** No invented numbers, dates,
   attributions; hedge only where warranted.
6. **Domain terminology.** The right term for the subject, used consistently.
7. **Active writing profile.** The controlled-technical family and its
   procedural, descriptive, and safety sub-profiles.
8. **STOW presentation preferences.** Surface-shaping and prose-integrity
   defaults.

**Invariant:** a lower band never corrupts an output governed by a higher band.
When two rules touch the same span, the higher band wins and the lower-band rule
yields for that span; it does not partially apply. A rule also never reaches
outside its own region (next section). The registry encodes the known collisions
ahead of time under each record's `conflicts[]`, always resolved toward the
higher band.

## Output-region classification

A single response mixes regions: editable prose, a procedure, a description,
structured data, code, quotations, and identifiers can all appear in one reply.
Each rule declares `scope.include` (the regions it governs), `scope.exclude`
(the regions it must never touch), and an `activation.predicate` (whether it is
live at all). STOW classifies each span into a region, then applies only the
rules whose include-region matches and whose predicate holds.

Regions and the band that owns each:

- **Editable prose**: general (`all-prose`), procedural (`procedural-prose`),
  descriptive (`descriptive-prose`), safety (`safety-prose`), or user-facing
  (`user-facing-output`). Governed by bands 5 through 8.
- **Structured data** (`structured-data`) and **code** (`code`): owned by band
  3. Validated for well-formedness by `skills/stow/runtime/validate.py`, never
  rewritten by a prose rule.
- **Quotations** (`quoted-text`) and **identifiers** (`identifiers`): owned by
  band 4, immutable.
- **Safety notices**: owned by band 1, independent of any active profile.

Nearly every controlled-technical and presentation record carries the same
`scope.exclude: [code, structured-data, quoted-text, identifiers]`. That uniform
exclusion is the invariant in data form: those regions belong to higher bands (3
and 4), so a band 7 or band 8 prose rule is structurally forbidden from touching
them. The mask-then-scan ordering in `protected-regions.md` enforces it
mechanically.

## Mapping the registry `precedence` field onto the ladder

The registry stores one of three values in each record's `precedence`. They land
on the ladder as:

- **`system` -> band 1.** Only the safety rules. Their predicate fires on the
  presence of a safety notice, not on any writing profile, so this governance is
  always live. See `skills/stow/references/safety-instructions.md`.
- **`profile` -> band 7.** The controlled-technical rule families. Predicate: a
  controlled-technical writing profile is active and the response contains the
  matching prose region.
- **`presentation` -> band 8.** The action-shaping and prose-integrity families.
  Predicate is region presence alone, independent of the controlled-technical
  profile, so they govern user-facing output broadly.

Bands 2 and 4 through 6 are not `precedence` values; they are the host and
context constraints the STOW bands sit beneath. Band 2 is whatever output
contract the user pinned, and it outranks every STOW band: when the user fixes a
format, the profile and presentation preferences yield to it. Bands 4 through 6
surface in the registry only through declared `conflicts[]` (the cross-band
section below).

## Band 1: safety (always live)

- **Trigger:** the response emits a safety instruction, warning, caution, or
  hazard notice. Not gated on any writing profile.
- **Region:** the `safety-prose` block only; excludes code, structured data,
  quoted text, and identifiers.
- **How STOW checks it:** the three SAF rules run semantic-review and parser
  validators per notice (`STOW-SAF-001`..`003`).
- Because these outrank the profile and presentation bands, a lower-band lexical
  or layout preference never suppresses or reshapes a safety notice.
- See corpus/safety/stow-saf-001.md, corpus/safety/stow-saf-002.md,
  corpus/safety/stow-saf-003.md (and the per-rule breakdown in
  `skills/stow/references/safety-instructions.md`).

## Band 7: controlled-technical profile

Live only when a controlled-technical profile is active and the matching region
is present. Every family below excludes code, structured data, quoted text, and
identifiers, and none auto-fixes. Per family: trigger add-on, region, check
kind, and corpus directory.

- **Words** (`STOW-WRD-001`..`014`): trigger: profile active + prose present;
  region: editable prose; check: approved-word, part-of-speech, sense, and
  inflection validators (semantic-review, parser, deterministic). See
  corpus/words/.
- **Multi-word nouns** (`STOW-MWN-001`..`002`): region: prose; check: parser
  word-count and heuristic. See corpus/multiword-nouns/.
- **Verbs** (`STOW-VRB-001`..`007`): region: prose; check: parser form, tense,
  and voice validators plus a nominalization heuristic. See corpus/verbs/.
- **Sentences** (`STOW-SEN-001`..`005`): region: prose; check: parser and
  semantic-review. See corpus/sentences/.
- **Procedures** (`STOW-PRC-001`..`005`): trigger add-on: procedural or safety
  instructions present; region: `procedural-prose`; check: deterministic word
  caps plus parsers (imperative form, one instruction per sentence,
  condition-then-comma). See corpus/procedures/ and
  `skills/stow/references/controlled-technical-writing.md`.
- **Descriptions** (`STOW-DSC-001`..`006`): region: `descriptive-prose`; check:
  deterministic caps plus semantic-review of topic and paragraph structure. See
  corpus/descriptions/ and `skills/stow/references/descriptions.md`.
- **Punctuation** (`STOW-PCT-001`..`007`): region: prose; check: deterministic
  and heuristic (including the word-count token rules). See corpus/punctuation/.
- **Style** (`STOW-STY-001`..`004`): region: prose; check: semantic-review,
  heuristic, and parser. See corpus/style/.
- **General grammar** (`STOW-GEN-001`..`008`): region: prose; check: parser,
  heuristic, deterministic, and semantic-review. See corpus/general/.

## Band 8: presentation preferences

Live on region presence alone; no writing profile is required.

- **Action-shaping** (`STOW-ACT-001`..`011`): trigger: the response is
  user-facing; region: `user-facing-output`; check: heuristic, deterministic,
  and semantic-review validators covering opening, ordering, list caps, tone,
  and framing. See corpus/action-shaping/ and
  `skills/stow/references/action-shaping.md`.
- **Prose-integrity** (`STOW-PRO-001`..`024`): trigger: prose sentences present
  (a few fire only when section headings, or an external quotation, are
  present); region: editable prose, always excluding the protected regions;
  check: deterministic lexical scans and semantic-review. See
  corpus/prose-integrity/.

## Cross-band conflicts (the invariant in action)

The registry pre-declares each collision under `conflicts[]` with a resolution;
every one resolves by the higher band winning. The load-bearing cases:

- **Protected regions vs a presentation or profile lexical rule.** `STOW-PRO-021`
  and the profile lexical rules `STOW-WRD-014` and `STOW-PCT-006` yield inside
  `quoted-text`, `identifiers`, and `structured-data`: bands 3 and 4 outrank
  bands 7 and 8, so keys, identifiers, and quoted text are never re-spelled or
  re-cased. See corpus/prose-integrity/stow-pro-021.md,
  corpus/words/stow-wrd-014.md, corpus/punctuation/stow-pct-006.md.
- **Factual accuracy vs an estimate preference.** `STOW-ACT-006` yields to
  `STOW-PRO-002`: band 5 forbids presenting an unsupported number as fact, so an
  estimate is given only when a defensible range exists and is otherwise omitted.
  See corpus/action-shaping/stow-act-006.md,
  corpus/prose-integrity/stow-pro-002.md.
- **Domain terminology and profile consistency vs a variation preference.**
  `STOW-PRO-007` yields to `STOW-WRD-011` and `STOW-STY-004`: bands 6 and 7 keep
  one term per referent and consistent wording for recurring content. See
  corpus/prose-integrity/stow-pro-007.md, corpus/words/stow-wrd-011.md,
  corpus/style/stow-sty-004.md.
- **Profile length caps vs the same variation preference.** `STOW-PRO-007` also
  yields to `STOW-PRC-001` and `STOW-DSC-003`: vary sentence length below the
  profile's cap, never above it. See corpus/procedures/stow-prc-001.md,
  corpus/descriptions/stow-dsc-003.md.
- **Two punctuation bans on one substitution.** `STOW-PRO-001` (presentation)
  and `STOW-PCT-001` (profile) collide because the profile-band ban removes a
  substitute character the presentation-band rule would otherwise reach for. The
  resolution uses neither character and lets the active profile choose the
  replacement. See corpus/prose-integrity/stow-pro-001.md,
  corpus/punctuation/stow-pct-001.md.

## How to read a finding

For any STOW finding, place it on the ladder before acting on it: identify the
rule's `precedence` band and the region it governs, confirm the span is
in that region and not a protected literal, then resolve upward: a higher-band
finding on the same span wins. Read the cited `corpus_ref` for the rule's
wording; this page only tells you where the rule lives and when it fires.
