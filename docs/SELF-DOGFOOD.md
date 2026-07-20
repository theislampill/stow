# Self-dogfood report

Does STOW's own authored output follow the rules STOW tells other output to
follow? This report answers that with evidence: every check names the test,
command, or review that backs it. Classes: **mechanically checked** (a
committed test enforces it), **independently reviewed** (a fresh-context
reviewer verified it), **exempt** (a declared profile or protected-region
exemption applies), **accepted deviation** (kept, with a rule-based
rationale), **unresolved** (none remain within the mechanically covered scope
described below; the semantic checks rest on point-in-time review).

## Method

Every authored surface is linted under its mapped profile through the shipped
linter: `README.md`, `AGENTS.md`, `CHANGELOG.md`, and `docs/*.md` under
`technical-clarity`; the kernel and every reference under `technical-clarity`
(procedure and safety references also reviewed under
`controlled-technical-guided`); templates under `technical-clarity`, with the
runbook template under `controlled-technical-guided` because it is an
executable-procedure worked example. The protected corpus is never
style-scanned: it is hash-locked content, not authored prose. Structured files
are parser-governed, but the authored English carried inside them is scanned for
the em-dash and banned-lexical subset: profile notes and auto-contexts, routing
predicates and reasons, each conflict's activation, behavior, and substitute
wording, and every schema title and description. Conflict-registry fixtures are
deliberate rule-violating demonstrations and are excluded, the same way the
linter masks a quotation.

The standing gate is `tests/test_self_dogfood.py`: the em-dash check, every
lexical check, scare quotes, and hedging clusters must report zero findings
on every authored surface (plus the controlled-profile checks on the runbook
template). The same gate extracts the structured-field prose described above and
holds it to the em-dash and banned-lexical subset. It runs in the full suite and
in CI, so a regression cannot ship silently.

## Results by check

