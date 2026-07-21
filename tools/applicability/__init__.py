"""STOW applicability engine (Phase 2.5).

Off the hot path: this package is tooling for later phases (P3 routing
prediction, P5 dogfood, P6 attestation), not part of the per-response
runtime. ``tools/`` is not package-walked by ``tools/build_skill.py``, so
nothing here ships in the built skill artifact.

Design authority: ``.IMPLEMENTAUDIT/runs/stow-normalization-20260720/
RESOLVER-DESIGN.md`` (not reproduced here; read it directly for the
algorithm, invariants, and worked examples).

This subsystem is delivered task by task. Subsystem S3, Task T1 (this
package's first contents) is the region classifier and data model only:

- ``regions``: the closed region vocabulary, the pinned ``expand()``
  lattice, and ``classify()``, the region-classifier conformance boundary
  (RESOLVER-DESIGN.md FIX-7).
- ``model``: the ``ResolveInput`` / ``ResolutionResult`` frozen dataclasses
  and the first-class ``Tristate`` value.

Everything here is read-only tooling: it reads the frozen registry and
cold sidecar, and never mutates ``scope``/``category``/``activation``/
``baseline_text`` on any record.
"""
