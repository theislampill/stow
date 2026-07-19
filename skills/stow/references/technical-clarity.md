# The technical-clarity profile

Native architecture reference for the `technical-clarity` profile declared in
`rules/profiles.json`. It governs technical prose that coordinates work
without being a controlled executable procedure.

## When it activates

Automatically, for: technical explanations, architecture descriptions, agent
handoffs, implementation plans, audit reports, runbooks, state and continuity
records, and structured task instructions surrounding code. It can also be
selected explicitly (`--profile technical-clarity` on the runtime linter).

When the same artifact also matches a more specific profile, the
auto-precedence order in `rules/profiles.json` decides: an executable
procedure or safety instruction promotes to `controlled-technical-guided`.

## What it adds over stow-default

Everything in `stow-default` (the always-on families, protected regions,
accuracy, progressive disclosure) plus review-level discipline:

- One term per concept, held stable across the artifact (guidance rule
  `STOW-WRD-011`).
- Consistent wording for recurring content such as repeated steps, labels,
  and cautions (guidance rule `STOW-STY-004`).
- Stable names for artifacts, gates, and actors across turns and documents.
- Bounded steps: each instruction names its actor, action, and completion
  condition.
- Explicit conditions: state when a step applies, not only what it does.
- Evidence-aware claims: tie each claim to the artifact, measurement, or gate
  that supports it, and keep justified uncertainty.

The two guidance rules are review-level. They activate as discipline for the
writer and reviewer; no mechanical check enforces them under this profile,
and the runtime linter reports them under `guidance_active` in its output
rather than as findings.

## What it does not do

- Mechanical checks are identical to `stow-default`: no semicolon ban, no
  contraction ban, no Latin-abbreviation ban, no sentence-length caps.
- It makes no controlled-language conformance claim of any kind. Conformance
  language stays governed by `references/conformance.md`.

## Meta-code binding

Meta-code artifacts (handoffs, plans, audits, runbooks, state records, task
packets, event streams; see `references/meta-code.md`) bind to this profile
by default. An artifact that is an executable procedure or a safety
instruction promotes to `controlled-technical-guided`.
