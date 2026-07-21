"""Region vocabulary, lattice, and classifier for the STOW applicability
engine (Subsystem S3, Task T1).

Pins the closed region vocabulary and the ``expand()`` lattice from
RESOLVER-DESIGN.md section "2. Input model", reconciled against the ACTUAL
``skills/stow/rules/registry.yaml`` ``scope.include`` / ``scope.exclude``
token vocabulary across all 104 records. No reconciliation gap was found:
the registry's five ``scope.include`` tokens and its uniform four-kind
``scope.exclude`` match the design doc's vocabulary exactly (verified by
``tests/test_applicability_regions.py``, which loads the live registry
rather than trusting this comment). Nothing in this module reads or writes
``registry.yaml`` at runtime; the vocabulary below is reproduced as pinned
constants only.

``classify()`` operates on already-labeled spans. Per RESOLVER-DESIGN.md
section 2, "no free text is interpreted at resolve time (extraction happens
upstream and is passed in)" -- this module does not decide that a stretch
of text IS ``code`` or IS ``safety-prose``; it validates a caller-supplied
label against the closed leaf vocabulary and derives ``is_protected``. A
label outside the closed vocabulary is rejected, never guessed into
"prose" -- RESOLVER-DESIGN.md section 5 calls a mislabeled protected span
"the one unsafe firewall failure mode," so failing closed here is the
region-classifier conformance boundary (FIX-7) that any INV-1/INV-2 claim
depends on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Optional

from tools.applicability.model import Region

# ---------------------------------------------------------------------------
# Writable (prose) scope.include tokens -- the registry's actual vocabulary.
# ---------------------------------------------------------------------------
# Confirmed against skills/stow/rules/registry.yaml: across all 104 records
# scope.include only ever takes these five values (77 records: all-prose;
# 11: user-facing-output; 3: procedural-prose; 6: descriptive-prose;
# 3: safety-prose; 2 each of the procedural+descriptive and
# procedural+safety pairs). Matches RESOLVER-DESIGN.md section 2 verbatim.
WRITABLE_SCOPE_TOKENS: FrozenSet[str] = frozenset(
    {
        "all-prose",
        "user-facing-output",
        "procedural-prose",
        "descriptive-prose",
        "safety-prose",
    }
)

# ---------------------------------------------------------------------------
# Protected leaf kinds -- the uniform scope.exclude on all 104 records.
# ---------------------------------------------------------------------------
PROTECTED_KINDS: FrozenSet[str] = frozenset(
    {
        "code",
        "structured-data",
        "quoted-text",
        "identifiers",
    }
)

# ---------------------------------------------------------------------------
# Editable (writable) leaf kinds -- the concrete per-span classification a
# non-protected Region may carry. ``plain-prose`` has no scope.include token
# of its own; it is only ever reached through expand(all-prose) /
# expand(user-facing-output), per RESOLVER-DESIGN.md section 2.
# ---------------------------------------------------------------------------
WRITABLE_LEAF_KINDS: FrozenSet[str] = frozenset(
    {
        "procedural-prose",
        "descriptive-prose",
        "safety-prose",
        "plain-prose",
    }
)

# The closed set of concrete leaf kinds a Region.kind may take -- exactly
# the union of the writable and protected leaves, eight total.
LEAF_KINDS: FrozenSet[str] = WRITABLE_LEAF_KINDS | PROTECTED_KINDS

# ---------------------------------------------------------------------------
# The pinned expand() lattice -- verbatim from RESOLVER-DESIGN.md section 2.
# ---------------------------------------------------------------------------
# ``user-facing-output`` is described as the whole user-facing prose surface
# (superset of ``all-prose``); as pinned in the design doc the two rows are
# equal sets today (both expand to all four writable leaves), so the
# superset relation holds by equality. No editable token expands to a
# protected leaf, which is the INV-1 precondition: writeset() can never
# contain a protected span by construction.
_EXPAND_TABLE = {
    "all-prose": frozenset(
        {"procedural-prose", "descriptive-prose", "safety-prose", "plain-prose"}
    ),
    "user-facing-output": frozenset(
        {"procedural-prose", "descriptive-prose", "safety-prose", "plain-prose"}
    ),
    "procedural-prose": frozenset({"procedural-prose"}),
    "descriptive-prose": frozenset({"descriptive-prose"}),
    "safety-prose": frozenset({"safety-prose"}),
}

assert set(_EXPAND_TABLE) == WRITABLE_SCOPE_TOKENS  # the lattice covers every token, no more, no less


def expand(token: str) -> FrozenSet[str]:
    """Expand one ``scope.include`` token to its concrete writable leaf
    kinds, per the pinned lattice above.

    Defined only over the five ``WRITABLE_SCOPE_TOKENS``; raises
    ``ValueError`` for anything else, including a protected kind, so an
    unrecognized or out-of-vocabulary token never silently expands to an
    empty or guessed set (fail closed, matching ``classify()`` below).
    """

    try:
        return _EXPAND_TABLE[token]
    except KeyError:
        raise ValueError(f"unknown scope.include token: {token!r}") from None


@dataclass(frozen=True)
class RawSpan:
    """An already-labeled span handed to :func:`classify`.

    The label (``kind``) is decided upstream, by whatever extracted the
    span from a request or artifact; ``classify()`` only validates it
    against the closed leaf vocabulary and derives ``is_protected``. It
    never inspects ``text`` and this type carries none, precisely to keep
    that boundary honest: nothing downstream of extraction can re-derive a
    kind from content here.
    """

    id: int
    kind: str
    subkind: Optional[str] = None


def classify(spans: Iterable[RawSpan]) -> List[Region]:
    """Classify already-labeled spans into typed :class:`Region` objects,
    sorted by id (RESOLVER-DESIGN.md S0 canonicalization: "Sort regions by
    id").

    Each span's ``kind`` must be one of the eight closed leaves in
    :data:`LEAF_KINDS`. A span carrying any other label raises
    ``ValueError`` -- it is never coerced into a writable kind and never
    silently dropped. This fail-closed behavior is the region-classifier
    conformance boundary: RESOLVER-DESIGN.md section 5 identifies a
    mislabeled protected span (for example ``code`` tagged as
    ``plain-prose``) as the one firewall failure the downstream S10
    assertions cannot detect on their own, because the corruption happens
    upstream of the math. This function is the last point that can refuse
    an out-of-vocabulary label before it reaches the firewall.
    """

    out: List[Region] = []
    for span in spans:
        if span.kind not in LEAF_KINDS:
            raise ValueError(f"unknown leaf kind: {span.kind!r}")
        out.append(
            Region(
                id=span.id,
                kind=span.kind,
                is_protected=span.kind in PROTECTED_KINDS,
                subkind=span.subkind,
            )
        )
    out.sort(key=lambda region: region.id)
    return out
