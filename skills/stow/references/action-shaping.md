# Action-shaping reference

Application guidance for the ACT rule group (`category: action-shaping`, eleven
records `STOW-ACT-001`..`011`). These rules shape the surface form of a
user-facing reply so the reader can act on it. They all carry
`precedence: presentation` (the lowest tier, so they yield to `profile` and
`system` rules) and `activation: always-user-facing` (they apply whenever the
response is user-facing, and never inside `code`, `structured-data`,
`quoted-text`, or `identifiers`).

This file is a scanned surface: it tells STOW *when* each rule fires, *which
region* of the output it governs, and *how* the check runs. It does not restate
the rules themselves. For the normative wording of any rule, open the
`corpus_ref` cited under it. Shared entry shape below: **Trigger** (the
observable condition in a draft that makes the rule relevant), **Region** (where
in the output to look), **Check** (the registry `enforcement` mechanism), and
the corpus citation.

## Per-rule application

**STOW-ACT-001: Action-first response opening**
- Trigger: the draft's first line announces intent, greets, or clears its
  throat before anything actionable appears.
- Region: line one of the reply.
- Check: `heuristic` validator `lead-with-action` inspects the opening line.
- Full text: see corpus/action-shaping.md#STOW-ACT-001

**STOW-ACT-002: Numbered steps for multi-step work**
- Trigger: the work decomposes into more than one ordered step, but the draft
  renders it as running prose or undifferentiated bullets.
- Region: the body of any procedure or plan.
- Check: `heuristic` validator `numbered-multistep`.
- Full text: see corpus/action-shaping.md#STOW-ACT-002

**STOW-ACT-003: Close with a single concrete next step**
- Trigger: work remains open at the end of the turn and the final line does not
  point to exactly one next step (or points to several).
- Region: the last line of the reply.
- Check: `semantic-review` (no deterministic validator); a review pass confirms
  the closer names one concrete action.
- Full text: see corpus/action-shaping.md#STOW-ACT-003

**STOW-ACT-004: Defer secondary issues**
- Trigger: a side observation or "by the way" aside is spliced into the main
  answer.
- Region: the body, between the primary action and its close.
- Check: `deterministic` validator `no-inline-tangents`.
- Full text: see corpus/action-shaping.md#STOW-ACT-004

**STOW-ACT-005: Restate progress each turn**
- Trigger: a continuing multi-turn task where the new turn assumes the reader
  still holds prior state in memory.
- Region: the status line at the top of each turn.
- Check: `semantic-review`; a review pass confirms current state is visible on
  screen, not implied.
- Full text: see corpus/action-shaping.md#STOW-ACT-005

**STOW-ACT-006: Concrete effort estimates**
- Trigger: the reply proposes work whose size or duration the reader must weigh.
- Region: wherever proposed work is introduced.
- Check: `semantic-review`. Conflict: `STOW-PRO-002` (require attributable
  numbers) outranks this on accuracy: supply an estimate only when a defensible
  range exists, otherwise omit it rather than invent a number.
- Full text: see corpus/action-shaping.md#STOW-ACT-006

**STOW-ACT-007: Surface completed outcomes**
- Trigger: work ran and produced a result, but the outcome is buried in the
  body or left implicit.
- Region: the result or status area after an action runs.
- Check: `heuristic` validator `surface-outcomes`.
- Full text: see corpus/action-shaping.md#STOW-ACT-007

**STOW-ACT-008: Neutral error reporting**
- Trigger: a failure or error is being reported with an alarmed or apologetic
  opener.
- Region: the line that first reports the failure.
- Check: `deterministic` validator `no-alarm-openers`.
- Full text: see corpus/action-shaping.md#STOW-ACT-008

**STOW-ACT-009: Bound action lists to five items**
- Trigger: an enumerated list of actions exceeds five entries.
- Region: any action list in the reply.
- Check: `deterministic` validator `list-max-5-items` (`limit: 5`).
- Full text: see corpus/action-shaping.md#STOW-ACT-009

**STOW-ACT-010: No preamble, recap, or sign-off**
- Trigger: the reply opens with framing before the content or ends with a recap
  or closing pleasantry.
- Region: the first and last lines (the reply's framing).
- Check: `deterministic` validator `no-preamble-or-signoff`. Pairs with
  `STOW-ACT-001` (opening) and `STOW-ACT-003` (close).
- Full text: see corpus/action-shaping.md#STOW-ACT-010

**STOW-ACT-011: Lists, not tables, for action sequences**
- Trigger: a table encodes steps or actions the reader is meant to perform in
  sequence.
- Region: any tabular block that carries actions.
- Check: `heuristic` validator `no-action-tables`; convert the table to a
  numbered list under `STOW-ACT-002`.
- Full text: see corpus/action-shaping.md#STOW-ACT-011

## Secondary modules

Three module files support the group. Cite them for the reasoning and the
pre-send discipline; do not inline their content.

- **When the defaults yield**: the conditions under which an ACT rule is
  correctly overridden (for example, an explicit request to explain at length,
  or a destructive action that must be confirmed first). See
  corpus/action-shaping.md
- **Pre-send gates**: the ordered hard checks to run on a draft before it is
  sent, including the first-line, last-line, tangent, table, and scan gates.
  See corpus/action-shaping.md
- **Rationale**: the reader model that motivates the whole group. See
  corpus/action-shaping.md

## Precedence note

Every ACT rule is `presentation` tier. Where an ACT rule meets a `profile` or
`system` rule, the higher tier wins. The one recorded intra-registry conflict is
`STOW-ACT-006` against `STOW-PRO-002`, resolved in favor of factual accuracy as
noted under that rule above.
