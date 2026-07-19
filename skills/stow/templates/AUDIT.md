# Audit — meta-code layer readiness

Worked-example template for the audit / evidence class. A read-only reviewer
produces findings a decision-maker acts on. FACTS are separated from
RECOMMENDATIONS; every record carries a verifiable locator and reaches a terminal
disposition — no orphan findings. The fenced block validates against
`skills/stow/schemas/evidence-record.schema.json`. A `fact` needs at least one
resolvable locator; a `finding` with `verified: true` needs a `failure_scenario`;
`disposition` is one of the terminal set
`{fixed, already-covered, rejected-with-evidence, owner-decision, blocked, deferred}`.

## Verdict

The meta-code contracts are declared but not runnable until the validator gains a
schema mode. One deferred finding, one recommendation, one confirmed fact.

## Facts

- Schema validation is declared in the kernel integrity gate but no schema-runner ships yet.

## Findings

- Templates without a runnable schema mode cannot be enforced as fixtures; they drift silently.

## Recommendations

- Add a `--schema <id> <file>` mode to the validator, reusing the existing result shape.

```yaml
records:
  - record_id: F-1
    kind: fact
    statement: >-
      The kernel integrity gate requires "parse or schema-check", but the shipped
      validator exposes only format validators, so schema conformance is not runnable.
    locators:
      - {type: file-line, value: "skills/stow/SKILL.md:33"}
      - {type: file-line, value: "skills/stow/references/format-json.md:50-53"}
    severity: medium
    disposition: deferred
    verified: true
  - record_id: N-1
    kind: finding
    statement: >-
      A meta-code template with no runnable schema mode cannot be gated as a fixture,
      so a field can be dropped or mistyped without any check failing.
    locators:
      - {type: command, value: "python -m pytest tests/test_meta_templates.py -q"}
    severity: high
    disposition: fixed
    verified: true
    failure_scenario: >-
      An editor removes handoff.next_action; with no schema gate the template still
      "looks" valid, and a cold reader receives a handoff with no next action.
  - record_id: R-1
    kind: recommendation
    statement: >-
      Add a --schema mode to skills/stow/runtime/validate.py that loads
      skills/stow/schemas/<id>.schema.json and returns the existing Result shape.
    locators:
      - {type: file-line, value: "skills/stow/runtime/validate.py:280-284"}
    severity: medium
    disposition: owner-decision
    verified: false
```
