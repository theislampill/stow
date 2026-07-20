# Mixed-Markdown format reference (embedded literals and data)

Application guidance for Markdown output that carries embedded literals or
structured data. This page is a scanned surface, not rule text. It tells a
reviewer *where* each region boundary falls in a Markdown document, *which*
rules may touch each region, and *how* STOW checks the result. The normative
statement of every rule named here lives only in its cited `corpus_ref` file.
Read the corpus for the wording, never this page.

The contract in one line: apply prose rules only to editable prose, keep every
code fence, inline-code span, quotation, path, identifier, schema key, and
serialized region byte-stable, and validate each embedded structured-data region
on its own.

## When this page applies

- **Predicate:** the response is Markdown that contains at least one embedded
  literal or structured-data region: a fenced code block, an inline-code span,
  a block quote, YAML front matter, a data fence, a table cell holding a literal,
  or a bare path, identifier, version, or key inside prose.
- Load it together with `references/protected-regions.md`, which defines how STOW
  recognizes a protected literal. This page adds the Markdown-specific boundaries;
  that page defines the literal itself.

## The region model

A Markdown document is not one surface. It interleaves editable prose with
protected literals and structured regions, and the boundaries follow the
delimiters already in the text: fences, backticks, quotation marks, list layout,
front-matter rules, and table pipes. Split the document at those delimiters, then
apply each rule only to the region its scope names, exactly as the kernel
requires (`SKILL.md` section 2).

Two invariants hold across every construct below:

- A prose rule never edits code, structured data, quoted text, or an identifier.
  These regions carry the shared scope `exclude` of every prose rule.
- Each embedded structured-data region parses and schema-checks independently.
  A valid prose region never excuses an invalid data region, and the reverse.
  Serialization (band 3) and literals (band 4) outrank the profile and
  presentation bands, so a lexical or shaping preference yields on any conflict.

## Fenced code blocks and inline code

- **Trigger:** a fenced block opened by ``` or `~~~`, or an inline span between
  single backticks.
- **Region:** protected literal. The body is byte-stable, including its spelling,
  spacing, and punctuation.
- **How STOW checks it:** no prose rule enters the fence or the span. The literals
  band holds the bytes fixed; the presentation and profile lexical checks skip the
  region entirely. This is the immutability behavior the registry records on the
  protected-literal conflicts: see corpus/punctuation/stow-pct-006.md and
  corpus/words/stow-wrd-014.md.
- When a fence's info string names a data language, also treat its body as a
  structured region (below).

## Embedded structured-data regions

- **Trigger:** YAML front matter delimited by `---` rules at the top of the
  document, and any fenced block whose info string is a data format (for example
  `json`, `yaml`, or `jsonl`).
- **Region:** one independent serialization region per block.
- **How STOW checks it:** validate each region against its own format reference
  (`references/format-json.md`, `references/format-yaml.md`, or
  `references/format-jsonl.md`) and through `runtime/validate.py` before delivery.
  No prose rule renames a key, reorders a mapping, or edits a value. A failure in
  one region is isolated to that region.

## Block quotes and inline quotations

- **Trigger:** a `>` block quote, or quotation marks around attributed text in
  prose.
- **Region:** quoted text. Excluded from the lexical prose rules.
- **How STOW checks it:** the quoted span stays byte-exact, so its spelling is not
  changed to match the prose spelling convention (see corpus/words/stow-wrd-014.md),
  and each quotation counts as a single token for length (see
  corpus/punctuation/stow-pct-006.md). Fidelity to the source and the block layout
  for a long quotation are reviewed by the quotation check at
  corpus/prose-integrity/stow-pro-023.md.

## Paths, identifiers, schema keys, and bare literals

- **Trigger:** a file path, code identifier, schema key, version string, or
  alphanumeric identifier appearing in prose, whether or not it sits in backticks.
- **Region:** identifier. Protected.
- **How STOW checks it:** the token passes through unchanged and is not renamed,
  re-cased, or reworded, and it counts as one word (see
  corpus/punctuation/stow-pct-006.md). Recognition of a bare, un-fenced literal is
  the job of `references/protected-regions.md`; this page only confirms that once
  recognized, the token is out of scope for every prose rule.

## Headings

- **Trigger:** an ATX (`#`) or setext heading line.
- **Region:** the heading text is editable prose, but two presentation checks
  target headings specifically, and any literal inside the heading stays protected.
- **How STOW checks it:** STOW inspects each heading against the parenthetical
  constraint at corpus/prose-integrity/stow-pro-003.md and the concreteness
  constraint at corpus/prose-integrity/stow-pro-016.md. Both are flagged for the
  author, not auto-fixed.

## Lists and tables

- **Trigger:** a bulleted or numbered list, or a pipe (`|`) table.
- **Region:** list-item and cell prose is editable prose; a cell that holds a
  literal stays protected.
- **How STOW checks it:** a multi-step action sequence is rendered as a numbered
  list rather than a table (see corpus/action-shaping/stow-act-002.md and
  corpus/action-shaping/stow-act-011.md), and complex conditional text is broken
  into a vertical list (see corpus/sentences/stow-sen-003.md). The prose inside
  each item is checked as editable prose against the active profile and
  presentation rules.

## Validation gate

Before delivery, confirm each of these for the Markdown document:

- prose edits are confined to editable-prose regions;
- every fence, inline-code span, quotation, path, identifier, and schema key is
  byte-identical to its intended value;
- every embedded structured-data region parses and schema-checks on its own
  through `runtime/validate.py`;
- the top output contract is obeyed: a raw artifact ships raw, with no added
  prose wrapper or fence.

For how STOW recognizes and bounds a protected literal, defer to
`references/protected-regions.md`. For the band ordering that decides any
cross-region conflict, see `references/activation-and-precedence.md`.
