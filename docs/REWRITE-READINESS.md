# Rewrite readiness

Verdict sheet for opening the governed comparative rewrite phase (candidate
wordings measured against the retained verbatim baseline). The rewrite phase
must not start while any behavioral-composition blocker below is open.

| Gate | Verdict | Evidence |
|---|---|---|
| Profiles stable | **PASS** | One declaration (`rules/profiles.json`) + one shipped resolver (`runtime/profiles.py`) consumed by the linter, generators, kernel map, and tests. Alias, lock, precedence, shape, and consistency gates in `tests/test_profiles.py`; the README profile table matches the declaration. |
| Conflicts terminal | **PASS** | Twenty machine-readable entries in `rules/conflicts.yaml`, every one naming a winner band, losing behavior, and permitted substitute; registry edges imported verbatim with string-equality cross-checks; same-band pairs carry operational tie-breaks; `docs/rule-conflicts.md` generated and drift-checked (`tests/test_conflicts.py`). |
| Runtime activation aligned | **PASS** | Scope-fidelity gate: every profile-gated callable check is silent outside `controlled-technical-guided` and red under it; predicate-drift gate: the resolver's controlled include set equals the registry predicate set; the full target-behavior matrix (contraction, semicolon, em dash, Latin abbreviations, both sentence caps, list cap, exhaustive-list permission, quoted spans, raw artifacts) passes (`tests/test_profiles.py`). |
| Corpus fidelity | **PASS** | Twenty anchored corpus modules, hash-locked and internally consistent, each carrying per-module drift locks (per-module wording metadata records which modules carry identity-neutralized wording; the pre-neutralization baseline is preserved outside the public tree); 96/96 registry baseline hashes verified; drift-lock and mutation self-tests green; `wording.candidates` empty and `rewrite_status: deferred` on all 96 records. |
| Behavioral host evidence | **AVAILABLE (non-hermetic, labeled)** | A repeatable enabled-versus-disabled evaluation (`tools/ab_eval_runner.py`, `tests/evals/ab/`; summarized in `docs/FUNCTIONAL-EVIDENCE.md`): twenty fixed cases, three reps per case per arm, across three rounds (a baseline round, a post-repair checkpoint, and a final round on the shipped package), each round pinning one package digest for every run. Blind evaluators in four roles score anonymized output pairs on a frozen rubric; every format and schema verdict comes from the packaged mechanical validators. Four sealed hold-out prompts, hash-pinned in `prompts.yaml`, run only in the final round. In the final round the enabled arm auto-selected the skill and loaded the kernel-predicted references, produced schema-valid capability artifacts where the disabled arm produced none, and improved the mechanical measures (raw-output parses, fence discipline, hazard-first ordering, fewer em dashes). One critical-invariant miss is recorded rather than argued away: a single rep of the raw-YAML case emitted a code fence. Single-host, one pinned model per round: treated as evidence, not universal proof. |
| Remaining blockers before candidate generation | **NONE (composition)** | No open composition conflict, profile leak, stale public claim, or offline test dependency. |
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
- The controlled dictionary is out of scope and `controlled-technical-strict`
  stays locked; dictionary-dependent checks remain unavailable and say so.

## What the rewrite phase inherits

Candidate generation and comparative evaluation can rely on: stable profile
ids and activation semantics; terminal conflict resolutions with fixtures; a
runtime whose check scope equals the registry's declared scope in both
directions; hash-locked baselines with per-record digests; and an operational
always-on form that preserves each rule's conditions, so a candidate wording
is compared against what the rule states, under the activation it
carries.
