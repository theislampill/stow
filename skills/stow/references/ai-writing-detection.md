# Banned-list lookup for the self-check pass

The corpus self-check pass (`corpus/prose-integrity/self-check-pass.md`) sends
readers here for the full banned lists. This page is a pointer, not a copy:
the lists have exactly one home and are never duplicated into a reference.

Where the lists live and how to check against them:

- **Normative source.** The complete banned term, phrase, and construction
  lists are the corpus module `corpus/prose-integrity/banned-lists.md`. That
  file is the single authority; read it directly when reviewing by hand.
- **Deterministic checking.** The packaged linter parses those same lists out
  of the corpus file at runtime (`runtime/lint_prose.py`, which loads
  `corpus/prose-integrity/banned-lists.md`). Run
  `python runtime/lint_prose.py <file>` with the applicable profile to apply
  every lexical check mechanically instead of scanning by eye.
- **Region discipline.** The lists apply to model-authored prose only. Code,
  quoted text, structured data, and identifiers are excluded regions and are
  never flagged; see `references/prose-integrity.md` for the shared scan
  region and per-rule triggers.
