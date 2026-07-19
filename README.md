# STOW

STOW is a writing-discipline skill that governs every user-facing response a model produces. It treats a reply as a set of typed regions, prose, procedures, structured data, code, quotes, and identifiers, and applies a fixed set of rules so that each region stays correct for what it is. The goal is output that obeys the contract the request implies, keeps every literal byte-for-byte exact, validates every structured region, and reads as clear, consistent, and free of fabricated detail.

STOW is self-contained. It ships as a single skill with its own rule registry, its own runtime validators, and its own reference and corpus material. Nothing in the packaged skill points outward at the material the rules were originally distilled from.

## What STOW does

- Obeys the exact output contract. A raw artifact ships raw, with no prose wrapper, no fence, and no commentary.
- Protects literals. Identifiers, quotes, code, paths, and data values pass through unchanged.
- Adds no fabricated specificity. No invented numbers, names, versions, citations, or history, while justified uncertainty is preserved rather than flattened into false confidence.
- Keeps terminology stable. One term per concept, reused consistently across a response.
- Offers an optional controlled-technical writing profile for procedures and descriptions, activated only when a request calls for it.
- Shapes user-facing prose. Result first, progressive disclosure, concrete headings, and errors reported as cause, effect, and correction.

## Three-tier architecture

STOW is organized as three tiers, loaded from most general to most specific. A response is answered from the kernel alone unless a predicate calls for more.

### Kernel

The kernel is the always-on core (`skills/stow/SKILL.md`). It defines the precedence order, tells the model how to split a response into regions, states the integrity rules that are always active, sets the shape of user-facing output, and lists the predicates that decide when to load anything deeper. When no predicate is true, the kernel is the entire ruleset in play.

### References

References are mid-tier guidance modules under `skills/stow/references/`, each loaded only when its activation predicate is true. Examples: a raw-JSON contract loads the JSON format reference, an executable procedure loads the procedures reference, a hazard or damage risk loads the safety reference, and a request for the controlled-technical profile loads that reference. A reference expands a topic the kernel names but does not itself carry the full guidance for.

### Corpus

The corpus under `skills/stow/corpus/` holds one module per rule, grouped by category (words, sentences, procedures, descriptions, safety, punctuation, style, verbs, prose integrity, action shaping, and more). Each module carries the detailed statement, rationale, and examples for a single rule. Corpus modules are loaded last, only when a rule audit or a deep application cites a specific rule.

## Precedence

The kernel resolves conflicts through 8 precedence bands, highest to lowest: system directives, output contract, serialization, protected literals, accuracy, terminology, the optional writing profile, and user-facing presentation. The invariant is that a lower band never corrupts a higher one. Presentation never edits a literal, terminology never breaks serialization, and the writing profile never softens a safety instruction. When two bands conflict, the higher band wins and the lower yields.

## The rule registry

Every rule lives in a single registry at `skills/stow/rules/registry.yaml`, which indexes 96 rules. Each record carries a stable id, a title, a category, a precedence band, a scope that names which regions it applies to, an activation predicate, and a pointer to its corpus module. The registry is the one source of truth: the human-readable rule index and the per-rule corpus modules are all keyed to it, so a rule can be traced from its id to its full text and back.

## How it is used

1. The skill is active for every user-facing response, across casual replies, explanations, plans, procedures, technical documentation, Markdown, YAML, JSON, JSONL, code-adjacent text, and mixed-format output.
2. The model reads the kernel, splits the response into regions, and applies the always-on integrity rules.
3. If a predicate in the kernel's activation map is true, the matching reference is loaded; a rule audit or deep application additionally pulls the cited corpus module.
4. Structured regions are checked with `skills/stow/runtime/validate.py` before delivery. A region that fails to parse or schema-check is repaired and revalidated rather than shipped.
5. A final gate confirms the top contract is obeyed, literals are unchanged, every structured region validates, nothing unsupported was added and nothing required was dropped, and only predicate-matched references were loaded.

## Repository layout

```
skills/stow/
  SKILL.md              kernel: precedence, region model, integrity rules
  references/           mid-tier guidance, loaded by predicate
  corpus/               one module per rule, grouped by category
  rules/registry.yaml   the rule registry (96 rules) and its schema
  runtime/              validators and prose lint used before delivery
docs/                   design notes and evaluation results
tools/                  build and check tooling
```

## Installation

STOW is packaged as a plugin. The manifest is `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json` describes a single-plugin marketplace whose source is this repository root.