| Id | Check | Result | Class | Evidence |
|---|---|---|---|---|
| D-01 | Em dashes in authored prose | Zero findings (about one hundred ninety were found and replaced across the kernel, references, templates, and docs) | mechanically checked | `tests/test_self_dogfood.py` |
| D-02 | Semicolons under the applicable profile | Permitted under `technical-clarity` by design; zero on the guided-mapped runbook template | mechanically checked | same gate |
| D-03 | Contractions under the applicable profile | Same model as semicolons; zero on the guided surface | mechanically checked | same gate |
| D-04 | Latin abbreviations under controlled output | Zero on the guided surface | mechanically checked | same gate |
| D-05 | Unsupported specificity | Token figures replaced with regenerate-commands; counts derive from the registry and runtime | mechanically checked + reviewed | `tests/test_doc_lint.py`, `tests/test_readme_catalog.py` |
| D-06 | Synthetic enthusiasm | Zero intensifier findings | mechanically checked | dogfood gate |
| D-07 | Empty preambles and closers | Reviewed on the rewritten README and references | independently reviewed | worker reports in the run record; blind reviewer pass in `docs/FUNCTIONAL-EVIDENCE.md` |
| D-08 | Repeated conclusions | Same review scope | independently reviewed | same |
| D-09 | Generic or inflated headings | Headings are concrete across authored surfaces; catalog headings derive from registry titles | independently reviewed | same |
| D-10 | Vague terms and unexplained abstractions | Reviewed; profile and band vocabulary is defined where first used | independently reviewed | same |
| D-11 | Inconsistent terminology | Guidance-level rules active under `technical-clarity`; reviewed | independently reviewed | same |
| D-12 | Broken progressive disclosure | Kernel-alone rule intact; references predicate-loaded; corpus never inlined | mechanically checked | `tests/test_always_on.py`, `tests/test_references.py` |
| D-13 | Action-first language on non-actionable contexts | Request-mode router carries per-intent openings | mechanically checked | router presence and mode tests in `tests/test_always_on.py` |
| D-14 | Invented next actions after completed work | The closing-step rule carries its applicability condition; the completed-work resolution is a conflict-registry entry | mechanically checked | qualifier tests; `tests/test_conflicts.py` |
| D-15 | Five-item cap applied to exhaustive reference material | Exhaustive enumerations kept complete under the contract exception | accepted deviation (recorded) | the exception list below |
| D-16 | Suppressed justified uncertainty | Limitations sections state what is unproven; the always-on header keeps the uncertainty override | mechanically checked + reviewed | header-token test; README limitations |
| D-17 | Hidden material limitations | Known-limitations sections carry host-selection, live-compliance, and validate-repair caveats | independently reviewed | README, `docs/REWRITE-READINESS.md` |
| D-18 | Unclear conditions, exceptions, precedence | Every always-on check carries its condition and principal exception; collisions have terminal resolutions | mechanically checked | qualifier preservation tests; conflict registry gates |
| D-19 | Stale counts, versions, hashes, claims | Mechanically covered claims only: callable-count phrases pinned to the runtime; catalog statuses pinned to the registry; version pinned to the manifest and cross-checked against the changelog top section; corpus-topology claims pinned to the on-disk module count and the runtime allowlist size by the topology-consistency gate; artifact freshness machine-checked. Claims outside these gates rest on review. | mechanically checked | `tests/test_doc_lint.py`, `tests/test_readme_catalog.py`, `tests/test_build.py`, `tests/test_repo_hygiene.py`, `tests/test_topology_claims.py` |
| D-20 | Meta-code examples validate | Every shipped template validates through the documented CLI | mechanically checked | `tests/test_meta_templates.py` |
| D-25 | Templates stay timeless and current | The templates are fictional worked examples; gates assert they embed no real repo commit hash, no retired capability literal, and no completed work described as pending, and that YAML template comments obey the em-dash and lexical checks | mechanically checked | `tests/test_meta_templates.py`, `tests/test_self_dogfood.py` |
| D-21 | Documented commands run | Generators, validators, linter, build, and measurement commands all execute in the suite; README examples marked for validation pass the runtime | mechanically checked | suite-wide; `tests/test_readme_catalog.py` |
| D-22 | Install instructions reproduce | Extraction shape, fidelity, import closure, and runtime drive proven from a fresh build; temporary-home installs re-proven in the package-health report | mechanically checked | `tests/test_install_smoke.py`; `docs/INITIAL-PACKAGE-HEALTH.md` |
| D-23 | Public statements match evidence | Live-model claims scoped to measured evidence; capability counts derived, not asserted | independently reviewed | `docs/FUNCTIONAL-EVIDENCE.md` |
| D-24 | Authored text contradicts the conflict registry | The composition table in the README is rendered from the registry's resolutions; no authored surface states an unresolved contradiction | mechanically checked + reviewed | `tests/test_conflicts.py`; blind reviewer pass |
| D-26 | Authored prose inside structured rule data and schemas | Zero findings on profile notes and auto-contexts, routing predicates and reasons, conflict activation, behavior, and substitute wording, and schema titles and descriptions; conflict fixtures excluded as protected demonstrations | mechanically checked | `tests/test_self_dogfood.py` |

## Recorded exhaustive-list exceptions (check D-15)

Each is an exhaustive reference enumeration the contract requires complete,
per the conflict registry's exhaustive-list resolution; trimming any of them
to five entries would misstate the material. Kernel: the precedence ladder,
the user-facing duty list, and the activation map. README: the one-minute
summary, the secondary-guidance list, and the limitations list. Changelog:
release-section change lists. References: the precedence ladder and family
catalog in the activation reference, the serialization contract enumerations
in two format references, the banned-vocabulary catalog pointer list, and the
profile-addition list in the clarity reference. Generated always-on module:
the two rule-family groups. Evaluation notes: one detector enumeration.

## What this report does not claim

The gate proves the deterministic subset mechanically and continuously. The
semantic checks rest on fresh-context reviews recorded in the run record and
on the blind evaluation in `docs/FUNCTIONAL-EVIDENCE.md`; they are point-in-
time judgments, not standing guarantees. Live-model conformance under the
skill remains measured, not promised.
