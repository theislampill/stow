# Changelog

All notable changes to STOW are recorded in this file. The format follows
Keep a Changelog, and STOW versions follow Semantic Versioning.

## [Unreleased]

Richness pass toward v0.2: deepen the authored surfaces and the repository
documentation without changing rule behaviour or the shipped rule set.

### Added

- `AGENTS.md`: the working-rules contract for agents and contributors — the
  source-name-free surface rule, the two-gate leak model, the canonical
  registry, the verbatim-corpus and local-provenance rules, the invariant
  primary rule total, and byte-exact build reproducibility.
- `CHANGELOG.md`: this file.
- Repository-surface tests asserting the new authored surfaces exist, pass the
  source-name gate, and carry their required sections.

### Changed

- Expanded the README and docs coverage — positioning, install, quick start,
  examples, profiles, validator usage, and known limitations — as
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
