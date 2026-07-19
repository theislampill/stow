# Cross-harness interchange

A **cross-harness interchange envelope** lets an artifact produced under one
harness be consumed under another — a different agent runtime, a CI bot, a human
tool — without loss. It is a self-describing wrapper: what kind of artifact it
carries, which schema and version validate it, its content type, an integrity
hash, and the payload inline or by reference. This page also governs the
**machine-readable event stream** — the append-only, line-oriented log of what
happened during a run — because the stream is the interchange format for runtime
history and reuses the existing JSONL contract.

This page is a scanned surface, not rule text. For the wording of any governed
prose rule named below, open its cited `corpus_ref` module.

## When this page applies

- **Predicate:** an artifact must cross a harness boundary and be validated by a
  receiver with no shared memory, or a run emits an event log that a monitor,
  replayer, or auditor consumes.

## Governing STOW families

- **Serialization (band 3).** The envelope and the event stream are structured
  data that must parse and validate; the event stream reuses the JSONL contract
  in `references/format-jsonl.md` (`validate.py --format jsonl`), where each
  non-empty line is one independently parseable object.
- **Contract (band 2).** The envelope declares the payload's contract, so a
  receiver knows which schema to run without asking.
- **Literals (band 4).** The integrity hash and the payload bytes are protected
  literals — see corpus/words/stow-wrd-014.md and corpus/punctuation/stow-pct-006.md.
- **Terminology and versioning (band 6).** The schema id and version name a
  shipped contract exactly.

## Governing schema + template

- **Schema.** `schemas/output-contract.schema.json`. Required fields include
  `stow_version`, `artifact_type` (from the meta-code catalog), `content_type`,
  `schema_id`, `schema_version`, a `region_map[]`, an `integrity`
  (`{algo: "sha256", value}`), and exactly one of `payload` or `payload_ref`.
- **Template.** `templates/event-stream.jsonl` — a valid JSONL instance of one
  phase: each line an event `{ts, actor, type, ...}` with a monotonic timestamp
  and a `type` from a closed vocabulary.

## Validation contract

Validate the envelope against its schema, and an event stream line by line first:

```
python skills/stow/runtime/validate.py --schema output-contract <envelope>
python skills/stow/runtime/validate.py --format jsonl <event-stream>
```

The load-bearing rules: `sha256(payload_bytes) == integrity.value`; `artifact_type`
is in the catalog; `schema_id` resolves to a shipped schema, and if non-null the
payload validates against it; for an event stream, every line parses, there is no
wrapping array, timestamps are monotonic non-decreasing, and each `type` is in the
closed vocabulary. Line failures are reported as `line N: <reason>`. **Cold-reader
gate:** a receiver on another harness can validate the payload against the named
schema with no out-of-band knowledge — the interoperability acceptance test.
