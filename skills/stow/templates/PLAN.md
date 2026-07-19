# Plan — build the meta-code layer

Worked-example template for the implementation-plan class. It turns a goal into an
ordered, reviewable set of phases with acceptance criteria and gates, executable by
a different session and survivable when picked up cold. Each task has an `id`, an
observable `acceptance`, and a `gate`; dependencies form a DAG with no cycles;
every phase has a defined terminal state; no task is an orphan. The fenced block is
the machine-readable task DAG.

## Phase P0 — schemas

Author the five schemas as JSON-Schema-2020-12 with `additionalProperties:false`.

## Phase P1 — validator schema mode

Add `--schema <id> <file>` to the validator; add the cross-field post-checks that
JSON-Schema alone cannot express.

## Phase P2 — templates

Author seven worked-example templates, each a valid instance of its contract.

## Phase P3 — kernel wiring + catalog

Add one activation predicate per reference; record `meta_contract_total` outside
the primary count of 96.

```yaml
plan_id: PLAN-metacode
tasks:
  - id: T-schemas
    phase: P0
    depends_on: []
    acceptance: five *.schema.json parse and reject an additional property
    method: schema
    gate: G-schemas
  - id: T-validator-mode
    phase: P1
    depends_on: [T-schemas]
    acceptance: "validate.py --schema handoff FILE exits zero on a valid instance"
    method: command
    gate: G-validator
  - id: T-templates
    phase: P2
    depends_on: [T-validator-mode]
    acceptance: each of seven templates validates against its contract
    method: schema
    gate: G-templates
  - id: T-kernel-wiring
    phase: P3
    depends_on: [T-templates]
    acceptance: each meta-code reference has exactly one predicate in SKILL.md section 5
    method: parse
    gate: G-kernel
  - id: T-catalog
    phase: P3
    depends_on: [T-schemas]
    acceptance: meta_contract_total recorded; primary_total still 96
    method: command
    gate: G-catalog
phases:
  - id: P0
    terminal_state: schemas-authored
  - id: P1
    terminal_state: validator-schema-mode-runnable
  - id: P2
    terminal_state: templates-valid
  - id: P3
    terminal_state: kernel-wired-and-cataloged
```
