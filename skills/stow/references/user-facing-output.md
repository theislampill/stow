# User-facing output shaping

This reference covers the always-on shaping of every user-facing response: the
presentation layer, not the controlled-technical writing profile. Two registry
groups carry the specifics. Action-shaping (`STOW-ACT-*`) is scoped to
`user-facing-output` and fires on every user-facing reply. Prose-integrity
(`STOW-PRO-*`) fires whenever the reply contains prose. Both sit at
`presentation` precedence, the lowest tier: where either conflicts with a
controlled-technical profile rule (`profile`) or a safety rule (`system`), the
higher tier wins and the registry stores the exact resolution on the record.

This file does not restate what any rule says. For the normative text, follow
the `corpus_ref` link. Each entry below names the observable trigger, the output
region it governs, how STOW checks it, and the corpus source to read.

## Answer first

- **Trigger:** any user-facing response.
- **Region:** the opening line (first screenful).
- **How STOW checks:** validator `lead-with-action` inspects the first line and
  flags an opening that announces intent or sets up context instead of putting
  the deliverable (result, artifact, path, or command) in first position.
- **See** corpus/action-shaping.md#STOW-ACT-001.

## Bounded, visible actions

- **Trigger:** the response asks the reader to perform more than one action, or
  presents an action sequence.
- **Region:** the action list block.
- **How STOW checks:** `numbered-multistep` looks for a sequence rendered as an
  ordered list (STOW-ACT-002); `list-max-5-items` bounds the count at five and
  flags overflow (STOW-ACT-009); `no-action-tables` flags a table that carries
  steps and marks it for conversion to a list (STOW-ACT-011).
- **See** corpus/action-shaping.md#STOW-ACT-002,
  corpus/action-shaping.md#STOW-ACT-009,
  corpus/action-shaping.md#STOW-ACT-011.

## Progressive disclosure

- **Trigger:** any user-facing response; enforced more tightly when prose is
  present.
- **Region:** the opening, the closing, and any inline sidebar.
- **How STOW checks:** `no-preamble-or-signoff` flags an intent-announcing
  opener, a recap, or a closing pleasantry at the edges (STOW-ACT-010);
  `no-inline-tangents` flags a secondary issue raised mid-answer, which is
  deferred to a single offer at the end (STOW-ACT-004); the prose-layer
  `no-filler-phrases` check removes throat-clearing (STOW-PRO-011).
- **See** corpus/action-shaping.md#STOW-ACT-004,
  corpus/action-shaping.md#STOW-ACT-010,
  corpus/prose-integrity/rules.md#STOW-PRO-011.

## Close on the next step

- **Trigger:** work is still open when the turn ends.
- **Region:** the last line.
- **How STOW checks:** STOW-ACT-003 (semantic review) inspects the closer for
  exactly one concrete next action rather than a recap or an open-ended
  "anything else?"; it pairs with the closing half of `no-preamble-or-signoff`.
- **See** corpus/action-shaping.md#STOW-ACT-003.

## Carry state across turns

- **Trigger:** a task that spans more than one turn.
- **Region:** a short status line near the top of each turn.
- **How STOW checks:** STOW-ACT-005 (restate-state, semantic review) checks that
  each turn re-states where the work stands; `surface-outcomes` checks that
  completed results are made visible rather than left implicit (STOW-ACT-007).
- **See** corpus/action-shaping.md#STOW-ACT-005,
  corpus/action-shaping.md#STOW-ACT-007.

## Effort estimates, only when defensible

- **Trigger:** the reader asks how long or how large a piece of work is.
- **Region:** the estimate phrase.
- **How STOW checks:** STOW-ACT-006 prefers a specific range, but it conflicts
  with the attributable-number rule (STOW-PRO-002) and yields to it. The
  registry resolution: give a range only when a defensible basis exists,
  otherwise omit it; factual accuracy outranks the estimate preference, and an
  unsupported number must not be presented as fact.
- **See** corpus/action-shaping.md#STOW-ACT-006,
  corpus/prose-integrity/rules.md#STOW-PRO-002.

## Errors as cause, effect, correction

- **Trigger:** the response reports a failure, error, or blocked step.
- **Region:** the error sentence or sentences.
- **How STOW checks:** `no-alarm-openers` flags an alarm word at the start and
  keeps the report matter-of-fact (STOW-ACT-008). Structure the report so the
  reader gets the cause, then the effect, then the correction, in that order.
- **See** corpus/action-shaping.md#STOW-ACT-008.

## Prose quality inside user-facing output

- **Trigger:** the response contains prose sentences outside code, quoted text,
  and structured data. Section headings are a distinct sub-region.
- **Region:** all such prose; headings where called out.
- **How STOW checks:** the prose-integrity validators run always-on at
  presentation precedence. The ones that most shape user-facing tone:
  - Filler and machine tells: `no-filler-phrases`, `no-ai-transitions`,
    `no-ai-verbs`, `no-academic-tells` (STOW-PRO-011, -020, -021, -022).
  - Synthetic enthusiasm and empty intensifiers: `no-synthetic-enthusiasm`,
    `no-intensifiers` (STOW-PRO-014, -004).
  - Concrete headings: `no-heading-parentheticals`, `concrete-headings`
    (STOW-PRO-003, -016); a heading names the subject, not an abstraction.
  - Justified uncertainty: `no-weasel-words` (STOW-PRO-015) removes empty
    hedging, but honest, load-bearing uncertainty is kept; do not manufacture
    doubt and do not fake confidence. See also the unsourced-number check
    (STOW-PRO-002) and the performative-urgency check (STOW-PRO-009).
  - Presentation-layer punctuation: the em dash ban `no-em-dash` (STOW-PRO-001).
- **See** the prose-integrity corpus group under corpus/prose-integrity/, in
  particular corpus/prose-integrity/rules.md#STOW-PRO-011,
  corpus/prose-integrity/rules.md#STOW-PRO-020,
  corpus/prose-integrity/rules.md#STOW-PRO-021,
  corpus/prose-integrity/rules.md#STOW-PRO-022,
  corpus/prose-integrity/rules.md#STOW-PRO-014,
  corpus/prose-integrity/rules.md#STOW-PRO-004,
  corpus/prose-integrity/rules.md#STOW-PRO-003,
  corpus/prose-integrity/rules.md#STOW-PRO-016,
  corpus/prose-integrity/rules.md#STOW-PRO-015,
  corpus/prose-integrity/rules.md#STOW-PRO-002,
  corpus/prose-integrity/rules.md#STOW-PRO-009,
  corpus/prose-integrity/rules.md#STOW-PRO-001.

## Precedence and conflicts

All action-shaping and prose-integrity rules are `presentation` precedence,
the lowest tier. Inside a controlled-technical writing profile the profile rules
win; safety rules (`system`) always win. Where the registry records a conflict
(for example STOW-PRO-007 against the sentence-length caps, or STOW-PRO-001
against the semicolon rule), apply the resolution stored on that record rather
than the shaping preference here.
