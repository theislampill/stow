"""Closure contracts for deep prose and action-shaping absorption.

These tests protect semantic boundaries, not source genealogy. Contextual
behaviour still requires paired model evidence; the assertions here prevent a
future carrier or registry edit from silently dropping the accepted semantics.
"""

from pathlib import Path

from ruamel.yaml import YAML


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "stow"
EVIDENCE = REPO / "tests" / "evals" / "deep-absorption-v1.yaml"


def _yaml(path):
    with path.open(encoding="utf-8") as handle:
        return YAML(typ="safe").load(handle)


def _records():
    return {
        record["id"]: record
        for record in _yaml(SKILL / "rules" / "registry.yaml")["records"]
    }


def test_contextual_prose_carrier_covers_the_absorbed_boundaries():
    text = (SKILL / "references" / "descriptive-prose.md").read_text(
        encoding="utf-8"
    ).casefold()

    required = (
        "functionless conclusion or restatement",
        "repeated paragraph openings",
        "uniform sentence or paragraph shapes",
        "dramatic heading",
        "blanket hedging",
        "literal or established technical sense",
        "protected quotation, identifier, code, path, or data value",
        "compact paired examples",
        "does this match reveal an independent writing harm",
    )
    for phrase in required:
        assert phrase in text, phrase


def test_heading_and_uncertainty_owners_expose_contextual_applicability():
    records = _records()
    uncertainty = records["STOW-PRO-015"]
    heading = records["STOW-PRO-016"]

    assert "contextual prose-quality review" in uncertainty["activation"]["predicate"]
    assert "uncertainty lacks an evidence boundary" in (
        uncertainty["activation"]["applicability"]
    )
    assert "stacked qualifiers" in uncertainty["activation"]["applicability"]
    assert uncertainty["activation"]["always_on_for_prose"] is False

    assert "dramatizes" in heading["activation"]["applicability"]
    assert "requested voice" in heading["activation"]["exception"]
    assert heading["enforcement"]["kind"] == "semantic-review"
    assert heading["enforcement"]["validator"] is None


def test_action_owners_encode_boundedness_state_and_tangent_exceptions():
    records = _records()
    opening = records["STOW-ACT-001"]
    steps = records["STOW-ACT-002"]
    tangent = records["STOW-ACT-004"]
    state = records["STOW-ACT-005"]

    assert "safety or decision context" in opening["activation"]["exception"]
    assert "bounded, task-complete actions" in steps["title"]
    assert "exhaustive required material" in steps["activation"]["exception"]
    assert "blocking question" in tangent["activation"]["exception"]
    assert tangent["enforcement"]["kind"] == "semantic-review"
    assert tangent["enforcement"]["validator"] is None
    assert "changed progress" in state["title"]
    assert "no material state change" in state["activation"]["exception"]


def test_kernel_and_cold_action_carrier_preserve_complete_complex_work():
    kernel = " ".join(
        (SKILL / "SKILL.md").read_text(encoding="utf-8").split()
    ).casefold()
    reference = " ".join(
        (SKILL / "references" / "action-shaping.md")
        .read_text(encoding="utf-8")
        .split()
    ).casefold()
    continuity = " ".join(
        (SKILL / "references" / "continuity-and-state.md")
        .read_text(encoding="utf-8")
        .split()
    ).casefold()

    assert "bounded, task-complete actions" in kernel
    assert "preserve exhaustive required material" in kernel
    assert "externalize changed state without repeating a full ledger" in kernel
    assert "defer secondary issues without dropping them" in kernel

    for phrase in (
        "context can precede the action when the reader must understand it to decide or act safely",
        "do not impose an arbitrary item cap",
        "answer a blocking question in place",
        "report only material state changes",
        "cannot delete required exhaustive or discursive content",
    ):
        assert phrase in reference, phrase

    assert "do not repeat the full ledger when no material state changed" in continuity


