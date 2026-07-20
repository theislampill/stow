# JSONL output contract (one value per line)

A JSONL output region is a stream of records where each non-empty line holds one
complete, independently parseable JSON value. This page is a scanned surface, not
rule text. It tells a reviewer *when* the contract applies, *which* region of the
output it governs, and *how* STOW checks it. The mechanics of the contract are a
STOW-native serialization invariant enforced by
`skills/stow/runtime/validate.py`, not a rule derived from any corpus, so no
`corpus_ref` citation applies to the contract itself. Where a governed rule meets
the JSONL boundary, the normative statement lives only in the cited `corpus_ref`
file. Read the corpus for the wording, never this page.

## The contract

The observable properties `validate.py` enforces for a JSONL region:

- **One JSON value per non-empty line.** Each line is parsed on its own as a
  single complete JSON value.
- **No wrapping array.** The records are the lines themselves, not the elements
  of one enclosing JSON array. A pretty-printed multi-line array fails because
  its fragment lines (`[`, `1,`, `}`) are not each a valid JSON value.
- **Every line parses independently.** A line is valid or invalid on its own; one
  bad line does not invalidate the others, and one good line does not rescue a bad
  neighbor.
- **Blank lines carry no record.** Whitespace-only lines are skipped, not treated
  as empty records.
- **Failures are reported by line number.** Each parse failure is emitted as
  `line N: <reason>`, so a reviewer can locate the offending record directly.
- **A single trailing newline terminates the file.** CRLF line endings are
  tolerated; an incidental final blank line is accepted.
- **No leading BOM** (U+FEFF) and **no wrapping Markdown code fence**: the region
  is raw JSONL, not a fenced block.
- **Each line is strict JSON.** No `//` or `/* */` comments, no trailing commas,
  no duplicate object keys, and no non-finite literals (`NaN`, `Infinity`,
  `-Infinity`).

## How STOW checks it

Run the packaged validator against the file:

```
python skills/stow/runtime/validate.py --format jsonl <file>
```

It prints `VALID (jsonl): <file>` and exits `0` when every non-empty line parses,
or `INVALID (jsonl): <file>` with one `line N: …` message per failure and a
nonzero exit otherwise. The validator reads the region but never mutates it. These
are engineering invariants of the serialization, so they stand on the code path
above rather than on a `corpus_ref`.

## Governed rules at the JSONL boundary

A JSONL region is a **structured-data** region. Every controlled-technical rule
and every presentation-layer rule lists `structured-data` under `scope.exclude`
in `skills/stow/rules/registry.yaml`, so none of them evaluate or rewrite inside
the region. The entries below give the observable trigger, the region, how STOW
checks it, and the `corpus_ref` for the full rule text.

### Keys and string values are protected literals

- **Trigger:** a JSON object key or a quoted string value contains a token a
  presentation-layer lexical scan would otherwise change: a non-American
  spelling, a banned verb, a word it would count for length.
- **Region:** every key and every quoted string, on every line of the payload.
- **How STOW checks it:** the region is masked as structured-data before any scan,
  so the lexical rules skip it and never rename a key or re-spell a value. On
  conflict the resolution is fixed: serialization validity and the protected
  literal outrank the presentation-layer lexical preference, which skips the
  protected span.
- **Full text:** see corpus/words/usage.md#STOW-WRD-014, corpus/prose-integrity/rules.md#STOW-PRO-021,
  and corpus/punctuation.md#STOW-PCT-006.

### JSON structural punctuation is not prose punctuation

- **Trigger:** the `:` `,` `{` `}` `[` `]` and the quoting that make each line
  valid JSON.
- **Region:** the JSON syntax on each line.
- **How STOW checks it:** the line is excluded as structured-data, so the
  punctuation and character-ban rules never read a JSON delimiter as a prose mark
  or flag it for rewriting.
- **Full text:** see corpus/punctuation.md#STOW-PCT-001 and
  corpus/prose-integrity/rules.md#STOW-PRO-001.

## Applying it

Validate the region first with the command above, then resolve any reported line
against the contract. Because the region is masked from every prose scan, a value
that reads like ordinary prose is never rewritten into something that no longer
parses, and a finding on the surrounding prose never edits a key or a string
inside the JSONL payload.

## Deliver once

Trigger: any raw-output request (no fence, no commentary). Region: the entire
reply. How STOW checks it: composition and any validation happen privately,
before sending; the reply contains the finished artifact and nothing else. If a
checker cannot run in the current session, STOW still ships only the artifact
and never writes a note about the missing check inside the artifact or beside
it. A correction replaces the draft before sending; it is never appended after
a first attempt in the same reply. The governing duty is the kernel's
raw-delivery rule: a raw artifact ships raw.
