# Changelog

All notable changes to STOW are recorded in this file. The format follows
Keep a Changelog, and STOW versions follow Semantic Versioning.

## [Unreleased]

Nothing yet.

## [0.3.3] - 2026-07-20

Integrity corrections across the lookup helper, the public docs, and governance.

### Changed

- The packaged rule lookup helper (`runtime/query_rules.py`) now states its
  deployment truthfully: it ships inside the runtime allowlist. Its profile
  membership honors every selector kind (the always-on-for-prose selector,
  category-prefix selectors, and explicit guidance rules), it prints an
  always-on rule's applicability and exception, and it lists the composition
  conflicts from `rules/conflicts.yaml` that name the rule alongside the
  per-record registry conflicts.
- The kernel and the generated rule index route a single-rule lookup to
  `runtime/query_rules.py` when execution is available, and otherwise to a
  bounded registry read: locate the record by its sentinel line, read to the
  next sentinel, then read only the anchored corpus section. Full-registry
  ingestion is reserved for complete audits.
- Public-doc topology drift corrected: the README, the readiness sheet, the
  design notes, and the package-health report now describe the grouped
  anchored-module corpus (twenty modules, every rule addressable by a stable
  heading anchor) instead of the retired per-rule-module and per-turn-load
  phrasings. The README documents the lookup helper.
- The README catalog renders each rule's authored applicability, with its
  exception appended, in place of the family bucket when the qualifier exists.
- The kernel makes the protected-literal exception explicit: a supplied literal
  stays byte-for-byte exact unless the request itself asks for that literal to
  be edited, which the output contract band already outranks.

### Added

- A topology-consistency gate (`tests/test_topology_claims.py`): the README
  carries no per-rule-module claim, the corpus-module count in prose is derived
  from the on-disk modules, the AGENTS.md runtime allowlist claim tracks
  `build_skill.RUNTIME_ALLOW`, the manifest entry count matches the package
  walk, and `plugin.json` matches the top released changelog section.
- Extended lookup-helper tests: selector-aware membership for the always-on and
  controlled-only rules, applicability and exception presence, and a
  composition-conflict listing. `tests/test_query_rules.py` is bound to the
  runtime-code artifact class.

### Notes

- The packaged corpus, rule meanings, profile semantics, conflict resolutions,
  and the primary rule total are unchanged; the artifact was rebuilt so its
  digest reflects the truthful helper docstring and the kernel and rule-index
  routing text.

## [0.3.2] - 2026-07-20

Corpus topology consolidation and rule-usability governance.

### Changed

- Consolidated the per-rule corpus files into twenty anchored modules. Every
  rule keeps its exact wording and is addressable by a stable heading anchor;
  the kernel documents how to read one section from a module. All embedded
  corpus citations were migrated and are now resolution-checked.
- Added a machine-readable routing map validated against the kernel activation
  map, an artifact-class governance map binding every packaged file to its
  required checks, and a packaged rule lookup helper
  (runtime/query_rules.py, optional acceleration; plain file reads remain the
  contract).
- The registry now carries grep-seekable sentinel lines so one record can be
  located without ingesting the whole file.

## [0.3.1] - 2026-07-20

Public identity normalization and rule-catalog completion.

### Changed

- Normalized the wording of retained guidance so every public surface and the
  packaged skill are fully STOW-native. Rule meaning, scope, thresholds,
  examples, exceptions, and safety force are preserved; each replacement was
  narrowly scoped, ledgered, and independently reviewed. The pre-normalization
  baseline text remains preserved outside the public tree, and the future
  comparative rewrite gate still measures candidates against that preserved
  baseline.
- Corpus fidelity claims now describe the public model truthfully: modules are
  hash-locked and internally consistent; per-module wording metadata records
  which modules carry identity-neutralized wording.
- Strengthened raw-artifact delivery guidance from measured evaluation
  findings: the always-on router row and the format references now state that
  a raw artifact is composed once and shipped alone, with no
  draft-then-correction and no validation notes in the reply; the skill
  activation description now names exact-output-contract requests so hosts
  invoke the skill on raw-artifact prompts.
- Added the banned-list pointer reference named by the corpus self-check
  pass, closing the one dangling link found by the dead-reference scan.
- Version 0.3.1 (the packaged corpus changed); the artifact was rebuilt and
  its digest re-recorded.

### Fixed

- Corrected an invalid GitHub expression context in the verification workflow:
  the tokenizer cache directory was set in a job-level `env:` block using the
  `runner` context, which GitHub rejects at workflow parse before any job
  runs. The directory is now exported from a run step via `GITHUB_ENV`.

### Added

- Workflow semantic validation: a pinned, checksum-verified `actionlint`
  gate runs in CI over every workflow file, and a regression test pins the
  expression-context placement class that caused the rejection
  (`tests/test_workflow_contexts.py`).

### Notes

- The workflow fix itself changed no packaged skill bytes; the 0.3.1 digest
  change comes from the wording normalization above.

## [0.3.0] - 2026-07-19

Composition-hardening pass: named profiles with one shared resolver, runtime
activation that matches the registry, a machine-readable conflict registry, an
operational always-on module that keeps its conditions, meta-code contracts
that validate end to end, offline-hermetic measurement, and machine-enforced
repository hygiene.

### Added

- `rules/profiles.json` + shipped `runtime/profiles.py`: the single profile
  declaration (ids, aliases, lock state, auto-precedence, per-profile check
  gating) consumed by the linter, the generators, the kernel map, and the
  tests. `technical-clarity` is now a real, documented, tested profile;
  `controlled-technical` survives as a deprecated alias of
  `controlled-technical-guided`; the strict profile refuses resolution with an
  error naming the lock.
