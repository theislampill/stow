"""Tests for the applicability engine's region classifier and data model
(Subsystem S3, Task T1).

This module is the region-classifier CONFORMANCE test referenced by
RESOLVER-DESIGN.md FIX-7: "the independent region-classifier conformance
test is a hard gating dependency for any INV-1/INV-2 claim." A mislabeled
protected span (code/structured-data/quoted-text/identifiers tagged as
prose) is, per RESOLVER-DESIGN.md section 5, "the one unsafe firewall
failure mode" -- every S10 assertion downstream passes even when the
corruption is upstream. This file is the check that the classifier never
lets that happen: every protected kind must come out tagged
``is_protected=True`` and every writable kind must come out
``is_protected=False``, with no exceptions and no silent guessing on an
unrecognized label.

Run only this file: ``python -m pytest tests/test_applicability_regions.py -v``.
"""

import os

import pytest
from ruamel.yaml import YAML

from tools.applicability import model, regions

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")


def _load_registry():
    y = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        return y.load(fh)


# ---------------------------------------------------------------------------
# Vocabulary conformance: regions.py's pinned constants against the ACTUAL
# registry.yaml scope.include / scope.exclude tokens across all 104 records.
# ---------------------------------------------------------------------------

def test_registry_has_104_records():
    data = _load_registry()
    assert data["generated_counts"]["primary_total"] == 104
    assert len(data["records"]) == 104


def test_writable_scope_tokens_match_registry_scope_include():
    data = _load_registry()
    seen = set()
    for record in data["records"]:
        seen.update(record["scope"]["include"])
    assert seen == regions.WRITABLE_SCOPE_TOKENS
    # Pinned per RESOLVER-DESIGN.md input_model: exactly these five tokens.
    assert seen == {
        "all-prose",
        "user-facing-output",
        "procedural-prose",
        "descriptive-prose",
        "safety-prose",
    }


def test_protected_kinds_match_registry_scope_exclude_uniformly():
    data = _load_registry()
    exclude_sets = {tuple(sorted(r["scope"]["exclude"])) for r in data["records"]}
    # Every one of the 104 records carries the identical four-kind exclude.
    assert exclude_sets == {("code", "identifiers", "quoted-text", "structured-data")}
    assert set(exclude_sets.pop()) == regions.PROTECTED_KINDS
    assert regions.PROTECTED_KINDS == {
        "code",
        "structured-data",
        "quoted-text",
        "identifiers",
    }


# ---------------------------------------------------------------------------
# expand() lattice
# ---------------------------------------------------------------------------

def test_expand_all_prose_returns_exactly_the_four_prose_subkinds():
    assert regions.expand("all-prose") == {
        "procedural-prose",
        "descriptive-prose",
        "safety-prose",
        "plain-prose",
    }


def test_user_facing_output_is_superset_of_all_prose():
    assert regions.expand("user-facing-output") >= regions.expand("all-prose")


def test_expand_identity_tokens_expand_to_themselves():
    assert regions.expand("procedural-prose") == {"procedural-prose"}
    assert regions.expand("descriptive-prose") == {"descriptive-prose"}
    assert regions.expand("safety-prose") == {"safety-prose"}


def test_expand_never_yields_a_protected_leaf():
    for token in regions.WRITABLE_SCOPE_TOKENS:
        assert regions.expand(token).isdisjoint(regions.PROTECTED_KINDS)


def test_expand_unknown_token_raises_value_error():
    with pytest.raises(ValueError):
        regions.expand("not-a-real-token")


def test_expand_rejects_protected_kinds_as_input():
    # expand() is only defined over scope.include tokens; a protected kind
    # is not one of the five and must not silently expand to itself.
    for kind in regions.PROTECTED_KINDS:
        with pytest.raises(ValueError):
            regions.expand(kind)


# ---------------------------------------------------------------------------
# classify(): labeled-span fixtures -> typed Region objects
# ---------------------------------------------------------------------------

ALL_LEAF_KIND_FIXTURES = [
    regions.RawSpan(id=1, kind="procedural-prose"),
    regions.RawSpan(id=2, kind="descriptive-prose"),
    regions.RawSpan(id=3, kind="safety-prose"),
    regions.RawSpan(id=4, kind="plain-prose"),
    regions.RawSpan(id=5, kind="code"),
    regions.RawSpan(id=6, kind="structured-data"),
    regions.RawSpan(id=7, kind="quoted-text"),
    regions.RawSpan(id=8, kind="identifiers"),
]


def test_classify_tags_each_kind_correctly():
    result = regions.classify(ALL_LEAF_KIND_FIXTURES)
    by_id = {r.id: r for r in result}
    assert len(result) == 8
    for span in ALL_LEAF_KIND_FIXTURES:
        assert by_id[span.id].kind == span.kind


def test_classify_every_protected_kind_is_tagged_protected_and_non_writable():
    """The hard gate: RESOLVER-DESIGN.md FIX-7. Every protected leaf kind
    MUST classify as is_protected=True and MUST NOT be a writable leaf kind.
    This is the trust boundary any firewall (INV-1/INV-2) claim rests on."""
    fixtures = [
        regions.RawSpan(id=100 + i, kind=kind)
        for i, kind in enumerate(sorted(regions.PROTECTED_KINDS))
    ]
    result = regions.classify(fixtures)
    assert len(result) == len(regions.PROTECTED_KINDS)
    for region in result:
        assert region.kind in regions.PROTECTED_KINDS
        assert region.is_protected is True
        assert region.kind not in regions.WRITABLE_LEAF_KINDS


