# Protected regions (mask first, scan second)

Protected regions are spans the generation guidance tells a writer not to edit
on its own: code, quotations, machine identifiers, and serialized data. The
shipped implementation is narrower. `runtime/lint_prose.py` blanks recognized
spans in an in-memory copy before its advisory scans and never edits the input.
This behavior is STOW-authored, so no `corpus_ref` citation applies.

The masking functions cover their documented fence, inline-code, block-quote,
URL, path, and identifier patterns. Spaces replace matched characters while line
and column geometry stays stable. Different advisory checks use the masking
layer suited to that check, so the implementation is a finite syntax recognizer,
not a semantic partition of arbitrary text.

The exclusion is declared per rule in `skills/stow/rules/registry.yaml` under
`scope.exclude` (every prose record excludes `code`, `structured-data`,
`quoted-text`, and `identifiers`). Serialized spans are additionally validated
for well-formedness by `skills/stow/runtime/validate.py`, which reads them but
never mutates them.

## Guidance and runtime behavior

1. **Bound.** Generation guidance uses visible delimiters and the declared
   output contract to identify protected material.
2. **Mask for advisory scans.** The linter blanks only the span patterns its
   code recognizes and scans the copy.
3. **Keep custody external.** A host that requires byte fidelity must compare
   the actual final candidate with the authoritative literals and block a
   mismatch.

A linter finding may still refer to the text around a blanked span. The linter
does not rewrite either the span or its surroundings.

## Region taxonomy

Each entry gives the observable trigger, the region the linter attempts to
mask, and the advisory effect. It is grouped by `scope.exclude` class.

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

## Claim boundary

The shipped linter masks a finite set of recognizable spans before advisory
scanning; because it is read-only, it performs no restoration step and proves no
general final-output byte preservation.

Byte-preserving generation remains G1 guidance unless a named host owns the
actual final candidate, compares it with authoritative bytes, blocks mismatch,
and rechecks after any permitted repair.
