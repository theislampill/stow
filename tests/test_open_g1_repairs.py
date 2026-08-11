"""Contracts for the evidence-led repair of the remaining G1 surface."""

from pathlib import Path

from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "skills" / "stow" / "rules" / "registry.yaml"
CONTROLLED_REFERENCE = ROOT / "skills" / "stow" / "references" / "controlled-technical-writing.md"
CONFORMANCE_REFERENCE = ROOT / "skills" / "stow" / "references" / "conformance.md"
PROCEDURE_REFERENCE = ROOT / "skills" / "stow" / "references" / "procedures.md"


def _records():
    yaml = YAML(typ="safe")
    with REGISTRY_PATH.open(encoding="utf-8") as stream:
        return {record["id"]: record for record in yaml.load(stream)["records"]}


def test_simplified_rules_state_the_contextual_invariant_and_exception():
    records = _records()
    expected = {
        "STOW-GEN-002": (
            "Rewrite a with phrase only when it has two plausible attachments.",
            "a with phrase has two plausible attachments",
            "leave a clear with phrase unchanged",
        ),
        "STOW-GEN-007": (
            "When gender is unknown or irrelevant, name the role or use an inclusive reference.",
            "a human role is named and gender is unknown or irrelevant",
            "preserve gender when it is a supplied fact or materially relevant",
        ),
        "STOW-PRC-005": (
            "A note in a controlled procedure gives information and does not introduce an action.",
            "a note is attached to a controlled procedure",
            "a higher-precedence literal or output contract takes priority",
        ),
        "STOW-PRO-007": (
            "Avoid mechanical repetition that obscures function.",
            "consecutive repeated structures obscure the function of the content",
            "preserve deliberate parallelism, recurring terminology, house style, and required layouts",
        ),
        "STOW-PRO-009": (
            "Use urgency or intensified emphasis only when a decision-relevant reason is stated.",
            "urgency or intensified emphasis lacks a decision-relevant reason",
            "preserve a supported deadline-led command or requested functional emphasis",
        ),
        "STOW-PRO-011": (
            "Remove framing or process language only when it adds no information or decision value.",
            "framing or process language adds no information or decision value",
            "preserve a material limitation, method, audience, progress state, or requested voice",
        ),
    }
    for rule_id, (title, applicability, exception) in expected.items():
        record = records[rule_id]
        assert record["title"] == title
        assert record["activation"]["applicability"] == applicability
        assert record["activation"]["exception"] == exception


def test_context_dependent_controlled_rules_are_not_described_as_parsers_or_deterministic():
    text = CONTROLLED_REFERENCE.read_text(encoding="utf-8")
    expected = {
        "VRB-005": "contextual guidance",
        "GEN-002": "contextual guidance",
        "GEN-005": "external meaning authority",
        "GEN-007": "contextual guidance",
    }
    for short_id, mechanism in expected.items():
        row = next(line for line in text.splitlines() if line.startswith(f"| {short_id} |"))
        assert mechanism in row
        assert "deterministic ·" not in row
        assert "parser ·" not in row


def test_dictionary_meaning_and_technical_term_boundaries_are_explicit_and_cold():
    records = _records()
    assert records["STOW-WRD-001"]["activation"]["applicability"] == (
        "controlled vocabulary is requested and dictionary or project terminology authority is available"
    )
    assert records["STOW-WRD-001"]["activation"]["exception"] == (
        "unknown technical terms require external authority and are not rejected by lexical lookup alone"
    )
    assert records["STOW-WRD-003"]["activation"]["applicability"] == (
        "an approved meaning is supplied for contextual review"
    )
    assert records["STOW-WRD-003"]["activation"]["exception"] == (
        "lexical membership and listed alternatives do not establish the intended sense or an equivalent action"
    )
    controlled = CONTROLLED_REFERENCE.read_text(encoding="utf-8")
    assert "A listed alternative is evidence to review, not replacement authorization" in controlled
    assert "preserve the source term and mark the item unresolved" in controlled
    text = " ".join(CONFORMANCE_REFERENCE.read_text(encoding="utf-8").split())
    assert "external terminology authority" in text
    assert "contextual sense review is intentionally deferred" in text


def test_false_friend_guidance_requires_supplied_cross_language_meaning():
    record = _records()["STOW-GEN-005"]
    assert record["activation"]["applicability"] == (
        "a source-language form or intended English meaning is supplied for controlled review"
    )
    assert record["activation"]["exception"] == (
        "do not infer a false friend from spelling resemblance alone"
    )


def test_moved_controlled_rules_have_narrow_contextual_boundaries():
    records = _records()
    expected = {
        "STOW-PCT-003": (
            "parentheses appear in controlled prose",
            "protected text and the listed parenthetical purposes remain unchanged",
        ),
        "STOW-VRB-002": (
            "controlled prose requires a bounded tense or aspect choice",
            "preserve a time relation when the source or procedure requires it",
        ),
        "STOW-VRB-005": (
            "a word ending in ing appears outside a declared technical noun",
            "project authority can classify the form as a noun term or noun modifier",
        ),
    }
    for rule_id, (applicability, exception) in expected.items():
        activation = records[rule_id]["activation"]
        assert activation["applicability"] == applicability
        assert activation["exception"] == exception


def test_vrb_005_is_not_claimed_as_a_parser_after_the_failed_behavioural_probe():
    record = _records()["STOW-VRB-005"]
    assert record["enforcement"] == {
        "kind": "semantic-review",
        "validator": "ing-role-contextual-review",
        "limit": None,
        "autofix": False,
        "status": "review-fallback",
    }
    row = next(
        line for line in CONTROLLED_REFERENCE.read_text(encoding="utf-8").splitlines()
        if line.startswith("| VRB-005 |")
    )
    assert "no reliable parser is claimed" in row


def test_imperative_guidance_does_not_silently_strength_source_modality():
    record = _records()["STOW-PRC-003"]
    activation = record["activation"]
    assert "source already authorizes a command" in activation["applicability"]
    assert "do not silently strengthen" in activation["exception"]
    procedures = PROCEDURE_REFERENCE.read_text(encoding="utf-8")
    assert "preserve the source force" in procedures
    assert "Dictionary status never authorizes changing source force" in procedures


def test_dictionary_repair_cannot_change_a_named_safety_operation():
    safety = (ROOT / "skills" / "stow" / "references" / "safety-instructions.md").read_text(encoding="utf-8")
    canonical = " ".join((ROOT / "skills" / "stow" / "references" / "canonical-terms.md").read_text(encoding="utf-8").split())
    assert "does not authorize changing the named operation" in safety
    assert "do not substitute it solely because lookup reports an alternative" in canonical


def test_note_function_and_sentence_cap_have_distinct_owners():
    text = PROCEDURE_REFERENCE.read_text(encoding="utf-8")
    note_section = text.split("### STOW-PRC-005", 1)[1].split("## Punctuation", 1)[0]
    assert "contextual" in note_section
    assert "does not introduce an action" in note_section
    assert "STOW-DSC-003" in note_section
    assert "25-word cap" in note_section
