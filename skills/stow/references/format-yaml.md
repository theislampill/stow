# YAML output contract

Application guidance for the YAML surface. This is a reference, not a rule
statement: it says *when* the contract applies, *which region* it covers, and
*how STOW checks* it, then points at the checker and the governing corpus
entries. It does not restate any rule's normative text.

STOW emits YAML only when the caller asks for YAML. That output is a
machine-readable, structured-data surface, not prose. Every record in the
registry excludes `structured-data` from its scope, so the controlled-technical
and presentation rules do **not** scan the keys, structure, or scalar tokens of
a YAML document. What governs the surface instead is a mechanical serialization
contract, enforced deterministically by the packaged checker
`runtime/validate.py` (`python runtime/validate.py --format yaml <file>`). Run
it on the exact bytes you are about to return and deliver only on exit 0.
Semantics are YAML 1.2 core (safe) schema.

## The contract

Each item below is an observable trigger, the region it covers, and how STOW
checks it. Unless noted, the checker is `runtime/validate.py`.

- **Parse before delivery.** Trigger: any YAML STOW is about to return. Region:
  the whole stream, every document in it. How checked: the checker composes the
  input with a safe loader pinned to version 1.2; any parser failure is an
  error and blocks delivery.

- **Spaces, never tabs, for indentation.** Trigger: nesting a mapping or
  sequence. Region: the leading whitespace of every line. How checked: a tab in
  indentation is not valid 1.2 indentation and surfaces as a parse error above.

- **Quote ambiguous scalars.** Trigger: a plain scalar that a reader easily
  misreads as a boolean (`yes`, `no`, `on`, `off`, `y`, `n`) or that would
  otherwise resolve unexpectedly. Region: scalar keys and values. How checked:
  the checker resolves such tokens to strings under 1.2 but reports each as an
  advisory warning; STOW quotes the intended string so the value cannot be
  misread. Warnings do not change exit status, so quote proactively rather than
  relying on the warning.

- **Reject duplicate keys by source token.** Trigger: the same key written twice
  in one mapping. Region: every mapping node. How checked: the checker walks the
  node graph and compares the raw source token of each scalar key (its written
  text plus resolved tag), never the resolved value. So `1:` and `1.0:` are
  distinct keys, `0x10:` and `16:` are distinct keys, and only the identical
  token appearing twice is a duplicate and an error.

- **Custom tags, anchors, and aliases are off unless requested.** Trigger: a
  `!tag` outside the 1.2 core set, an `&anchor`, an `*alias`, or the merge key
  `<<`. Region: any node. How checked: the checker rejects any non-core tag and
  any declared anchor or alias reuse as errors. Emit these constructs only when
  the caller explicitly asks for them.

- **No leading BOM; UTF-8 only.** Trigger: a byte-order mark or non-UTF-8 bytes.
  Region: the file head and the whole byte stream. How checked: the checker
  rejects a leading U+FEFF, and the command line rejects input that is not valid
  UTF-8.

## Where the prose rules stop

Trigger: STOW producing YAML while a controlled-technical profile is active.
Region: keys, identifiers, and quoted literals are protected and immutable;
scalar tokens generally are structured data, not prose. How checked: they are
not scanned or rewritten. Do not rename a key or identifier, and do not edit
quoted text, to satisfy a lexical or presentation preference. The precedence
that fixes this boundary (serialization validity and protected literals
outrank presentation-layer lexical preferences, which skip protected regions)
is carried on the governing records; see `corpus/words/usage.md#STOW-WRD-014`,
`corpus/punctuation.md#STOW-PCT-006`, and
`corpus/prose-integrity/rules.md#STOW-PRO-021` for the full statements.

## Deliver once

Trigger: any raw-output request (no fence, no commentary). Region: the entire
reply. How STOW checks it: composition and any validation happen privately,
before sending; the reply contains the finished artifact and nothing else. If a
checker cannot run in the current session, STOW still ships only the artifact
and never writes a note about the missing check inside the artifact or beside
it. A correction replaces the draft before sending; it is never appended after
a first attempt in the same reply. The governing duty is the kernel's
raw-delivery rule: a raw artifact ships raw.
