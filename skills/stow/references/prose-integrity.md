# Prose-integrity checks (PRO)

The PRO group is a presentation-layer pass over model-authored prose. It removes
the surface tells of machine writing (typographic, lexical, structural, and
sourcing) after the controlled-technical rules have already shaped vocabulary and
sentence form. Every PRO record carries `precedence: presentation`, so each check
yields to the controlled-technical profile and to the safety rules wherever they
collide; PRO never rewrites content those higher layers own.

This page gives application guidance only: for each rule, the observable trigger,
the output region it inspects, how STOW checks it, and the `corpus_ref` that holds
the full normative text. Read the corpus file for the rule itself. Do not treat
the trigger lines below as the rule; they say only *when and where* to look.

Shared scan region (applies to the whole group unless an entry says otherwise):
model-authored prose only. Per each record's scope, code, quoted text, structured
data (tables, JSON, YAML), and identifiers are excluded and never flagged.

Enforcement kinds referenced below:

- deterministic: a fixed linter matches an exact character, token, or listed
  phrase; zero tolerance, no autofix.
- heuristic: a linter flags a likely pattern for confirmation; expect some false
  positives, so the flag is reviewed before it stands.
- semantic-review: no automatic validator; a review pass applies judgement
  against the corpus rule.

Many of the deterministic and heuristic linters match against the shared tables in
`corpus/prose-integrity/banned-lists.md` (banned verbs, adjectives, metaphorical
nouns, transitions and connectors, opening / transitional / concluding phrases,
inflated-symbolism phrases, heading anti-patterns, filler words and empty
intensifiers, and hedging / epistemic-modality markers). The lists are large and
versioned; each linter reads its terms from that file at check time. This page does
not inline them, name them, or restate them; consult `banned-lists.md` for the
current entries.

## Typographic tells

- **STOW-PRO-001 · Ban the em dash.** Trigger: an em-dash character (`—`, U+2014),
  or a double-hyphen standing in for one, inside a prose sentence. Region: all
  prose. Check: deterministic linter `no-em-dash`. Full text:
  `corpus/prose-integrity/stow-pro-001.md`. Cross-layer note: when this would fire
  alongside the semicolon check (STOW-PCT-001), neither character is kept; the
  active controlled-technical profile selects the substitute (see the `conflicts`
  note on this record in `skills/stow/rules/registry.yaml`).
- **STOW-PRO-010 · No scare quotes on ordinary words.** Trigger: quotation marks
  wrapping a single common word where the marks are not a real quotation, a
  term-being-defined, or a title. Region: all prose. Check: heuristic linter
  `no-scare-quotes`. Full text: `corpus/prose-integrity/stow-pro-010.md`.

## Banned-vocabulary linters

Each of these matches its trigger against the corresponding table in
`corpus/prose-integrity/banned-lists.md`; the linter reads that file rather than
carrying the words itself.

- **STOW-PRO-021 · No AI verbs.** Trigger: a verb drawn from the overused-verb
  table. Region: all prose. Check: deterministic linter `no-ai-verbs`, matched
  against the Overused Verbs table in `banned-lists.md`. Full text:
  `corpus/prose-integrity/stow-pro-021.md`.
- **STOW-PRO-014 · No synthetic enthusiasm.** Trigger: promotional adjectives,
  metaphorical nouns used for false gravitas, or listed inflated-symbolism phrases.
  Region: all prose. Check: deterministic linter `no-synthetic-enthusiasm`, matched
  against the Overused Adjectives, Metaphorical Nouns, and Inflated Symbolism tables
  in `banned-lists.md`. Full text: `corpus/prose-integrity/stow-pro-014.md`.
- **STOW-PRO-004 · No empty intensifiers.** Trigger: a degree word from the
  intensifier list attached to a claim it does not measurably strengthen. Region:
  all prose. Check: deterministic linter `no-intensifiers`, matched against the
  Filler Words and Empty Intensifiers table in `banned-lists.md`. Full text:
  `corpus/prose-integrity/stow-pro-004.md`.
- **STOW-PRO-011 · No filler phrases.** Trigger: a multi-word filler or opener from
  the listed phrases. Region: all prose. Check: deterministic linter
  `no-filler-phrases`, matched against the Phrases That Signal AI Writing section of
  `banned-lists.md`. Full text: `corpus/prose-integrity/stow-pro-011.md`.
- **STOW-PRO-020 · No AI transition phrases.** Trigger: a connector or transition
  from the list at a clause or sentence boundary. Region: all prose. Check:
  deterministic linter `no-ai-transitions`, matched against the Overused Transitions
  and Connectors and Transitional Phrases tables in `banned-lists.md`. Full text:
  `corpus/prose-integrity/stow-pro-020.md`.
- **STOW-PRO-015 · No weasel words.** Trigger: an unattributed hedge or vague
  quantifier standing in for a specific figure or source. Region: all prose. Check:
  deterministic linter `no-weasel-words`, matched against the Hedging and Epistemic
  Modality markers in `banned-lists.md`. Full text:
  `corpus/prose-integrity/stow-pro-015.md`.
