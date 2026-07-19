# Runbooks

A **runbook** is an operational procedure a human or an agent executes under time
pressure or during an incident — a deploy, a rebuild-and-republish, a rollback, a
recovery. Determinism and safety are paramount: a step that reads two ways or a
command that is paraphrased can cause harm, so a runbook is held to the strictest
procedural and safety families in STOW.

This page is a scanned surface, not rule text. For the wording of any governed
prose rule named below, open its cited `corpus_ref` module.

## When this page applies

- **Predicate:** an operational or incident procedure will be run step by step,
  possibly under pressure, where each command must be copy-pastable and each
  risk must be visible before the step runs.

## Governing STOW families

- **Procedures (profile, band 7).** Each step is short, a single imperative
  instruction, and any leading condition is set off first — see
  corpus/procedures/stow-prc-001.md, corpus/procedures/stow-prc-002.md,
  corpus/procedures/stow-prc-003.md, and corpus/procedures/stow-prc-004.md.
- **Safety (band 1, system precedence, always on).** Every step that can cause
  loss carries a risk-level label and a stated consequence, and outranks any
  presentation or profile preference — see corpus/safety/stow-saf-001.md,
  corpus/safety/stow-saf-002.md, and corpus/safety/stow-saf-003.md.
- **Verbs (profile, band 7).** Instructions stay imperative and active, per
  corpus/verbs/stow-vrb-006.md.
- **Literals (band 4).** Command bodies and paths are protected literals, byte-exact
  and unchanged by any prose scan.

## Governing schema + template

- **Schema.** A runbook is a Markdown artifact whose contract is declared by
  `schemas/output-contract.schema.json` with `content_type: markdown` and a region
  map that marks each command body as a protected literal. The schema governs the
  envelope; the procedure and safety families above govern the step prose.
- **Template.** `templates/RUNBOOK.md` — a valid instance with preconditions, a
  success check, numbered imperative steps, per-step `verify` and `rollback`, and
  labeled safety cautions.

## Validation contract

Validate the runbook document (its fenced step-list block) against the runbook
schema; when a runbook travels between harnesses inside an envelope, the
envelope validates separately as an output contract:

```
python skills/stow/runtime/validate.py --schema runbook templates/RUNBOOK.md
```

The load-bearing rules: each step is imperative and singular; every step that can
fail has a `verify` and a `rollback`; every safety step carries a risk-level label
and a consequence; `preconditions` and a `success_check` are present; command
bodies match their region map as protected literals. **Cold-reader gate:** an
operator can run the runbook end to end from the document alone, with no
out-of-band knowledge of the system.