def test_classify_every_writable_kind_is_tagged_non_protected():
    fixtures = [
        regions.RawSpan(id=200 + i, kind=kind)
        for i, kind in enumerate(sorted(regions.WRITABLE_LEAF_KINDS))
    ]
    result = regions.classify(fixtures)
    assert len(result) == len(regions.WRITABLE_LEAF_KINDS)
    for region in result:
        assert region.kind in regions.WRITABLE_LEAF_KINDS
        assert region.is_protected is False
        assert region.kind not in regions.PROTECTED_KINDS


def test_leaf_kinds_partition_writable_and_protected_with_no_overlap():
    assert regions.WRITABLE_LEAF_KINDS.isdisjoint(regions.PROTECTED_KINDS)
    assert regions.LEAF_KINDS == regions.WRITABLE_LEAF_KINDS | regions.PROTECTED_KINDS
    assert len(regions.LEAF_KINDS) == 8


def test_classify_preserves_subkind_passthrough():
    fixtures = [regions.RawSpan(id=1, kind="quoted-text", subkind="attributed")]
    result = regions.classify(fixtures)
    assert result[0].subkind == "attributed"


def test_classify_defaults_subkind_to_none():
    result = regions.classify([regions.RawSpan(id=1, kind="code")])
    assert result[0].subkind is None


def test_classify_sorts_output_by_id():
    fixtures = [
        regions.RawSpan(id=3, kind="code"),
        regions.RawSpan(id=1, kind="plain-prose"),
        regions.RawSpan(id=2, kind="identifiers"),
    ]
    result = regions.classify(fixtures)
    assert [r.id for r in result] == [1, 2, 3]


def test_classify_fails_closed_on_unrecognized_kind():
    """A mislabeled/unrecognized span must never be silently accepted as
    prose (or anything else); it must raise, not guess."""
    with pytest.raises(ValueError):
        regions.classify([regions.RawSpan(id=1, kind="not-a-real-leaf-kind")])


def test_classify_empty_input_returns_empty_list():
    assert regions.classify([]) == []


def test_classify_returns_model_region_instances():
    result = regions.classify([regions.RawSpan(id=1, kind="code")])
    assert isinstance(result[0], model.Region)


# ---------------------------------------------------------------------------
# model.py: tri-state and dataclass shape
# ---------------------------------------------------------------------------

def test_tristate_is_first_class_not_a_bool():
    assert model.Tristate.TRUE != True  # noqa: E712 -- deliberately checking identity, not truthiness
    assert model.Tristate.FALSE != False  # noqa: E712
    assert model.Tristate.UNKNOWN not in (True, False)
    assert {model.Tristate.TRUE, model.Tristate.FALSE, model.Tristate.UNKNOWN} == set(model.Tristate)
    assert len(model.Tristate) == 3


def test_region_is_protected_is_a_bool_field():
    region = model.Region(id=1, kind="code", is_protected=True)
    assert region.is_protected is True
    assert region.subkind is None


def test_resolve_input_signal_defaults_absent_to_unknown():
    ri = model.ResolveInput(
        request_mode=model.RequestMode(
            contract_kind="conversational-prose", intent="informational", quotes_present=False
        ),
        profile_ctx=model.ProfileContext(),
        regions=(),
        context={"safety_content": model.Tristate.TRUE},
    )
    assert ri.signal("safety_content") == model.Tristate.TRUE
    assert ri.signal("artifact_mutation") == model.Tristate.UNKNOWN


def test_resolve_input_and_resolution_result_are_frozen():
    ri = model.ResolveInput(
        request_mode=model.RequestMode(
            contract_kind="conversational-prose", intent="informational", quotes_present=False
        ),
        profile_ctx=model.ProfileContext(),
        regions=(),
        context={},
    )
    with pytest.raises(Exception):
        ri.regions = (1,)

    result = model.ResolutionResult(
        rules=(),
        protected_region_exclusions=(),
        unknown_applicability=(),
    )
    with pytest.raises(Exception):
        result.rules = (1,)


def test_rule_resolution_status_is_closed_tristate_like_enum():
    values = {status.value for status in model.ApplicabilityStatus}
    assert values == {"applicable", "not_applicable", "unknown"}


def test_resolution_result_unknown_applicability_is_first_class():
    resolution = model.RuleResolution(
        rule_id="STOW-SAF-001",
        status=model.ApplicabilityStatus.UNKNOWN,
        reason=model.ReasonCode.SIGNAL_UNKNOWN,
    )
    result = model.ResolutionResult(
        rules=(resolution,),
        protected_region_exclusions=(),
        unknown_applicability=("STOW-SAF-001",),
    )
    assert result.unknown_applicability == ("STOW-SAF-001",)
    assert result.rules[0].status == model.ApplicabilityStatus.UNKNOWN
