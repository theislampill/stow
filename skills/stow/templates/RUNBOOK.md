# Runbook: rebuild and republish the STOW skill artifact

Worked-example template for the runbook class. Because an operator (human or
agent) executes this under time pressure, every step is a single imperative.
Every step that can fail carries a `verify` and a `rollback`. Every safety step
states a risk level and its consequence. Commands are protected literals: copy
them exactly. The fenced block is the machine-readable step list.

## Preconditions

- Working tree is clean (`git status` shows nothing to commit).
- All gates are green (tests pass, and both leak gates report `LEAK CHECK PASSED`).

## Steps

1. Run the full test suite.
   - Verify: exit code is zero.
   - Rollback: none (read-only).
2. Run the anti-leak gate over the tree.
   - Verify: output ends with `LEAK CHECK PASSED`.
   - Rollback: none (read-only).
3. Build the artifact.
   - Verify: two consecutive builds are byte-identical.
   - Rollback: delete the build output directory.
4. CAUTION (medium): publishing replaces the live artifact. Consequence: installed
   agents pick up the new build on next load. Publish only after steps 1–3 are green.
   - Verify: the published artifact's short SHA matches the local build.
   - Rollback: republish the previous release.

## Success check

The published artifact matches the local build byte-for-byte and both leak gates
pass over the extracted artifact.

## Safety

- CAUTION (high): never `git push --force`. Consequence: remote history is
  rewritten and every clone diverges. Push fast-forward only.
- To undo a bad release, revert to the last known-good commit `5e3aafe` and
  rebuild. Do not rewrite history.

```yaml
schema_version: 1
profile: controlled-technical-guided
runbook_id: RB-rebuild-republish
preconditions:
  - clean working tree
  - all gates green
steps:
  - n: 1
    action: run the full test suite
    verify: exit code is zero
    rollback: none
    risk: none
  - n: 2
    action: run the anti-leak gate over the tree
    verify: output ends with LEAK CHECK PASSED
    rollback: none
    risk: none
  - n: 3
    action: build the artifact
    verify: two consecutive builds are byte-identical
    rollback: delete the build output directory
    risk: low
  - n: 4
    action: publish the artifact
    verify: published short SHA matches the local build
    rollback: republish the previous release
    risk: medium
    consequence: installed agents pick up the new build on next load
success_check: published artifact matches the local build and both leak gates pass on extract
```
