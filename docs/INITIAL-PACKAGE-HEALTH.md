# Initial package health

> **Scope note.** This is the historical 0.3.1 package-health report. Superseded
> metrics below, including the runtime module count and the version, are stated
> as-of that release. Current state is covered by the CHANGELOG sections from
> 0.3.2 onward and by `docs/RULE-USABILITY.md`.

Status of the shipped artifact `dist/STOW.skill` as a fresh install, verified
on 2026-07-20 against version 0.3.1. Every check below ran against the built
package or the tracked tree that produces it; raw command captures live in the
governed run record outside the repository.

## Install paths

- **Plugin path.** A temporary plugin home built from the packaged artifact
  (never a real user home) resolves under `--plugin-dir`: the host loads the
  manifest, lists the skill, and invokes it. The packaged evaluation harness
  (`tools/ab_eval_runner.py`) builds exactly this layout for every enabled-arm
  run, so the path is exercised dozens of times per evaluation round, and
  `tests/test_install_smoke.py` gates it in CI.
- **Direct archive path.** Extracting `dist/STOW.skill` into a temporary
  skills directory yields `stow/SKILL.md` at the documented location, and the
  three runtime modules work from the extracted copy: `runtime/validate.py`
  validates a JSON fixture, `runtime/profiles.py` resolves the
  `controlled-technical` alias to its guided profile, and
  `runtime/lint_prose.py` lints the packaged `SKILL.md` under the
  technical-clarity profile with advisory-only exit status.

## Package integrity

- The archive is a spec-compliant ZIP with the single top-level directory
  `stow/`; every entry name passes the identity sweep.
- `dist/manifest.json` records the artifact digest and is regenerated with the
  build; `tests/test_build.py` gates archive shape, entry set, and digest
  freshness against the tracked sources.
- The build is deterministic: rebuilding from an unchanged tree reproduces the
  recorded digest.

## Reference and claim hygiene

- A dead-reference scan over every tracked markdown file resolved each
  relative link and each backticked repository path. It found one dangling
  pointer: the corpus self-check pass names a banned-list reference file that
  had never been created. The repair adds
  `references/ai-writing-detection.md` as a pointer to the single normative
  home of the banned lists (`corpus/prose-integrity/banned-lists.md`) and to
  the packaged linter that parses them at runtime. No corpus wording changed.
- A stale-claim scan found no outdated digest, version, or total in tracked
  docs: the README rule totals and catalog are generated and drift-checked,
  the changelog names only versions that exist, and the plugin manifest
  carries the current version.

## Verification surfaces

- The full test suite passes offline: it is stdlib-only by construction, makes
  no network calls, and gates corpus hashes, registry consistency, profile
  resolution, conflict generation, always-on freshness, README catalog
  freshness, count-leak rules, self-dogfood lint, provenance, and package
  shape.
- All four generators (`gen_rule_index`, `gen_always_on`,
  `gen_rule_conflicts`, `gen_readme_catalog`) confirm their outputs are
  current in check mode.
- The self-dogfood gate holds: the deterministic lint subset reports zero
  findings on every STOW-authored surface under its mapped profile (see
  `docs/SELF-DOGFOOD.md`).

## Known limits

- Host execution approval: in non-interactive host runs, reading packaged
  files works but executing the packaged validator can require interactive
  approval. The skill's guidance covers this case: when a checker cannot run,
  the artifact still ships alone, with no commentary about the missing check.
- Functional efficacy evidence, including the enabled-versus-disabled
  comparison, lives in `docs/FUNCTIONAL-EVIDENCE.md`.
