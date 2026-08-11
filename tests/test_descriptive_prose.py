"""Structural and false-positive gates for contextual prose review.

The fixture corpus is static specification evidence. It exercises the shipped
advisory runtime over natural work and a deliberate house-style control; it is
not evidence from a live model comparison.
"""

import importlib.util
import os
import re

from ruamel.yaml import YAML


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL_DIR = os.path.join(REPO, "skills", "stow")
REFERENCE = os.path.join(SKILL_DIR, "references", "descriptive-prose.md")
KERNEL = os.path.join(SKILL_DIR, "SKILL.md")
REGISTRY = os.path.join(SKILL_DIR, "rules", "registry.yaml")
ROUTING = os.path.join(SKILL_DIR, "rules", "routing.yaml")
FIXTURE = os.path.join(HERE, "fixtures", "descriptive-prose", "v1.yaml")
LINTER = os.path.join(SKILL_DIR, "runtime", "lint_prose.py")
PROSE_REFERENCE = os.path.join(SKILL_DIR, "references", "prose-integrity.md")
LOOKUP_REFERENCE = os.path.join(
    SKILL_DIR, "references", "ai-writing-detection.md")
USER_REFERENCE = os.path.join(
    SKILL_DIR, "references", "user-facing-output.md")

LEAVES = (
    "semantic repetition",
    "empty metadiscourse",
    "manufactured contrast or escalation",
    "hollow evaluation",
    "mechanical symmetry or fragmentation",
    "heading opacity or unnecessary sectioning",
    "epistemic opacity",
    "lexical inflation or cliché clusters",
)

FIELDS = (
    "Description",
    "Rationale",
    "Applicability",
    "Legitimate counterexample",
    "Rewrite principle",
    "Mechanism",
)

EXPECTED_TITLES = {
    "STOW-PRO-001": "Use em dashes only under an explicit style contract",
    "STOW-PRO-006": "Functionless semantic repetition",
    "STOW-PRO-013": "Evidence-grounded requested voice",
    "STOW-PRO-015": "Grounded uncertainty",
    "STOW-PRO-020": "Review formulaic lexical patterns",
}

OFF_HOT_PATH = {
    "STOW-PRO-001",
    "STOW-PRO-020",
}

REQUIRED_CONTROL_KINDS = {
    "informational",
    "explanatory",
    "technical",
    "procedural",
    "code-adjacent",
    "deliberate-human-style",
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle)


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _records():
    return {record["id"]: record for record in _yaml(REGISTRY)["records"]}


def test_detailed_reference_has_the_complete_taxonomy():
    text = _read(REFERENCE)
    headings = re.findall(r"^## (.+)$", text, re.M)
    assert [heading.casefold() for heading in headings] == list(LEAVES)
    for index, leaf in enumerate(LEAVES):
        start = text.index("## " + headings[index])
        end = text.find("\n## ", start + 1)
        section = text[start:end if end != -1 else len(text)]
        for field in FIELDS:
            assert re.search(r"^- \*\*%s:\*\* \S" % re.escape(field), section, re.M), (
                "%s lacks %s" % (leaf, field))


def test_kernel_and_routing_have_one_contextual_review_route():
    kernel = _read(KERNEL)
    target_lines = [
        line for line in kernel.splitlines()
        if "references/descriptive-prose.md" in line
    ]
    assert target_lines == [
        "- contextual prose-quality review -> references/descriptive-prose.md"
    ]
    routes = [
        route for route in _yaml(ROUTING)["routes"]
        if route["references"] == ["references/descriptive-prose.md"]
    ]
    assert len(routes) == 1
    assert routes[0]["mode"] == "descriptive-prose-review"
    assert routes[0]["predicate"] == "contextual prose-quality review"


def test_target_registry_titles_and_qualifiers_are_contextual():
    records = _records()
    for rule_id, title in EXPECTED_TITLES.items():
        record = records[rule_id]
        assert record["title"] == title
        activation = record["activation"]
        assert activation.get("applicability")
        assert activation.get("exception")

    assert "functional repetition" in records["STOW-PRO-006"]["activation"]["exception"]
    assert "requested voice" in records["STOW-PRO-013"]["activation"]["exception"]
    assert "justified uncertainty" in records["STOW-PRO-015"]["activation"]["exception"]
    assert "technical" in records["STOW-PRO-020"]["activation"]["exception"]