def test_composition_registry_protects_safety_and_exhaustive_contracts():
    entries = _yaml(SKILL / "rules" / "conflicts.yaml")["conflicts"]
    by_id = {entry["id"]: entry for entry in entries}

    safety = by_id["CFL-020"]
    complete = by_id["CFL-021"]
    assert {p["ref"] for p in safety["participants"]} == {
        "STOW-ACT-001", "system"
    }
    assert safety["winner"]["band"] in {"system", "contract"}
    assert "context before the action" in safety["permitted_substitute"]

    assert {p["ref"] for p in complete["participants"]} == {
        "STOW-ACT-002", "contract"
    }
    assert complete["winner"]["band"] == "contract"
    assert "preserve every required item" in complete["permitted_substitute"].casefold()

    kernel = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
    opening = _records()["STOW-ACT-001"]["activation"]["exception"].casefold()
    assert "safety or decision context" in opening
    assert "system" in kernel and "exact output contract" in kernel
    assert "nothing required was dropped" in kernel


def test_no_new_profile_route_or_runtime_checker_is_needed():
    profiles = _yaml(SKILL / "rules" / "profiles.json")["profiles"]
    routes = _yaml(SKILL / "rules" / "routing.yaml")["routes"]
    assert {profile["id"] for profile in profiles} == {
        "stow-default",
        "technical-clarity",
        "controlled-technical-guided",
        "controlled-technical-strict",
    }
    assert not any(route["mode"] == "deep-absorption" for route in routes)

    runtime_names = {
        path.name for path in (SKILL / "runtime").glob("*.py")
    }
    assert runtime_names == {
        "dictionary_lookup.py",
        "lint_prose.py",
        "profiles.py",
        "query_rules.py",
        "validate.py",
        "validate_terms.py",
    }
    records = _records().values()
    advisory_count = sum(
        len(record.get("enforcement", {}).get("advisory_validators") or [])
        for record in records
    )
    assert advisory_count == 10
    assert len(routes) == 23


def test_deep_absorption_evidence_is_terminal_and_owner_bound():
    evidence = _yaml(EVIDENCE)
    owners = set(_records())

    assert evidence["status"] == "qualified"
    assert evidence["no_retry_or_tuning"] is True
    assert evidence["prose"]["mechanical_preservation"] == "12/12"
    assert evidence["action"]["mechanical_preservation"] == "16/16"
    assert evidence["prose"]["blind_reviews"] == [
        "QUALIFIED",
        "QUALIFIED",
    ]
    assert evidence["action"]["blind_reviews"] == [
        "QUALIFIED",
        "QUALIFIED",
    ]
    assert evidence["prose"]["carrier"] == "references/descriptive-prose.md"
    assert evidence["action"]["carrier"] == "references/action-shaping.md"
    assert evidence["prose"]["mechanism"] == "contextual-g1"
    assert evidence["action"]["mechanism"] == "contextual-g1"
    prose_owner_map = {
        family["id"]: set(family["owners"])
        for family in evidence["prose"]["families"]
    }
    assert prose_owner_map == {
        "filler-process-empty-closer": {"STOW-PRO-006", "STOW-PRO-011"},
        "hollow-evaluation": {"STOW-PRO-005", "STOW-PRO-013"},
        "false-contrast-escalation": {"STOW-PRO-009", "STOW-PRO-020"},
        "repetitive-shapes": {"STOW-PRO-007"},
        "blanket-hedging": {"STOW-PRO-015", "STOW-PRO-020"},
        "dramatic-heading-inflated-metaphor": {
            "STOW-PRO-016",
            "STOW-PRO-020",
        },
    }
    action_owner_map = {
        family["id"]: set(family["owners"])
        for family in evidence["action"]["families"]
    }
    assert action_owner_map == {
        "action-and-secondary-deferral": {"STOW-ACT-001", "STOW-ACT-004"},
        "bounded-task-complete-actions": {"STOW-ACT-002"},
        "changed-progress": {"STOW-ACT-005"},
        "defer-versus-block": {"STOW-ACT-004"},
        "exhaustive-contract": {"STOW-ACT-002"},
        "decision-context": {"STOW-ACT-001"},
        "safety-precedence": {"STOW-ACT-001"},
        "anti-overprescription": {
            "STOW-ACT-002",
            "STOW-ACT-004",
            "STOW-ACT-005",
        },
    }
    boundary = evidence["evidence_boundary"].casefold()
    for phrase in (
        "one exact behavior-bearing kernel and cold carrier",
        "not independent model populations",
        "does not establish universal behaviour",
        "delivery custody",
    ):
        assert phrase in boundary

    for suite in (evidence["prose"], evidence["action"]):
        assert suite["families"]
        for family in suite["families"]:
            assert family["pathology"]
            assert family["countercontrol"]
            assert set(family["owners"]) <= owners