- **STOW-PRO-022 · No academic AI tells.** Trigger: stacked hedging or academic
  boilerplate layered over declarative content, above the per-paragraph and
  per-1000-word thresholds. Region: all prose, especially declarative sections
  (Background, History, Timeline). Check: deterministic linter `no-academic-tells`,
  matched against the Hedging thresholds and AI Hedging Phrases in `banned-lists.md`.
  Full text: `corpus/prose-integrity/stow-pro-022.md`.
- **STOW-PRO-012 · Ban the whether-you-are opener.** Trigger: an opener of the
  "Whether you are X, Y, or Z" shape (three trailing examples after `whether`).
  Region: sentence and paragraph openings. Check: deterministic linter
  `no-whether-youre-opener`, matched against the Structural Patterns list in
  `banned-lists.md`. Full text: `corpus/prose-integrity/stow-pro-012.md`.

## Headings

Both rules activate only when the response contains section headings.

- **STOW-PRO-003 · No parentheticals in headings.** Trigger: a parenthetical clause
  inside a heading line. Region: section headings. Check: heuristic linter
  `no-heading-parentheticals`. Full text: `corpus/prose-integrity/stow-pro-003.md`.
- **STOW-PRO-016 · Concrete, descriptive headings.** Trigger: a heading matching a
  dramatic or clickbait shape rather than describing the section content. Region:
  section headings. Check: heuristic linter `concrete-headings`, matched against the
  Heading Anti-Patterns table and self-check in `banned-lists.md`. Full text:
  `corpus/prose-integrity/stow-pro-016.md`.

## Structure and non-repetition

- **STOW-PRO-006 · No repeated points.** Trigger: the same claim restated across
  sentences or sections without adding new content. Region: all prose. Check:
  semantic-review. Full text: `corpus/prose-integrity/stow-pro-006.md`.
- **STOW-PRO-007 · Vary structure.** Trigger: consecutive paragraphs or sections
  built on the same repeated template. Region: across sections. Check: heuristic
  linter `vary-section-structure`. Full text:
  `corpus/prose-integrity/stow-pro-007.md`.
- **STOW-PRO-005 · End claims on a concrete detail.** Trigger: a paragraph or
  section closing on an abstract restatement rather than a specific fact. Region:
  the closing sentence of a claim. Check: semantic-review. Full text:
  `corpus/prose-integrity/stow-pro-005.md`.

## Sourcing and fabrication

These are judgement checks: the reviewer verifies each claim against a real,
traceable source rather than pattern-matching text.

- **STOW-PRO-002 · Require attributable numbers.** Trigger: a statistic or quantity
  with no source the reader can trace. Region: all prose. Check: semantic-review.
  Full text: `corpus/prose-integrity/stow-pro-002.md`.
- **STOW-PRO-023 · Quote sources accurately.** Trigger: quoted material from an
  external source. Region: the quoted text and its attribution. Check:
  semantic-review against the cited source. Activates only when the response quotes
  an external source. Full text: `corpus/prose-integrity/stow-pro-023.md`.
- **STOW-PRO-019 · No fabricated attributions.** Trigger: a quote, opinion, or
  position credited to a named person or organization. Region: all prose. Check:
  semantic-review. Full text: `corpus/prose-integrity/stow-pro-019.md`.
- **STOW-PRO-018 · No fabricated history.** Trigger: dates, sequences, or origin
  accounts presented as historical fact. Region: all prose, especially Background
  and Timeline sections. Check: semantic-review. Full text:
  `corpus/prose-integrity/stow-pro-018.md`.
- **STOW-PRO-017 · No fabricated scenarios.** Trigger: an invented example or
  anecdote presented as a real event. Region: all prose. Check: semantic-review.
  Full text: `corpus/prose-integrity/stow-pro-017.md`.

## Voice and meta-narration

- **STOW-PRO-013 · Write like a researcher.** Trigger: prose whose stance or voice
  departs from grounded, evidence-first exposition. Region: all prose. Check:
  semantic-review. Full text: `corpus/prose-integrity/stow-pro-013.md`.
- **STOW-PRO-008 · Reference without narrating.** Trigger: text that narrates the
  act of consulting or citing a source instead of stating the sourced fact. Region:
  all prose. Check: deterministic linter `no-reference-narration`. Full text:
  `corpus/prose-integrity/stow-pro-008.md`.
- **STOW-PRO-024 · No research-process narration.** Trigger: sentences describing
  the author's own searching, reading, or deliberation. Region: all prose. Check:
  semantic-review. Full text: `corpus/prose-integrity/stow-pro-024.md`.
- **STOW-PRO-009 · No urgency without a reason.** Trigger: urgency or pressure
  language with no stated cause. Region: all prose. Check: semantic-review. Full
  text: `corpus/prose-integrity/stow-pro-009.md`.