- `rules/conflicts.yaml` + `tools/gen_rule_conflicts.py`: the machine-readable
  conflict registry (twenty entries covering the sixteen hardened collision
  classes), from which `docs/rule-conflicts.md` is now genuinely generated and
  drift-checked in CI.
- Operational qualifiers: registry records carry STOW-authored
  `activation.applicability` and `activation.exception` fields, and the
  generated always-on module renders every check as id + action + condition +
  exception + corpus pointer, opened by a request-mode router and an explicit
  accuracy/safety yield note. Tests fail if a qualifier disappears from the
  operational form.
- Meta-code hardening: `event`, `plan`, and `runbook` validator schemas (the
  interchange meta-contract catalog is unchanged); optional `schema_version`
  and `profile` fields on the instance schemas; `x-` prefix escapes on status
  vocabularies with the lifecycle-ownership boundary documented; Markdown
  fence extraction, per-line `.jsonl` validation, and the evidence-record
  `{records: [...]}` wrapper in `validate.py --schema`; and a test that
  validates every shipped template against its schema through the real CLI.
- Offline-hermetic measurement: `tools/measure_context.py` never downloads,
  records its measurement method, and falls back to a deterministic
  conservative estimate when the tokenizer cache is absent; the full suite
  passes with no network access.
- Hygiene gates: a tracked-tree junk scan, a committed-artifact freshness test
  (the committed `dist/` set must byte-match a fresh build), and a CI step
  asserting the working tree stays clean after the run.

### Changed

- The prose linter gates the controlled-family checks (semicolon, contraction,
  Latin abbreviations, both sentence caps) behind
  `controlled-technical-guided`, exactly as the registry activation predicates
  declare; previously the contraction, Latin-abbreviation, and sentence-cap
  checks ran on every prose turn regardless of profile. Structured artifacts
  receive no prose findings, and `--exhaustive-list-ok` records a contract's
  permission for a complete list.
- The five Markdown/YAML templates were corrected to validate against their
  schemas (gate `state` -> `status` keys, string evidence references, acceptance
  ids with matching evidence entries, a single-string `acceptance_for_next`).
- `dist/manifest.json` now carries the product version and no
  build-environment strings, so the manifest reproduces across hosts.
- README, design notes, and this changelog were aligned with the shipped
  runtime: fourteen rules have callable validators (previous docs said one),
  the profiles table reflects `rules/profiles.json`, the validator
  documentation covers the new instance modes, and token figures are
  regenerated on demand instead of hardcoded.

### Corrections

- The 0.1.0 known-limitations entry "The validator CLI exposes `--format`
  only, with no schema argument" was already stale when written: the
  `--schema` mode shipped in the richness pass below.

## [0.2.0] - 2026-07-19

Richness pass (previously tracked as unreleased work toward v0.2): deepen the
authored surfaces and the repository documentation without changing the
shipped rule set.

### Added

- The meta-code layer: five interchange schemas under `skills/stow/schemas/`,
  seven worked-example templates under `skills/stow/templates/`, seven
  coordination references, and the `validate.py --schema <id> <file>` mode
  with its cross-field post-checks.
- Fourteen callable prose validators in `runtime/lint_prose.py`, with the
  enforcement-status honesty gate deriving the callable set bidirectionally
  from the runtime.
- The generated always-on operational module (`references/always-on.md`) and
  the kernel routing that applies the always-on families on every user-facing
  prose turn.
- `AGENTS.md`: the working-rules contract for agents and contributors: the
  source-name-free surface rule, the two-gate leak model, the canonical
  registry, the verbatim-corpus and local-provenance rules, the invariant
  primary rule total, and byte-exact build reproducibility.
- `CHANGELOG.md`: this file.
- Repository-surface tests asserting the new authored surfaces exist, pass the
  source-name gate, and carry their required sections.
- Install-smoke gate: extraction shape, sampled fidelity, import closure, and
  runtime drive of the packaged modules.

### Changed

- Expanded the README and docs coverage: positioning, install, quick start,
  examples, profiles, validator usage, and known limitations: as
  source-name-free, count-leak-safe prose.

### Notes

- Every addition registers outside the invariant primary rule total, which is
  unchanged.
- Every new surface stays source-name-free and count-leak-safe.

## [0.1.0] - 2026-07-19

Mechanical baseline: the first self-contained release.

### Added

- STOW kernel (`SKILL.md`): 8-band precedence, the typed-region model, the
  always-on integrity and user-facing-output rules, and a predicate-gated
  reference activation map.
- Machine-readable rule registry (96 primary rules) with its schema, plus a
  generated rule index and a cross-rule conflict report.
- Three-tier context architecture: kernel, reference modules, and the complete
  verbatim corpus (one module per rule).
- Runtime validators: JSON, JSONL, and YAML checking (`validate.py`) and a
  report-only prose lint (`lint_prose.py`).
- Structured-output format references (JSON, JSONL, YAML, Markdown) and profile
  references (controlled-technical writing, conformance, safety, procedures,
  descriptions).
- Deterministic `dist/STOW.skill` build with a SHA-256 sidecar and a manifest.
- Test suite and evaluations (baseline, behavioural, adversarial) with CI wiring
  and the anti-leak gate.

### Known limitations

- The strict, fully-conformant controlled-technical profile is locked in this
  release.
- Evaluations assert detector contracts only; there is no live-model harness.
- The validator CLI exposes `--format` only, with no schema argument.
