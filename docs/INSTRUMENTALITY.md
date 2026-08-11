# STOW instrumentality

Controlled-language semantic ownership is regression-locked in
`docs/controlled-language-coverage.yaml`; retired rule identity and disposition
history remain in `docs/rule-dispositions.yaml`.

This document separates writing guidance, callable checks, host custody, and
package evidence. The distinction prevents a useful instruction or a passing
checker from being reported as control over a model's final response.

## G1 to G4

G1 generation guidance is model-mediated instruction: it can improve a draft,
but it does not deterministically govern the model's output.

G2 mechanical detection returns a deterministic verdict only for a closed,
observable input contract.

G3 delivery gating exists only when a named host gives the detector the actual
final candidate, blocks failure and unknown, repairs only where permitted, and
revalidates before delivery.

G4 build and package proof establishes repository or artifact integrity, not
semantic prose behavior.

This repository contains no general G3 host integration.

## Current components

| Component | Layer | Actual consumer | Bounded result | Direct evidence | Hot or cold cost | Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Compact kernel and descriptive prose guidance | G1 | Model or host that reads the files | Presents precedence, routing cues, and observable prose harms | Static routing, structure, and budget tests | Kernel is compact; deeper prose guidance is cold | Compliance remains model-mediated |
| Profile resolver | G2 composition helper | Explicit caller, prose linter, generators, and tests | Resolves an id or alias, rejects a lock, and answers check-gating queries | Profile and routing tests | Small standard-library module; loaded by its callers | Does not infer intent from request text |
| Advisory prose linter | G2 detector | Explicit CLI or library caller | Reports closed lexical and structural findings over its masked input | Bidirectional fixtures and profile tests | Runtime scan plus term-table read when called | Findings are advisory; unreadable input has no blocking prose verdict |
| `validate.py` | G2 detector | Explicit CLI or library caller | Parses supported formats or checks one shipped schema | Parser, schema, fence, package, and install tests | Called only for a requested check; existing YAML and schema dependencies | Knows only the supplied file and selected mode |
| `validate_terms.py` | G2 detector | Explicit CLI caller | Checks declared variants in caller-labeled segments | Boundary, ambiguity, label-premise, package, and install tests | Standard-library scan loaded only for an explicit term map | Trusts caller segmentation and has no concept or sense inference |
| Protected-span masking | G2 preprocessing | Advisory prose linter | Blanks a finite set of recognizable spans while retaining positions | Masking geometry and exclusion tests | Paid only when the linter runs | Does not compare a composed final response with supplied source bytes |
| Build, leak, freshness, and install checks | G4 | Contributor workflow and CI | Check named repository files, package bytes, extraction, imports, and sampled runtime calls | Build, hygiene, leak, and install suites | Development and packaging cost; no turn-time prose cost | Scope is the enumerated readable targets and tested environment |
| Historical A/B evidence | Evidence about G1 plus selected G2 outcomes | Maintainers and reviewers | Records bounded enabled-versus-disabled observations on one pinned host per round | Governed run record and committed summary | Offline evaluation cost; not ordinary-turn cost | Behavioral, package-bound, and not universal |

## Selection, checking, and custody boundaries

Reference and profile selection are model- or host-mediated unless a caller
explicitly supplies a profile identifier.

The profile resolver resolves identifiers, aliases, locks, precedence data, and
check gating; it does not semantically classify a request.

The prose linter is advisory: findings, zero findings, or unreadable input do
not establish semantic correctness, authorship, or delivery acceptance.

The structured and closed-term validators are G2 detectors; they become part
of G3 only under the explicit host conditions above.

Protected-span masking is finite, read-only preprocessing for advisory scans,
not a general final-output preservation or restoration mechanism.

## Cost evidence

Static context figures measure declared file bundles with one tokenizer or a
character estimator; they do not prove live host reads, tokens, latency, tool
calls, or repair cost.

The fallback estimator is deterministic for its character formula and
historically conservative on the calibrated files, but it is not a universal
token upper bound.

Load-path labels describe the intended file bundle for a routing predicate.
They become observations about a live host only when telemetry records the
actual reads for that host and run.
