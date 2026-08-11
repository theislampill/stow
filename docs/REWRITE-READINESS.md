# Rewrite readiness

This sheet records the earlier production-baseline checkpoint. The active
reconciliation supersedes its readiness verdicts: registry migration is in
progress and surviving G1 semantics still require qualifying paired behavioral
evidence. Historical evidence below is not current-candidate qualification.

| Gate | Verdict | Evidence |
|---|---|---|
| Profiles stable | **PASS** | One declaration (`rules/profiles.json`) + one shipped resolver (`runtime/profiles.py`) consumed by the linter, generators, kernel map, and tests. Alias, lock, precedence, shape, and consistency gates in `tests/test_profiles.py`; the README profile table matches the declaration. |
| Conflicts terminal | **PASS at the recorded baseline** | Each machine-readable entry in `rules/conflicts.yaml` named a winner band, losing behavior, and permitted substitute; current conflict truth is regenerated and tested separately. |
| Runtime activation aligned | **PASS at the recorded baseline** | Scope-fidelity tests covered the profile-gated contraction, semicolon, Latin-abbreviation, and sentence-cap observations plus the profile-independent em-dash advisory, quoted spans, and raw artifacts. Current-candidate qualification remains separate. |
| Corpus fidelity | **PASS** | Twenty anchored corpus modules, hash-locked and internally consistent, each carrying per-module drift locks (per-module wording metadata records which modules carry identity-neutralized wording; the pre-neutralization baseline is preserved outside the public tree); baseline hashes verified for the complete audited starting population; drift-lock and mutation self-tests green; `wording.candidates` empty and `rewrite_status: deferred` on every current record. |
| Behavioral host evidence | **HISTORICAL, NON-QUALIFYING FOR THIS CANDIDATE** | Earlier enabled-versus-disabled evidence remains useful diagnostic context, but it does not qualify the reconciled registry or establish automatic activation. |
| Remaining blockers before candidate generation | **OPEN** | Surviving G1 semantics need a repaired, budget-frozen paired challenge design and current-candidate evidence. |
| Repository verification (external gate) | **REQUIRED before rewrite initiation** | Workflow files must pass local semantic validation (pinned actionlint) before push. The exact candidate commit must trigger a GitHub Actions workflow that GitHub accepts, every required job step must run, and the final conclusion must be `success`: a workflow that merely parses, or a skipped/cancelled/neutral/partial run, is not success evidence. Exact run evidence (run id, commit, conclusion, step coverage) is recorded in the governed audit object for the run that produced the commit, not hardcoded here. Rewrite initiation stays paused until this gate passes on the current baseline. |

## Residual limitations (not blockers, carried forward)

- Prose linting is advisory by decision; live outputs showed partial always-on
  conformance (em dashes appeared in skill-invoked replies) that the linter
  reports and nothing blocks.
- On a raw-artifact request the model may not invoke the skill at all; the
  shipped validator rejects a malformed raw artifact, but skill-side shaping
  does not engage on a non-invoked turn. This is a property of on-invoke skill
  hosting, not of the rule set.
- Live evidence comes from a single host with one pinned model per round; it
  reports deltas across reps and rounds, not cross-host variance. The repeatable
  enabled-versus-disabled suite now exists (`tools/ab_eval_runner.py`,
  `tests/evals/ab/`); cross-host and cross-harness measurement remains unshipped.
- A cold lexical index supports exact membership and explicitly listed forms.
  `controlled-technical-strict` stays locked because contextual meaning,
  terminology authority, applicability, final-output validation, and delivery
  custody remain unavailable.

## What the rewrite phase inherits

Candidate generation and comparative evaluation can rely on: stable profile
ids and activation semantics; terminal conflict resolutions with fixtures; a
runtime whose check scope equals the registry's declared scope in both
directions; hash-locked baselines with per-record digests; and an operational
always-on form that preserves each rule's conditions, so a candidate wording
is compared against what the rule states, under the activation it
carries.