def test_contextual_rules_leave_the_ordinary_selector_and_keep_advisory_signals():
    records = _records()
    for rule_id in OFF_HOT_PATH:
        record = records[rule_id]
        assert record["activation"]["always_on_for_prose"] is False
        assert record["enforcement"]["status"] == "review-fallback"
        assert record["enforcement"]["validator"] is None
        assert record["enforcement"]["advisory_validators"]


def test_compact_digest_is_instrumental_and_points_to_detail():
    text = _read(os.path.join(SKILL_DIR, "references", "always-on.md"))
    digest = text.split("## Descriptive prose digest", 1)[1]
    assert "Authorship is irrelevant." in digest
    for leaf in LEAVES:
        assert re.search(r"^- %s:" % re.escape(leaf), digest, re.M), leaf
    assert "references/descriptive-prose.md" in digest
    for label in ("AI", "machine-written", "human-written", "generated text"):
        assert label not in digest


def test_versioned_controls_cover_natural_work_and_deliberate_style():
    fixture = _yaml(FIXTURE)
    assert fixture["schema_version"] == 1
    assert fixture["evidence_kind"] == "static-specification"
    controls = fixture["controls"]
    assert {control["kind"] for control in controls} == REQUIRED_CONTROL_KINDS
    assert len({control["id"] for control in controls}) == len(controls)
    assert all(control["text"].strip() for control in controls)


def test_corrective_contrast_has_a_paired_contextual_microchallenge():
    fixture = _yaml(FIXTURE)
    cases = {case["id"]: case for case in fixture["paired_microchallenges"]}
    case = cases["corrective-contrast"]
    assert case["rule_id"] == "STOW-PRO-020"
    assert "not merely" in case["pathology"]
    assert "report calls" in case["negative_control"]
    assert "absent or materially implausible" in case["criterion"]


def test_corrective_contrast_is_owned_by_the_contextual_lexical_rule():
    record = _records()["STOW-PRO-020"]
    assert "corrective contrast" in record["activation"]["applicability"]
    assert "discourse-present correction" in record["activation"]["exception"]


def test_closed_matches_request_contextual_review_without_defect_labels():
    lint_prose = _module("lint_prose_for_descriptive_controls", LINTER)
    tables = lint_prose.load_banned_lists()
    for control in _yaml(FIXTURE)["controls"]:
        findings = lint_prose.lint(control["text"], tables=tables)
        expected = set(control["expected_advisories"])
        assert {finding.rule for finding in findings} == expected, control["id"]
        for finding in findings:
            message = finding.message.casefold()
            assert "review" in message, (control["id"], finding.message)
            for label in ("authorship", "machine-written", "human-written", "ai tell",
                          "banned opener", "overused verb", "automatic defect"):
                assert label not in message, (control["id"], finding.message)


def test_cold_prose_references_do_not_restore_authorship_blacklists():
    references = {
        "prose-integrity": _read(PROSE_REFERENCE),
        "banned-list lookup": _read(LOOKUP_REFERENCE),
    }
    combined = re.sub(
        r"\s+", " ", "\n".join(references.values()).casefold())
    forbidden = (
        "surface tells of machine writing",
        "ban the em dash",
        "no ai verbs",
        "no ai transition phrases",
        "zero tolerance",
        "machine tells",
        "run always-on",
        "apply every lexical check mechanically",
        "never flagged",
    )
    for phrase in forbidden:
        assert phrase not in combined, phrase

    assert "references/descriptive-prose.md" in references["prose-integrity"]
    for name, text in references.items():
        assert "advisory" in text.casefold(), name


def test_redundant_user_facing_reference_and_route_are_removed():
    assert not os.path.exists(USER_REFERENCE)
    kernel = _read(KERNEL)
    routing = _read(ROUTING)
    assert "references/user-facing-output.md" not in kernel
    assert "references/user-facing-output.md" not in routing
    assert "user-facing prose turn -> references/always-on.md" in kernel


def test_description_guidance_preserves_clear_natural_coordination():
    text = _read(os.path.join(SKILL_DIR, "references", "descriptions.md")).casefold()
    assert "closely related subjects" in text
    assert "repeat full subjects mechanically" in text
