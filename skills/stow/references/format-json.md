# JSON output contract

STOW-native format guidance plus a closed JSON detector. It describes how a JSON deliverable should be emitted and
has no controlled-technical-rules provenance, so it cites no corpus record. The
single source of truth for every clause below is the runtime validator
`skills/stow/runtime/validate.py` (function `validate_json`). This reference
gives application guidance only: when the contract applies, which output region
it covers, and how STOW checks it. The runtime is authoritative only for its G2
parse verdict; delivery custody remains with the caller or host.

**When it applies (trigger).** The turn asks for a JSON deliverable, or a
downstream consumer parses the output as JSON. This is raw-JSON mode: the value
is delivered on its own, with no explanation and no wrapper.

**Output region.** The whole delivered payload is exactly one JSON value. In
raw-JSON mode that region is the entire response body; when JSON is written to a
file or artifact, it is the entire file. Nothing may share the region: no prose
before or after the value, and no Markdown fence around it.

**How STOW checks it.** Write the candidate to a file and run the validator:

```
python skills/stow/runtime/validate.py --format json <file>
```

Exit status 0 with `VALID (json)` passes. Any nonzero exit with `INVALID (json)`
fails and names the clause that broke. Do this before delivery, every time. See
`skills/stow/runtime/validate.py` for the exact behavior.

## Contract clauses

Each clause is an observable property of the supplied payload. The validator
checks all of them in a single strict parse.

| Clause | Observable trigger of a failure | How STOW checks it |
| --- | --- | --- |
| Single value | A second top-level value, or any trailing text after the value | The full text is parsed as exactly one JSON value |
| No fence | The payload opens with a Markdown code fence (three backticks) | A leading fence is rejected before parsing |
| No BOM | A leading U+FEFF byte-order mark | A leading BOM is rejected |
| No non-finite | The tokens `NaN`, `Infinity`, or `-Infinity`, or a numeric literal that overflows to a non-finite float | Non-finite constants and overflowing floats are rejected by the parse hooks |
| No comments | A `//` line comment or a `/* */` block comment | Comments are rejected by the strict parse |
| No trailing commas | A comma before a closing `]` or `}` | Trailing commas are rejected by the strict parse |
| Unique keys | The same key appearing twice in one object | Duplicate keys are rejected instead of silently taking last-wins |

## Two checks the validator does not replace

- **Parse the actual candidate.** A G3 host gives the final bytes to the parser,
  blocks a nonzero result, and reruns the parser after any permitted repair.
- **Schema conformance.** When the task supplies a JSON Schema, validate the
  value against that schema after the structural check. Format mode checks
  structural strictness only; use schema mode for a shipped schema or a separate
  checker for a caller-supplied schema.

## Deliver once

Trigger: any raw-output request (no fence, no commentary). Region: the entire
reply. The guidance says composition and checking happen before sending, so the
reply contains the finished artifact and nothing else. If a checker cannot run
in the current session, the response still contains only the artifact
and never writes a note about the missing check inside the artifact or beside
it. A correction replaces the draft before sending; it is never appended after
a first attempt in the same reply. The governing duty is the kernel's
raw-delivery rule: a raw artifact ships raw.
