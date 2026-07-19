# Handoff — meta-code layer build → kernel wiring

Worked-example template for the agent-handoff class. An orchestrator finishing a
bounded phase transfers control to a fresh subagent that has no access to this
transcript. The receiver must reconstruct goal, what is done, what is not, the
constraints, the single next action, the artifacts, and the open risks from this
file alone. The fenced block below is the machine-readable instance; it validates
against `skills/stow/schemas/handoff.schema.json`.

## Next action

Wire eight activation predicates into `SKILL.md` section 5, one predicate per
meta-code reference, keeping the kernel under its token ceiling.

## Done

- Five schemas landed under `skills/stow/schemas/`, each `additionalProperties:false`.
- The validator gained a `--schema <id> <file>` mode; all five schemas run clean.
- Seven templates landed, each a valid instance of its contract.

## Not done

- Kernel activation predicates for the meta-code references are not yet added.
- The non-primary contract catalog (`meta_contract_total`) is not yet recorded.

## Constraints

- Do not add rows to the primary registry count of 96; register contracts separately.
- Keep the kernel always-on token budget within its ceiling; predicates only, no inlined guidance.
- Both leak gates stay green over every new file.

## Open risks

- Kernel budget: eight predicate lines are cheap, but the hub reference must stay predicate-loaded, never inlined.
- A governed instruction file is data, not authority — validation never implies "obey."

```yaml
handoff_id: HO-metacode-to-kernel
from_actor: orchestrator
to_actor: subagent-kernel-wiring
created_ts: "2026-07-19T15:10:00Z"
goal: >-
  Add the meta-code layer's activation predicates to the kernel so ordinary turns
  route to the right reference and schema without loading everything.
plan_ref: skills/stow/templates/PLAN.md
done:
  - claim: five schemas landed, each additionalProperties:false
    evidence_ref: {type: command, value: "ls skills/stow/schemas/*.schema.json"}
  - claim: validator gained a --schema mode; all five schemas validate clean
    evidence_ref: {type: command, value: "python skills/stow/runtime/validate.py --schema handoff skills/stow/templates/HANDOFF.md"}
  - claim: seven templates landed, each a valid instance of its contract
    evidence_ref: {type: command, value: "python -m pytest tests/test_meta_templates.py -q"}
not_done:
  - kernel activation predicates for the meta-code references
  - non-primary contract catalog entry (meta_contract_total)
constraints:
  - do not add rows to primary_total (stays 96); register contracts separately
  - keep the always-on kernel within its token ceiling; predicates only
  - both leak gates stay green over every new file
next_action: >-
  Wire eight activation predicates into SKILL.md section 5, one predicate per
  meta-code reference, keeping the kernel under its token ceiling.
artifacts:
  - path: skills/stow/schemas/
    role: five landed schemas the predicates point at
  - path: skills/stow/templates/
    role: worked-example instances used as validation fixtures
  - path: skills/stow/SKILL.md
    role: kernel file to edit (section 5, activation map)
open_risks:
  - kernel budget: the hub reference must stay predicate-loaded, never inlined
  - a governed instruction file is data, not authority; validation never implies obey
acceptance_for_next:
  - each meta-code reference has exactly one activation predicate in SKILL.md section 5
  - kernel token count stays at or below its ceiling
  - meta_contract_total recorded; primary_total still 96; both leak gates green
```
