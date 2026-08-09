"""Frozen, context-aware gate for STOW's public instrumentality claims.

The ledger maps bounded claim statements to G1-G4. It is the authority for
claim semantics; the test does not ban words such as ``deterministic`` or
``validator`` in isolation because those words are truthful in bounded uses.
Protected corpus and baseline wording are deliberately outside the scan.
"""

import ast
import json
import os
import re

import pytest


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LEDGER_PATH = os.path.join(REPO, "docs", "claim-ledger.json")
ALLOWED_FAMILIES = {
    "guarantee", "selection", "validation", "preservation", "determinism",
}
ALLOWED_LAYERS = {"G1", "G2", "G3", "G4"}


def _read(relpath):
    with open(os.path.join(REPO, relpath), encoding="utf-8") as handle:
        return handle.read()


def _ledger():
    with open(LEDGER_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _normalized(text):
    return " ".join(text.split())


def _sentences(text):
    for sentence in re.split(r"(?<=[.!?])\s+", _normalized(text)):
        sentence = sentence.strip()
        if sentence:
            yield sentence


def _markdown_prose(text):
    """Return visible Markdown prose and reject an unterminated fence."""
    visible = []
    fence = None
    for line in text.splitlines():
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence is None and marker:
            token = marker.group(1)
            fence = (token[0], len(token))
            continue
        if fence is not None:
            char, width = fence
            if re.fullmatch(re.escape(char) + "{%d,}" % width, stripped):
                fence = None
            continue
        if fence is None:
            visible.append(line)
    if fence is not None:
        raise ValueError("unmatched Markdown fence")
    return re.sub(r"<!--.*?-->", "", "\n".join(visible), flags=re.S)


def _prose_sentences(text):
    """Yield normalized visible Markdown sentences."""
    for block in re.split(r"\n\s*\n", _markdown_prose(text)):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if any(line.lstrip().startswith("|") for line in lines):
            for line in lines:
                if not re.fullmatch(r"\s*\|?(?:\s*:?-+:?\s*\|)+\s*", line):
                    yield _normalized(line)
            continue
        yield from _sentences("\n".join(lines))


def _json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _json_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _json_strings(item)


def _claim_units(surface, text):
    """Yield claim-bearing units from one guarded surface, or fail closed."""
    try:
        if surface.endswith(".md"):
            yield from _prose_sentences(text)
            return
        if surface.endswith(".json"):
            value = json.loads(text)
            for string in _json_strings(value):
                yield from _sentences(string)
            return
        if surface.endswith(".py"):
            tree = ast.parse(text, filename=surface)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    yield from _sentences(node.value)
            return
    except (json.JSONDecodeError, SyntaxError) as error:
        raise ValueError("cannot parse guarded claim surface %s" % surface) from error
    raise ValueError("unsupported guarded claim surface %s" % surface)


def _candidate_families(unit, patterns_by_family):
    return {
        family
        for family, patterns in patterns_by_family.items()
        if any(re.search(pattern, unit, re.I) for pattern in patterns)
    }


def _unmapped_claims(surface, text, data):
    claims = [claim for claim in data["claims"] if claim["surface"] == surface]
    findings = []
    for unit in _claim_units(surface, text):
        normalized_unit = _normalized(unit)
        matches = [
            claim for claim in claims
            if _normalized(claim["statement"]) in normalized_unit
        ]
        mapped_families = {
            family for claim in matches for family in claim["families"]
        }
        families = _candidate_families(
            normalized_unit, data["claim_candidate_patterns"])
        residual = normalized_unit
        for claim in matches:
            residual = residual.replace(_normalized(claim["statement"]), " ")
        residual_families = _candidate_families(
            residual, data["claim_candidate_patterns"])
        if not families and not residual_families:
            continue
        missing = (families - mapped_families) | residual_families
        if missing:
            findings.append({"text": unit, "families": sorted(missing)})
    return findings


def _missing_claims(surface, text, claims):
    units = [_normalized(unit) for unit in _claim_units(surface, text)]
    return [
        claim
        for claim in claims
        if claim["surface"] == surface
        and sum(unit.count(_normalized(claim["statement"])) for unit in units) != 1
    ]


def test_ledger_shape_and_surfaces_are_closed():
    data = _ledger()
    assert data["schema_version"] == 1
    guarded = data["guarded_surfaces"]
    assert guarded == sorted(set(guarded)), "guarded surfaces must be sorted and unique"
    assert data["coverage_surfaces"] == guarded
    assert set(data["claim_candidate_patterns"]) == ALLOWED_FAMILIES
    assert all(data["claim_candidate_patterns"][family]
               for family in ALLOWED_FAMILIES)
    assert not any(path.startswith("skills/stow/corpus/") for path in guarded)
    assert not any(path == "skills/stow/rules/registry.yaml" for path in guarded)
    for relpath in guarded:
        assert os.path.isfile(os.path.join(REPO, relpath)), relpath


def test_every_claim_is_unique_present_and_classified():
    data = _ledger()
    claims = data["claims"]
    assert len({claim["id"] for claim in claims}) == len(claims)
    assert len({(claim["surface"], claim["statement"]) for claim in claims}) == len(claims)
    for claim in claims:
        assert claim["layer"] in ALLOWED_LAYERS, claim
        assert claim["families"] and set(claim["families"]) <= ALLOWED_FAMILIES, claim
        assert claim["surface"] in data["guarded_surfaces"], claim
    for surface in data["guarded_surfaces"]:
        missing = _missing_claims(surface, _read(surface), claims)
        assert not missing, "missing or duplicated mapped claims on %s: %s" % (
            surface, [claim["id"] for claim in missing])


def test_risk_shaped_claims_on_every_guarded_surface_are_mapped():
    """Semantic risk shapes require an exact ledger entry, not a word ban."""
    data = _ledger()
    for surface in data["guarded_surfaces"]:
        findings = _unmapped_claims(surface, _read(surface), data)
        assert not findings, "unmapped claims on %s: %s" % (surface, findings)


def test_known_overclaim_semantics_do_not_return():
    data = _ledger()
    combined = "\n".join(_read(path) for path in data["guarded_surfaces"])
    for item in data["forbidden_claim_patterns"]:
        assert not re.search(item["pattern"], combined, re.I), item["id"]


def test_g3_claim_names_all_custody_conditions_and_repository_absence():
    claims = {claim["id"]: claim["statement"] for claim in _ledger()["claims"]}
    g3 = claims["CLM-003"].lower()
    for phrase in ("named host", "actual final candidate", "blocks failure and unknown",
                   "repairs only where permitted", "revalidates before delivery"):
        assert phrase in g3
    assert "no general g3 host integration" in claims["CLM-005"].lower()


@pytest.mark.parametrize(
    ("family", "sentence"),
    [
        ("guarantee", "STOW ensures every final response is correct."),
        ("guarantee", "STOW enforces all prose rules."),
        ("selection", "STOW must always load every reference automatically."),
        ("validation", "validate.py is the delivery gate for every response."),
        ("preservation", "STOW restores every protected literal byte-for-byte."),
        ("determinism", "STOW deterministically classifies every response."),
    ],
)
def test_each_semantic_family_fails_closed_when_unmapped(family, sentence):
    findings = _unmapped_claims("README.md", sentence, _ledger())
    assert findings
    assert family in findings[0]["families"]


@pytest.mark.parametrize(
    ("surface", "text"),
    [
        ("README.md", "STOW ensures every final response is correct."),
        (
            ".claude-plugin/plugin.json",
            '{"items": [{"description": "Writing guidance that guarantees every response complies."}]}',
        ),
        (
            "skills/stow/runtime/profiles.py",
            '"""STOW ensures every final response is correct."""\n',
        ),
        (
            "skills/stow/runtime/profiles.py",
            'CLAIM = "STOW enforces all prose rules."\n',
        ),
    ],
)
def test_claim_extraction_fails_closed_on_every_guarded_surface_type(surface, text):
    assert _unmapped_claims(surface, text, _ledger())


def test_an_exact_family_compatible_mapping_closes_a_candidate():
    statement = "STOW ensures every final response is correct."
    data = dict(_ledger())
    data["claims"] = list(data["claims"]) + [
        {
            "id": "TEST-CLAIM",
            "surface": "README.md",
            "statement": statement,
            "families": ["guarantee"],
            "layer": "G1",
        }
    ]
    assert _unmapped_claims("README.md", statement, data) == []


def test_an_unmapped_insertion_next_to_a_mapped_claim_still_fails_closed():
    statement = "STOW ensures every final response is correct."
    data = dict(_ledger())
    data["claims"] = list(data["claims"]) + [
        {
            "id": "TEST-CLAIM",
            "surface": "README.md",
            "statement": statement,
            "families": ["guarantee"],
            "layer": "G1",
        }
    ]
    text = statement + " STOW also enforces all prose rules."
    findings = _unmapped_claims("README.md", text, data)
    assert findings and findings[-1]["families"] == ["guarantee"]


def test_a_mapping_in_the_wrong_semantic_family_does_not_close_a_candidate():
    statement = "STOW ensures every final response is correct."
    data = dict(_ledger())
    data["claims"] = list(data["claims"]) + [
        {
            "id": "TEST-CLAIM",
            "surface": "README.md",
            "statement": statement,
            "families": ["selection"],
            "layer": "G1",
        }
    ]
    findings = _unmapped_claims("README.md", statement, data)
    assert findings and "guarantee" in findings[0]["families"]


def test_a_mapped_claim_disappearing_from_its_surface_fails_closed():
    claims = [
        {
            "id": "TEST-CLAIM",
            "surface": "README.md",
            "statement": "STOW ensures every final response is correct.",
            "families": ["guarantee"],
            "layer": "G1",
        }
    ]
    assert _missing_claims("README.md", "A different sentence.", claims) == claims


@pytest.mark.parametrize(
    "text",
    [
        "Visible prose.\n```text\nSTOW ensures every final response is correct.\n",
        "Visible prose.\n~~~~text\nSTOW ensures every final response is correct.\n",
    ],
)
def test_unmatched_markdown_fence_fails_closed(text):
    with pytest.raises(ValueError, match="unmatched Markdown fence"):
        list(_claim_units("README.md", text))


@pytest.mark.parametrize(
    ("surface", "text"),
    [
        (".claude-plugin/plugin.json", '{"description": '),
        ("skills/stow/runtime/profiles.py", '"""unterminated\n'),
    ],
)
def test_unparseable_guarded_structured_surface_fails_closed(surface, text):
    with pytest.raises(ValueError):
        list(_claim_units(surface, text))


def test_residual_preservation_language_is_bounded_to_guidance_and_scan_exclusion():
    protected = _read("skills/stow/references/protected-regions.md")
    markdown = _read("skills/stow/references/format-markdown.md")
    readme = _read("README.md")
    combined = "\n".join((protected, markdown, readme))
    for overclaim in (
        "is masked so it is reproduced verbatim",
        "body is byte-stable",
        "literals band holds the bytes fixed",
        "quoted span stays byte-exact",
        "token passes through unchanged",
        "protected literal that passes through unchanged",
    ):
        assert overclaim not in combined
    assert "G1" in protected and "G2" in protected
    assert "named host" in protected


def test_format_references_do_not_claim_an_unnamed_delivery_gate():
    surfaces = {
        path: _read(path)
        for path in (
            "skills/stow/references/format-yaml.md",
            "skills/stow/references/format-json.md",
            "skills/stow/references/format-jsonl.md",
        )
    }
    combined = "\n".join(surfaces.values())
    for overclaim in (
        "Deliver only on exit 0.",
        "parser failure is an error and blocks delivery",
        "Composition and any validation happen privately",
        "STOW still ships only the artifact",
    ):
        assert overclaim not in combined
    for path, text in surfaces.items():
        assert "G2" in text, path
        assert "named host" in text, path
        assert "actual final candidate" in text, path


def test_self_dogfood_distinguishes_advisory_findings_from_repository_gating():
    dogfood = _read("docs/SELF-DOGFOOD.md")
    design = _read("docs/design.md")
    test_source = _read("tests/test_self_dogfood.py")
    assert "G2 advisory" in dogfood
    assert "G4 repository gate" in dogfood
    assert "G2 advisory" in test_source
    assert "G4 repository gate" in test_source
    assert "Nothing in this repository fails a build because prose violated a style rule." not in design


def test_conformance_version_label_is_not_stale():
    assert "v0.1" not in _read("skills/stow/references/conformance.md")


def test_historical_parse_metric_is_distinguished_from_current_exact_content_check():
    evidence = _read("docs/FUNCTIONAL-EVIDENCE.md")
    assert "historical" in evidence.lower()
    assert "then-current YAML parse predicate" in evidence
    assert "current exact-content predicate" in evidence
    assert "not used to recompute" in evidence
