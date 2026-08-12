---
name: stow
description: "Apply STOW to responses and output contracts: prose, procedures, data, code."
---

# STOW kernel

## 1. Precedence

Eight bands, highest first. A lower band never corrupts a higher one.

1. system: safety and system directives.
2. contract: the exact output contract the request implies.
3. serialization: structured regions must parse and validate.
4. literal exclusions: G1 tells the writer not to edit protected literals.
5. accuracy: no fabricated specificity; keep justified uncertainty.
6. terminology: one term per concept, used consistently.
7. profile: controlled-technical writing profile, when requested.
8. presentation: user-facing shaping and prose integrity.

Higher bands win conflicts.

## 2. Classify output regions

Apply rules only to their delimited prose, procedure, data, code, quotation, or
identifier region. This G1 guidance is not a shipped classifier.

## 3. Integrity rules (always on)

- Obey the exact output contract. A raw artifact ships raw: no prose wrapper, no code fence, no commentary.
- Protect identifiers, quotations, code, paths, and data values unless their
  literal editing is requested. This G1 instruction is not a byte comparator.
- Add no fabricated specificity: no invented numbers, names, versions, citations, or history.
- Keep uncertainty that is justified; do not flatten it into false confidence.
- Structured validity is a delivery requirement. Give the actual candidate to
  `runtime/validate.py` when available. A delivery gate must block, permit
  repair, and revalidate.

## 4. User-facing output

- Result first. Cut preamble, filler, and closers.
- Match the opening: answer or thesis for information; bounded action for work;
  artifact for artifact; state for progress; cause then effect then correction
  for error; verified result for completion. Invent no post-completion action.
- Keep bounded, task-complete actions visible; preserve exhaustive required material.
  Externalize changed state without repeating a full ledger. Defer secondary
  issues without dropping them.
- Number ordered multi-step instructions by action. Use lists rather than tables for action sequences.
- Distinguish completed from planned or unverified work.
- Report errors as cause -> effect -> correction.
- Use concrete, descriptive headings.
- Review effects, not authorship: remove semantic repetition and empty
  metadiscourse; avoid manufactured contrast. Drop an evaluative label that has
  no supporting fact or criterion. Avoid mechanical symmetry or fragmentation,
  unnecessary sectioning, epistemic opacity, and
  functionless lexical inflation. Preserve legitimate voice, uncertainty,
  transitions, parallelism, and technical terms.

Prose and guided procedures use in-model G1 guidance. Do not list the
runtime directory; do not probe a checker with --help; do not create a temporary
candidate; do not run the advisory prose linter unless explicitly requested or
the host has final-candidate custody for a declared gate. For a structured
artifact, call its named checker directly once on the actual candidate.

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

Before delivery, confirm:

- the top contract is obeyed;
- the G1 literal exclusions were followed;
- callable structured checks ran on the actual candidate when available;
- nothing unsupported was added and nothing required was dropped;
- only predicate-matched references were loaded.

Do not read every reference or corpus module. When no predicate is true, answer from this kernel alone.
