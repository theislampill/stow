"""Data model for the STOW applicability engine (Subsystem S3, Task T1).

Frozen, side-effect-free dataclasses mirroring RESOLVER-DESIGN.md section
"2. Input model" (``ResolveInput``) and section "4. Output shape"
(``ResolutionResult``). No free text is interpreted here -- extraction
happens upstream and is handed in already typed ("no free text is
interpreted at resolve time," RESOLVER-DESIGN.md section 2).

This module defines the shapes only. The thirteen-step resolution
algorithm (S0-S12) that populates a ``ResolutionResult`` from a
``ResolveInput`` is out of scope for this task and lands in a later one.

Naming note (judgment call, see task report): RESOLVER-DESIGN.md names the
profile field ``profile_request`` and the signal map ``signals`` /
``ContextSignals``; this task's brief asked for ``profile_ctx`` and
``context`` respectively, so those are the names used here. The shapes are
otherwise unchanged from the design doc.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple


class Tristate(str, Enum):
    """A first-class tri-state value: {true, false, unknown}.

    RESOLVER-DESIGN.md is explicit that ``unknown`` is not a degraded or
    default boolean: "`unknown` is the only source of an `unknown` verdict.
    A signal that is present but wrong yields a confidently wrong (still
    deterministic) verdict; only a missing signal becomes `unknown`, and it
    is never guessed." Modeling it as a bare ``bool | None`` would let
    ``None`` collapse into falsy contexts by accident; this enum cannot.
    """

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class ApplicabilityStatus(str, Enum):
    """Per-rule resolution status. RESOLVER-DESIGN.md section 4."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class ReasonCode(str, Enum):
    """Closed reason-tag vocabulary. RESOLVER-DESIGN.md section 4
    ``rules[].reason_code``."""

    NO_SURFACE = "no-surface"
    SIGNAL_FALSE = "signal-false"
    SIGNAL_UNKNOWN = "signal-unknown"
    PROFILE_INACTIVE = "profile-inactive"
    APPLICABILITY_FALSE = "applicability-false"
    APPLICABILITY_UNOBSERVED = "applicability-unobserved"
    PASS = "pass"


@dataclass(frozen=True)
class Region:
    """One typed, classified region span.

    RESOLVER-DESIGN.md section 2 pins ``{ id, leaf_kind, is_protected }``;
    this task's brief additionally asks for a ``subkind`` field. ``kind``
    here is that ``leaf_kind`` -- the concrete per-span classification, one
    of the eight closed leaves in ``regions.LEAF_KINDS``. ``subkind`` is
    reserved for a future finer-grained tag *within* a leaf kind (for
    example distinguishing an attributed from an unattributed
    ``quoted-text`` span -- RESOLVER-DESIGN.md open question 1); this task's
    ``regions.classify()`` never infers or populates it, only passes through
    a caller-supplied value. ``is_protected`` is derived, never a free
    caller choice: it is True iff ``kind`` is in the four-kind protected set.
    """

    id: int
    kind: str
    is_protected: bool
    subkind: Optional[str] = None


@dataclass(frozen=True)
class RequestMode:
    """RESOLVER-DESIGN.md section 2 ``request_mode``."""

    contract_kind: str
    intent: str
    quotes_present: bool


@dataclass(frozen=True)
class ProfileContext:
    """RESOLVER-DESIGN.md section 2 ``profile_request`` (named
    ``profile_ctx`` on ``ResolveInput`` per this task's brief)."""

    explicit: Optional[str] = None
    auto_contexts: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolveInput:
    """RESOLVER-DESIGN.md section 2 ``ResolveInput``.

    ``context`` is the tri-state signal map (RESOLVER-DESIGN.md
    ``ContextSignals``, named ``context`` per this task's brief): one
    ``Tristate`` per named signal. It is intentionally a plain mapping
    rather than a fixed set of dataclass fields, so a new signal can be
    added without a schema change; the closed set of signal names it may
    carry is enumerated in RESOLVER-DESIGN.md section 2 and is not
    re-validated by this data-model task.
    """

    request_mode: RequestMode
    profile_ctx: ProfileContext
    regions: Tuple[Region, ...]
    context: Mapping[str, Tristate]

    def signal(self, name: str) -> Tristate:
        """Look up one context signal, defaulting an absent signal to
        UNKNOWN rather than raising. Mirrors RESOLVER-DESIGN.md S0:
        "Default any absent signal to unknown." A signal is only ever
        UNKNOWN because it is missing or explicitly recorded as such --
        never guessed."""

        return self.context.get(name, Tristate.UNKNOWN)


@dataclass(frozen=True)
class RuleResolution:
    """One rule's resolved status. RESOLVER-DESIGN.md section 4
    ``rules[]``, restricted to this task's brief: status plus a reason
    tag. The remaining ``rules[]`` fields (``plane``, ``binding``,
    ``enforcement_mode``, ``write_regions``, ``read_regions``, ...) belong
    to the algorithm task that builds a full ``ResolutionResult``."""

    rule_id: str
    status: ApplicabilityStatus
    reason: ReasonCode


@dataclass(frozen=True)
class ResolutionResult:
    """RESOLVER-DESIGN.md section 4 ``ResolutionResult``, restricted to
    this task's brief: per-rule status/reason, ``protected_region_exclusions``
    (the INV-2 anchor), and ``unknown_applicability[]`` (the PASS-gate
    input, RESOLVER-DESIGN.md section 10). Fields are populated by the
    resolution algorithm in a later task; this dataclass only fixes the
    shape.
    """

    rules: Tuple[RuleResolution, ...]
    protected_region_exclusions: Tuple[int, ...]
    unknown_applicability: Tuple[str, ...]
