# Functional evidence

Measured effect of enabling the packaged skill, from the repeatable
enabled-versus-disabled evaluation defined in `tests/evals/ab/` (fixed
prompts, frozen rubric, mechanical validators, blind scoring). This page
holds the committed summary; raw outputs, transcripts, seeds, mappings,
per-evaluator scores, and telemetry live in the governed run record outside
the repository.

## Design in brief

Twenty fixed cases, three reps per case per arm, both arms on one pinned
host model (recorded per round). The enabled arm means the plugin is
available; invocation is telemetry, never forced. Sixteen general cases are
scored; four capability cases are reported separately as validator
pass-rates; four sealed hold-out prompts (hash-pinned in `prompts.yaml`) run
only in the final round and are sign-compared without gating. Blind
evaluators in four roles score anonymized output pairs on the frozen rubric;
every format and schema verdict comes from the packaged mechanical
validators, not from judgment. Three rounds ran: a baseline round, a
checkpoint after the first repair, and a final round on the shipped package;
each round pinned one package digest for every run.

## Mechanical results (final round, enabled vs disabled)

- Schema-valid capability artifacts: 10 of 12 runs vs 0 of 12. The disabled
  arm never produced a packet that validates against the packaged schemas.
- Raw-output parses (raw JSON, JSONL, YAML cases): 8 of 9 vs 6 of 9.
- Fence discipline on raw-output cases: one fence slip in twelve runs vs
  three.
- Hazard statements preceding procedure steps: 5 of 6 vs 3 of 6.
- Em-dash occurrences across prose outputs: 194 vs 243.
- Byte-exact identifier and quote preservation: both arms clean in the final
  round; the mechanical checks gate it.

## Blind comparison (final round, sixteen general cases)

Per-case medians of rep-level mean rubric scores; delta is enabled minus
disabled. Median delta +0.05, mean +0.11, with eight case wins, one loss,
and seven ties, so the pre-registered primary gate passes. Protected
dimensions (contract compliance, factual restraint, protected-region
fidelity) show no per-case regression. Both arms score near the top of the
scale on most prose cases: the host model is already strong there, so prose
deltas are small and the pre-registered prose improvement thresholds
(+0.5 on actionability and prose integrity) were not reached; the material
improvement that was reached is the mechanical one above. Hold-out signs:
two positive, two zero, none negative.

## Unmet criterion, stated plainly

The rubric requires zero enabled-arm failures of critical invariants. The
final round has one: a single rep of the raw-YAML case emitted a code fence.
The contract is stated on four packaged surfaces (kernel rule, always-on
router, format reference, activation description), the enabled arm ships
clean raw output in the other reps, and the disabled arm fenced that case in
every rep of the last two rounds. The residual is host-model compliance
variance, not missing guidance; it is retained here rather than argued away.

## What repairs the evaluation drove

- Compose-once raw delivery: the always-on router and the format references
  now state that a raw artifact ships alone, composed once, with no
  draft-then-correction and no validation notes in the reply. Driven by
  observed fenced-draft self-corrections and embedded validator commentary.
- Activation routing: the skill description names exact-output-contract
  requests, after telemetry showed hosts skipping invocation on short raw
  prompts; the affected cases then went fully clean.

## Limits

Blinding is real for prose cases and limited for schema-bearing outputs,
whose provenance is structurally recognizable; that is why format and schema
verdicts are mechanical. Evaluators and generators share a model family, so
deltas, not absolute scores, are the unit of inference. Counts are reported
descriptively with no significance claims. Host execution approval blocks
the packaged validator in non-interactive runs, which handicaps only the
enabled arm; runs where the model narrated that blocked check inside a raw
artifact are counted as failures, not excused.
