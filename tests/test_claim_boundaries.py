"""Frozen, context-aware gate for STOW's public instrumentality claims.

The ledger maps bounded claim statements to G1-G4. It is the authority for
claim semantics; the test does not ban words such as ``deterministic`` or
``validator`` in isolation because those words are truthful in bounded uses.
Protected corpus and baseline wording are deliberately outside the scan.
"""

import json
import os
import re


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


def _prose_sentences(text):
    """Yield normalized prose sentences, excluding fenced/code-span payloads."""
    visible = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible.append(line)
    prose = re.sub(r"`[^`\n]*`", "", "\n".join(visible))
    prose = re.sub(r"<!--.*?-->", "", prose, flags=re.S)
    for sentence in re.split(r"(?<=[.!?])\s+", _normalized(prose)):
        if sentence:
            yield sentence


def test_ledger_shape_and_surfaces_are_closed():
    data = _ledger()
    assert data["schema_version"] == 1
    guarded = data["guarded_surfaces"]
    assert guarded == sorted(set(guarded)), "guarded surfaces must be sorted and unique"
    assert set(data["coverage_surfaces"]) <= set(guarded)
    assert not any(path.startswith("skills/stow/corpus/") for path in guarded)
    assert not any(path == "skills/stow/rules/registry.yaml" for path in guarded)
    for relpath in guarded:
        assert os.path.isfile(os.path.join(REPO, relpath)), relpath


def test_every_claim_is_unique_present_and_classified():
    claims = _ledger()["claims"]
    assert len({claim["id"] for claim in claims}) == len(claims)
    assert len({(claim["surface"], claim["statement"]) for claim in claims}) == len(claims)
    for claim in claims:
        assert claim["layer"] in ALLOWED_LAYERS, claim
        assert claim["families"] and set(claim["families"]) <= ALLOWED_FAMILIES, claim
        assert claim["surface"] in _ledger()["guarded_surfaces"], claim
        count = _normalized(_read(claim["surface"])).count(
            _normalized(claim["statement"]))
        assert count == 1, "%s statement occurs %d times" % (claim["id"], count)


def test_coverage_surface_claims_fail_closed_when_unmapped():
    data = _ledger()
    family_re = re.compile(
        r"\b(?:guarantee\w*|ensure\w*|enforc\w*|must|always|automatic\w*|"
        r"validat\w*|preserv\w*|restor\w*|determin\w*)\b|delivery gate",
        re.I,
    )
    claims_by_surface = {}
    for claim in data["claims"]:
        claims_by_surface.setdefault(claim["surface"], []).append(
            _normalized(claim["statement"]))
    for surface in data["coverage_surfaces"]:
        mapped = claims_by_surface.get(surface, [])
        for sentence in _prose_sentences(_read(surface)):
            if family_re.search(sentence):
                assert any(statement in sentence for statement in mapped), (
                    "unmapped claim on %s: %s" % (surface, sentence))


def test_risk_shaped_claims_on_guarded_markdown_are_mapped():
    """Semantic risk shapes require an exact ledger entry, not a word ban."""
    data = _ledger()
    patterns = [re.compile(pattern, re.I)
                for pattern in data["claim_candidate_patterns"]]
    mapped = {}
    for claim in data["claims"]:
        mapped.setdefault(claim["surface"], []).append(
            _normalized(claim["statement"]))
    for surface in data["guarded_surfaces"]:
        if not surface.endswith(".md"):
            continue
        for sentence in _prose_sentences(_read(surface)):
            if any(pattern.search(sentence) for pattern in patterns):
                assert any(statement in sentence
                           for statement in mapped.get(surface, [])), (
                    "unmapped risk-shaped claim on %s: %s" % (surface, sentence))


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
