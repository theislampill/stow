# State: meta-code layer build

Worked-example template for the state / continuity class. This is the durable,
externalized state of a multi-session effort: any session can resume from it
without re-deriving. The fenced block validates against
`skills/stow/schemas/state.schema.json`. Every gate state is terminal or in
flight with an evidence reference; every supersession link resolves to a real
decision id.

## Current

- Head: `5e3aafe` (v0.1 baseline).
- Phase: P-meta (templates landed, kernel wiring next).
- Next action: add eight activation predicates to the kernel.

## Gate ledger

| Gate | Status | Evidence |
|---|---|---|
| Meta schemas + validator mode | done | `validate.py --schema` runs the shipped schemas clean |
| Meta templates | done | `tests/test_meta_templates.py` passes |
| Kernel activation wiring | active | predicates being added to SKILL.md section 5 |
| Contract catalog + leak gates | pending | `meta_contract_total` to record; gates green over new files |

## Decisions

- MD-1 Contracts register outside the primary count: accepted.
- MD-2 Each Markdown template embeds one schema-valid block: accepted.
- MD-3 Superseded by MD-4: statements-only templates rejected.
- MD-4 Every template is a filled worked example, not a skeleton: accepted.

## Andons

- A-1 Handoff `next_action` carried two imperatives: resolved (split to one).

```yaml
schema_version: 1
profile: technical-clarity
run_id: meta-code-build-20260719
updated_ts: "2026-07-19T15:20:00Z"
history_append_only: true
current:
  head: "5e3aafe"
  phase: P-meta
  next_action: add eight meta-code activation predicates to SKILL.md section 5
gates:
  - id: G-schemas
    status: done
    evidence_ref: "command: python skills/stow/runtime/validate.py --schema state skills/stow/templates/STATE.md"
  - id: G-templates
    status: done
    evidence_ref: "command: python -m pytest tests/test_meta_templates.py -q"
  - id: G-kernel-wiring
    status: active
    evidence_ref: "file-line: skills/stow/SKILL.md section 5"
  - id: G-catalog-and-leak
    status: pending
decisions:
  - id: MD-1
    status: accepted
  - id: MD-2
    status: accepted
  - id: MD-3
    status: superseded
    superseded_by: MD-4
  - id: MD-4
    status: accepted
    supersedes: [MD-3]
andons:
  - id: A-1
    class: contract-violation
    status: resolved
    resolution: handoff next_action reduced to a single imperative
```
