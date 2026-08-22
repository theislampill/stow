---
name: stow
description: >-
  Standardising Technical Output Writing (STOW) applies exact output contracts,
  preserves code, commands, paths, identifiers, quotations, and data values,
  and reviews editable prose for focus, technical clarity, terminology,
  evidence strength, and recurrent synthetic-writing pathologies. Use when the
  user explicitly invokes STOW or asks to write, rewrite, review, or validate a
  README, runbook, procedure, plan, audit, handoff, public technical document,
  controlled-technical text, mixed prose with protected literals, or an exact
  JSON, JSONL, YAML, or Markdown artefact.
license: LICENSE
compatibility: >-
  Agent Skills-compatible hosts. Packaged helpers are qualified on CPython
  3.11. validate.py requires ruamel.yaml>=0.19.1 and
  jsonschema>=4.26.0; the other packaged helpers use the Python standard
  library. Installation alone runs no helper.
metadata:
  author: "theislampill"
  version: "0.4.2"
---

# STOW kernel

## 1. Precedence

Highest first: system; exact output contract; serialization; literal
exclusions; accuracy; terminology; profile; presentation.

## 2. Classify regions

Apply rules only to the delimited prose, procedure, data, code, quotation, or
identifier region. G1 guidance is not a shipped classifier.

## 3. Integrity rules

- Obey the exact output contract. A raw artefact has no wrapper or commentary.
- Protect identifiers, quotations, code, commands, paths, and data values unless
  editing that literal is the task; G1 is not a byte comparator.
- Add no invented numbers, names, versions, citations, or history. Preserve
  justified uncertainty.
- Structured validity is a delivery requirement. Validate the actual candidate;
  a gate must block, permit repair, and revalidate.

## 4. User-facing output

- Result first. Match the opening to answer, action, artefact, state, error, or
  verified completion; invent no post-completion action.
- Keep bounded, task-complete actions visible; preserve exhaustive required material.
  Externalize changed state without repeating a full ledger. Defer secondary
  issues without dropping them.
- Number ordered multi-step instructions by action. Use lists rather than tables for action sequences.
- Distinguish completed, planned, and unverified work. Report errors as cause -> effect -> correction.
- Use concrete headings. Remove semantic repetition and empty metadiscourse;
  avoid manufactured contrast. Drop an evaluative label that has no supporting
  fact or criterion. Avoid mechanical symmetry or fragmentation, unnecessary
  sectioning, epistemic opacity, and lexical
  inflation. Preserve legitimate voice, uncertainty, transitions, parallelism,
  and technical terms.

Prose and guided procedures use G1 guidance. Do not list the runtime directory;
do not probe a checker with --help; do not create a temporary candidate; do not
run the advisory prose linter unless explicitly requested or the host has
final-candidate custody for a declared gate. For structured artefacts, run the
named checker once on the actual candidate.

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

## 6. Final review

Confirm the top contract and literal exclusions; run any callable check on the
actual candidate; add nothing unsupported, ensure nothing required was dropped, and load only
predicate-matched references.

Do not read every reference or corpus module. When no predicate is true, answer from this kernel alone.

## 7. Complete example

Input: `Rewrite this runbook step. Preserve ERR-17 and /srv/api/config.json.`

Output: `If ERR-17 occurs, restore /srv/api/config.json, then restart the API.`
