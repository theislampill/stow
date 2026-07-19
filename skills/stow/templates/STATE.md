# State — meta-code layer build

Worked-example template for the state / continuity class. This is the durable,
externalized state of a multi-session effort: any session can resume from it
without re-deriving. The fenced block validates against
`skills/stow/schemas/state.schema.json`. Every gate state is terminal or in
flight with an evidence reference; every supersession link resolves to a real
decision id.

## Current

- Head: `5e3aafe` (v0.1 baseline).
- Phase: P-meta — templates landed, kernel wiring next.
- Next action: add eight activation predicates to the kernel.

## Gate ledger

| Gate | State | Evidence |
|---|---|---|
| Meta schemas + validator mode | done | `validate.py --schema` runs all five schemas clean |
| Meta templates | done | `tests/test_meta_templates.py` passes |
| Kernel activation wiring | in-progress | predicates being added to SKILL.md section 5 |
| Contract catalog + leak gates | planned | `meta_contract_total` to record; gates green over new files |

## Decisions

- MD-1 Contracts register outside the primary count — decided.
- MD-2 Each Markdown template embeds one schema-valid block — decided.
- MD-3 Superseded by MD-4 — statements-only templates rejected.
- MD-4 Every template is a filled worked example, not a skeleton — decided.

## Andons

- A-1 Handoff `next_action` carried two imperatives — resolved (split to one).

```yaml
run_id: meta-code-build-20260719
updated_ts: "2026-07-19T15:20:00Z"
history_append_only: true
current:
  head: "5e3aafe"
  phase: P-meta
  next_action: add eight meta-code activation predicates to SKILL.md section 5
gates:
  - id: G-schemas
    state: done
    evidence_ref: {type: command, value: "python skills/stow/runtime/validate.py --schema state skills/stow/templates/STATE.md"}
  - id: G-templates
    state: done
    evidence_ref: {type: command, value: "python -m pytest tests/test_meta_templates.py -q"}
  - id: G-kernel-wiring
    state: in-progress
    evidence_ref: {type: file-line, value: "skills/stow/SKILL.md:45-61"}
  - id: G-catalog-and-leak
    state: planned
    evidence_ref: {type: command, value: "python tools/check_provenance_leak.py --local skills/stow/templates"}
decisions:
  - id: MD-1
    status: decided
  - id: MD-2
    status: decided
  - id: MD-3
    status: superseded
    superseded_by: MD-4
  - id: MD-4
    status: decided
    supersedes: [MD-3]
andons:
  - id: A-1
    class: contract-violation
    state: resolved
    resolution: handoff next_action reduced to a single imperative
```
