# Rule usability

Historical evidence about whether primary rules were reachable and usable in a
bounded package and host evaluation. Measured
against the consolidated 0.3.2 package; the full coverage matrix, probe
captures, and per-rule evidence live in the governed run record outside the
repository.

## What was checked, per property

- **Reachability, all 96 then-current starting rules.** Every registry record resolves; every
  corpus anchor exists exactly once in its module; every baseline statement
  is byte-present in its anchored section with explanation beyond it; every
  module hash matches the drift-lock manifest.
- **Activation observations.** Live host probes per profile and region
  family, with mandatory negatives: raw artifacts suppress prose references,
  protected regions do not activate prose rules, the locked strict profile
  refuses without silent activation, and a question about a nonexistent rule
  id draws no invented rule. Some individual probes hit the known
  host invocation-skip class and are recorded as blocked-host evidence; every
  rule had at least one observed family-level activation path in that run.

The activation results are historical, single-host behavioral evidence; they do
not prove automatic selection for every rule, prompt, model, or host.
- **Application observations.** A fresh-context model given each anchored section produced
  a compliant artifact for all 96 then-current starting rules and identified
  and corrected a planted violation for all 96 starting rules. Blind reviewers, shown artifacts without rule
  ids, independently named the exact violated rule for 67 rules and quoted
  the offending span; the shortfall is an attribution limit of the blind
  evaluation, not a rule failure: in most cases the reviewer flagged the
  correct span but attributed it to an overlapping sibling rule, and in six
  cases a low-salience violation read as ordinary prose without the rule
  text. These cells are recorded as evaluation-attribution limits, separately
  from any runtime claim. They do not turn a semantic rule into a callable check.
- **Conflict behavior, all entries.** Every conflict-registry entry passed
  its structural checks; deterministic entries verified through the runtime
  where a callable check exists; every semantic entry judged blind with the
  declared winner upheld and the losing behavior yielding.
- **Callable checks.** Every rule with a callable validator was driven
  through the real runtime in both directions: the violating fixture is
  flagged and the clean fixture is not.

## Honesty boundary

Fourteen rules have callable runtime checks; only their closed detector
contracts are mechanically evidenced. Every other cell is model-behavior evidence and is labeled
model-compliance variance or evaluation-attribution limit. Passing one blind
application test does not make a semantic rule mechanically enforced, and
this page makes no such claim.

## Architecture verdict

No such defect was found in the recorded probes and structural checks. This is
not a universal semantic-classification or protected-region claim.
The known host constraints (invocation skip on short prompts, denied
non-interactive execution of packaged checkers) are environment classes,
recorded as such in the run record.
