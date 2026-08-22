---
name: stow
description: "Use when asked to write/rewrite/review/validate README/runbook/procedure/plan/audit/handoff, public/controlled technical text, mixed prose/literals, or exact JSON/JSONL/YAML/Markdown. Applies exact output contracts; protects literals."
license: LICENSE
compatibility: "Agent Skills-compatible hosts; CPython 3.11; validate.py: ruamel.yaml>=0.19.1 and jsonschema>=4.26.0; others: stdlib. Installation alone runs no helper."
metadata: {author: theislampill,version: 0.4.2}
---
# STOW kernel
## 1. Precedence
Eight bands, highest first: system:safety and system directives; contract:exact request-implied output contract; serialization:structured regions must parse/validate; literal exclusions:G1 bars protected-literal edits; accuracy:no fabricated specificity, retain justified uncertainty; terminology:one term per concept, used consistently; profile:requested controlled-technical writing; presentation:user-facing shaping/prose integrity.
A lower band never corrupts a higher one. Higher bands win conflicts.
## 2. Classify output regions
Apply rules only to delimited prose/procedure/data/code/quotation/identifier regions. G1 guidance is not a shipped classifier.
## 3. Integrity rules (always on)
- Obey the exact output contract. A raw artifact ships raw: no prose wrapper, no code fence, no commentary.
- Protect identifiers/quotations/code/paths/data values unless asked to edit literal; G1 is not a byte comparator.
- Add no fabricated specificity:numbers/names/versions/citations/history; preserve justified uncertainty, not false confidence.
- Structured validity is a delivery requirement: give the actual candidate to `runtime/validate.py` when available; delivery gate must block, permit repair, and revalidate.
## 4. User-facing output
- Result first. Cut preamble, filler, and closers.
- Open with information:answer/thesis; work:bounded action; artifact:artifact; progress:state; error:cause -> effect -> correction; completion:verified result. Invent no post-completion action.
- Keep bounded, task-complete actions visible; preserve exhaustive required material; externalize changed state without repeating a full ledger; defer secondary issues without dropping them.
- Number ordered multi-step instructions by action; use lists rather than tables for action sequences.
- Distinguish completed from planned or unverified work. Report errors as cause -> effect -> correction.
- Use concrete, descriptive headings.
- Review effects, not authorship: remove semantic repetition and empty metadiscourse; avoid manufactured contrast. Drop an evaluative label that has no supporting fact or criterion. Avoid mechanical symmetry or fragmentation, unnecessary sectioning, epistemic opacity, and functionless lexical inflation; preserve legitimate voice, uncertainty, transitions, parallelism, and technical terms.
Prose and guided procedures use in-model G1 guidance. Do not list the runtime directory; do not probe a checker with --help; do not create a temporary candidate; do not run the advisory prose linter unless explicitly requested or hosts have final-candidate custody for a declared gate. For structured artifact call named checker directly once on actual candidate.
## 5. Reference activation map

Load one match; do not inspect neighbours.

- ordinary editable user-facing prose -> section 4 of this kernel; no reference read. Exclude raw data, code, quotations, identifiers, and paths.
- explicit ordinary-rule applicability or rule-audit question -> references/always-on.md
- raw JSON -> references/format-json.md
- JSONL -> references/format-jsonl.md
- YAML -> references/format-yaml.md
- Markdown with embedded literals -> references/format-markdown.md
- executable procedure -> references/procedures.md under the guided profile
- hazard or damage risk -> references/safety-instructions.md
- public README/landing, install/use, release, or product/architecture/reference docs -> references/public-documentation.md (technical-clarity)
- system description -> references/descriptions.md
- technical explanation, architecture, plan, audit, runbook, or state -> references/technical-clarity.md
- controlled-technical profile -> references/controlled-technical-writing.md
- explicit project-term mapping -> references/canonical-terms.md
- mixed prose and literals -> references/protected-regions.md
- conformance claim -> references/conformance.md
- secondary issue, multi-turn state, or effort estimate guidance -> references/action-shaping.md
- prose-integrity deep guidance -> references/prose-integrity.md
- contextual prose-quality review -> references/descriptive-prose.md
- precedence or region question -> references/activation-and-precedence.md
- meta-code artifact -> references/meta-code.md
- rule audit, conformance, or deep application -> references/rule-index.md + rules/registry.yaml

For one rule, use `runtime/query_rules.py <ID>`.

## 6. Final review checklist
Before delivery: top contract; G1 literal exclusions; available callable structured checks on actual candidate; nothing unsupported was added and nothing required was dropped; only predicate-matched references.
Do not read every reference or corpus module. When no predicate is true, answer from this kernel alone.
