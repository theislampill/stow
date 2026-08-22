---
name: stow
description: "Use STOW for README/runbook/procedure/plan/audit/handoff, public/controlled text, mixed text/literals, or JSON/JSONL/YAML/Markdown. Applies exact output contracts; guards literals"
license: LICENSE
compatibility: "Agent Skills-compatible hosts; CPython 3.11; validate.py: ruamel.yaml>=0.19.1/jsonschema>=4.26.0; others: stdlib. Installation alone runs no helper."
metadata: {author: theislampill, version: "0.4.2"}
---

# STOW kernel

## 1. Precedence

Eight bands, highest first: system: safety/system directives; contract: exact implied output contract; serialization: structured regions must parse and validate; literal exclusions: G1 bars protected-literal edits; accuracy: no fabricated specificity, retain justified uncertainty; terminology: one term per concept, used consistently; profile: requested controlled-technical writing; presentation: user-facing shaping and prose integrity.

A lower band never corrupts a higher one. Higher bands win conflicts.

## 2. Classify output regions

Apply rules only to delimited prose, procedure, data, code, quotation, or identifier regions. G1 guidance is not a shipped classifier.

## 3. Integrity rules (always on)

- Obey the exact output contract. A raw artifact ships raw: no prose wrapper, no code fence, no commentary.
- Protect identifiers, quotations, code, paths, and data values unless asked to edit the literal; G1 is not a byte comparator.
- Add no fabricated specificity: numbers, names, versions, citations, or history; preserve justified uncertainty, not false confidence.
- Delivery requires structured validity: give the actual candidate to `runtime/validate.py` when available; the gate must block, permit repair, and revalidate.

## 4. User-facing output

- Result first. Cut preamble, filler, and closers.
- Open with information: answer/thesis; work: bounded action; artifact: artifact; progress: state; error: cause -> effect -> correction; completion: verified result. Invent no post-completion action.
- Keep bounded, task-complete actions visible; preserve exhaustive required material. Externalize changed state without repeating a full ledger; defer secondary issues without dropping them.
- Number ordered multi-step instructions by action. Use lists rather than tables for action sequences.
- Distinguish completed, planned, and unverified work; errors use cause -> effect -> correction.
- Use concrete, descriptive headings.
- Review effects, not authorship: remove semantic repetition and empty metadiscourse; avoid manufactured contrast. Drop an evaluative label that has no supporting fact or criterion. Avoid mechanical symmetry or fragmentation, unnecessary sectioning, epistemic opacity, and functionless lexical inflation; preserve legitimate voice, uncertainty, transitions, parallelism, and technical terms.

Prose and guided procedures use in-model G1. Do not list the runtime directory; do not probe a checker with --help; do not create a temporary candidate; do not run the advisory prose linter unless explicitly requested or the host has final-candidate custody for a declared gate. For a structured artifact, call its named checker directly once on the actual candidate.

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

Before delivery confirm: top contract; G1 literal exclusions; callable structured checks ran on the actual candidate when available; nothing unsupported was added and nothing required was dropped; only predicate-matched references.

Do not read every reference or corpus module. When no predicate is true, answer from this kernel alone.
