# Rewrite readiness

Verdict sheet for opening the governed comparative rewrite phase (candidate
wordings measured against the retained verbatim baseline). The rewrite phase
must not start while any behavioral-composition blocker below is open.

| Gate | Verdict | Evidence |
|---|---|---|
| Profiles stable | **PASS** | One declaration (`rules/profiles.json`) + one shipped resolver (`runtime/profiles.py`) consumed by the linter, generators, kernel map, and tests. Alias, lock, precedence, shape, and consistency gates in `tests/test_profiles.py`; the README profile table matches the declaration. |
| Conflicts terminal | **PASS** | Twenty machine-readable entries in `rules/conflicts.yaml`, every one naming a winner band, losing behavior, and permitted substitute; registry edges imported verbatim with string-equality cross-checks; same-band pairs carry operational tie-breaks; `docs/rule-conflicts.md` generated and drift-checked (`tests/test_conflicts.py`). |
| Runtime activation aligned | **PASS** | Scope-fidelity gate: every profile-gated callable check is silent outside `controlled-technical-guided` and red under it; predicate-drift gate: the resolver's controlled include set equals the registry predicate set; the full target-behavior matrix (contraction, semicolon, em dash, Latin abbreviations, both sentence caps, list cap, exhaustive-list permission, quoted spans, raw artifacts) passes (`tests/test_profiles.py`). |
| Corpus fidelity | **PASS** | 110/110 modules byte-exact against their locked sources; 96/96 registry baseline hashes verified; drift-lock and mutation self-tests green; `wording.candidates` empty and `rewrite_status: deferred` on all 96 records. |
| Behavioral host evidence | **AVAILABLE (non-hermetic, labeled)** | Thirteen live cases on one host (claude CLI 2.1.201, plugin session-load, no real-home install) with direct Skill-invocation and per-file Read telemetry: the skill auto-selected on every task-shaped, technical, and meta-code case and loaded exactly the kernel-predicted references for procedures, safety, and meta-code artifacts. Shipped-validator grading closed the loop: the live raw-JSON artifact validated clean, a malformed raw-YAML turn was rejected, and the live meta-code artifacts were recognizably shaped but not schema-exact (the validator rejected each approximation, which is the contract layer doing its job; the validate-repair-revalidate loop is the documented workflow). Single-run, single-host, one model: treated as evidence, not proof. A second harness was present but blocked by its own local configuration; two others were absent. |
| Remaining blockers before candidate generation | **NONE (composition)** | No open composition conflict, profile leak, stale public claim, or offline test dependency. |

## Residual limitations (not blockers, carried forward)

- Prose linting is advisory by decision; live outputs showed partial always-on
  conformance (em dashes appeared in skill-invoked replies) that the linter
  reports and nothing blocks.
- On a raw-artifact request the model may not invoke the skill at all; the
  shipped validator rejects a malformed raw artifact, but skill-side shaping
  does not engage on a non-invoked turn. This is a property of on-invoke skill
  hosting, not of the rule set.
- Live evidence is one run per case on one host and one model; no variance or
  cross-host measurement exists yet. A repeatable host-native evaluation suite
  with a with/without-skill arm remains the roadmap item.
- The controlled dictionary is out of scope and `controlled-technical-strict`
  stays locked; dictionary-dependent checks remain unavailable and say so.

## What the rewrite phase inherits

Candidate generation and comparative evaluation can rely on: stable profile
ids and activation semantics; terminal conflict resolutions with fixtures; a
runtime whose check scope equals the registry's declared scope in both
directions; byte-locked baselines with per-record hashes; and an operational
always-on form that preserves each rule's conditions, so a candidate wording
is compared against what the rule actually says, under the activation it
actually has.
