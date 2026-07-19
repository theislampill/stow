# Protected regions (mask first, scan second)

Protected regions are spans of a response that STOW must read but must never
rewrite: code, quotations, machine identifiers, and serialized data. Before any
prose rule or lexical scan runs, STOW replaces each protected span with an
opaque placeholder, applies every rule to the masked surface, then restores the
original spans byte-for-byte. This ordering is a STOW-native invariant, not a
rule derived from any corpus, so no `corpus_ref` citation applies.

This is why the controlled-technical rules (the word, sentence, procedure,
description, punctuation, and style families) and the presentation-layer lexical
scans (the prose-integrity and action-shaping families) never corrupt a code
block, a quoted line, a schema key, a file path, or a URL: by the time a scanner
sees the text, those spans are no longer text it can edit. A masked span is a
single opaque token to every scanner. It is not rewritten, not searched for
banned words or characters, and not split on word or sentence boundaries.

The exclusion is declared per rule in `skills/stow/rules/registry.yaml` under
`scope.exclude` (every prose record excludes `code`, `structured-data`,
`quoted-text`, and `identifiers`). Serialized spans are additionally validated
for well-formedness by `skills/stow/runtime/validate.py`, which reads them but
never mutates them.

## The invariant

1. **Mask.** Detect every protected span and swap it for a placeholder token.
2. **Scan.** Run the controlled-technical rules and the lexical scans over the
   masked surface only. Placeholders are inert: they match no banned pattern and
   carry no editable prose.
3. **Restore.** Put every original span back exactly as written. No protected
   span is ever paraphrased, re-spelled, re-cased, or re-punctuated.

A rule may still act on the region *around* a placeholder (spacing, a following
period, sentence length), but never on the masked content itself.

## Region taxonomy

Each entry gives the observable trigger, the region that gets masked, and how
STOW detects and protects it. Grouped by the `scope.exclude` class it maps to.

### Code (`scope.exclude: code`)

- **Fenced code blocks.** Trigger: a line opening with a triple-backtick or
  triple-tilde fence, through the matching closing fence at the same indent.
  Region: the fence lines and everything between them. How checked: the fence
  pair is located first and the whole block is masked as one unit before any
  prose scan, so spelling, word-choice, and banned-character rules never reach
  source code.
- **Inline code.** Trigger: a backtick-delimited span inside prose. Region: the
  span including its backticks. How checked: inline spans are masked in place;
  the controlled-technical rules treat the placeholder as one opaque token
  rather than as words to approve or re-spell.

### Serialized data (`scope.exclude: structured-data`)

- **Schema keys.** Trigger: an object key or field name in serialized data (for
  example a mapping key in YAML or JSON). Region: the key token. How checked:
  keys are masked so no prose rule renames or re-cases them; well-formedness of
  the surrounding document is checked by `validate.py`, which never edits the
  key.
- **Serialized-data spans.** Trigger: a recognizable JSON, JSONL, or YAML
  fragment (structural punctuation, quoting, and indentation). Region: the whole
  serialized span. How checked: the span is masked from prose scanning and
  validated for structure separately, so a value that reads like ordinary prose
  is never rewritten into something that no longer parses.

### Quotations (`scope.exclude: quoted-text`)

- **Block quotations.** Trigger: a line prefixed with a block-quote marker, and
  its continuation lines. Region: the quoted lines. How checked: quoted content
  is masked so it is reproduced verbatim; the controlled-technical rules never
  edit borrowed wording, and the quote-accuracy expectations of the
  prose-integrity family are preserved because the source text is untouched.

### Identifiers (`scope.exclude: identifiers`)

- **File paths.** Trigger: a slash- or backslash-delimited path, with or without
  an extension. Region: the full path token. How checked: masked as one opaque
  identifier so no word or spelling rule alters a directory or file name.
- **Identifiers.** Trigger: an alphanumeric symbol, a dotted or snake/camel name,
  or a code-like token. Region: the identifier token. How checked: masked before
  scanning so it is never split, re-cased, or treated as approvable vocabulary.
- **URLs.** Trigger: a `scheme://host/...` reference or a bare host with a path.
  Region: the whole URL. How checked: masked as one token so no punctuation,
  spelling, or word-choice rule mutates a link, and word-length scanners see a
  single unit.

## Why this holds

Because masking runs first and unconditionally, correctness of the protected
content does not depend on any individual rule being careful. Even a rule that
would otherwise rewrite a sentence operates only on the masked surface, and the
restore step guarantees the original code, quotation, key, path, or URL comes
back exactly as the author wrote it.
