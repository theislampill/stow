"""Frozen, context-aware gate for STOW's public instrumentality claims.

The ledger maps bounded claim statements to G1-G4. It is the authority for
claim semantics; the test does not ban words such as ``deterministic`` or
``validator`` in isolation because those words are truthful in bounded uses.
Protected corpus and baseline wording are deliberately outside the scan.
"""

import ast
import io
import json
import os
import re
import tokenize

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


def _python_claim_strings(text, tree):
    """Yield Python prose intended for readers, excluding runtime data."""
    doc_nodes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, doc_nodes):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                yield docstring

    visible_names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg not in {"description", "epilog", "help"}:
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, str):
                yield keyword.value.value
            elif isinstance(keyword.value, ast.Name):
                visible_names.add(keyword.value.id)

    for node in ast.walk(tree):
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None or not any(
                isinstance(target, ast.Name) and target.id in visible_names
                for target in targets):
            continue
        try:
            visible_value = ast.literal_eval(value)
        except (ValueError, TypeError):
            continue
        if isinstance(visible_value, str):
            yield visible_value

    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            comment = token.string.lstrip("#").strip()
            if comment:
                yield comment


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
            for string in _python_claim_strings(text, tree):
                yield from _sentences(string)
            return
    except (json.JSONDecodeError, SyntaxError, tokenize.TokenError) as error:
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
    assert data["coverage_boundary"] == (
        "The deterministic claim audit covers only the surfaces enumerated in "
        "docs/claim-ledger.json; it does not establish whole-runtime or "
        "whole-guidance closure."
    )
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
    ("family", "sentence"),
    [
        ("preservation", "STOW keeps every protected literal byte-for-byte unchanged."),
        ("selection", "Every relevant reference loads by itself."),
        (
            "validation",
            "The checker rejects every invalid final response before it is sent.",
        ),
        ("guarantee", "STOW makes every response conform."),
        ("preservation", "Quoted text is never re-cased."),
        ("selection", "The relevant reference loads on its own."),
        ("validation", "The checker blocks the final response before delivery."),
        ("guarantee", "STOW makes every response comply."),
    ],
)
def test_semantic_equivalent_claims_fail_closed_when_unmapped(family, sentence):
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
            '# STOW ensures every final response is correct.\nVALUE = 1\n',
        ),
    ],
)
def test_claim_extraction_fails_closed_on_every_guarded_surface_type(surface, text):
    assert _unmapped_claims(surface, text, _ledger())


def test_python_user_visible_help_and_named_scope_strings_are_scanned():
    text = '''\
"""A bounded command."""
import argparse
SCOPE = "STOW makes every response conform."
parser = argparse.ArgumentParser(epilog=SCOPE)
parser.add_argument("--mode", help="STOW ensures every final response is correct.")
'''
    findings = _unmapped_claims("tools/ab_eval_runner.py", text, _ledger())
    assert len(findings) == 2
    assert all("guarantee" in finding["families"] for finding in findings)


def test_python_detector_and_fixture_data_literals_are_not_claim_units():
    text = '''\
OVERCLAIM = ("fully conformant", "guarantees compliance")
FIXTURE = "STOW ensures every final response is correct."
'''
    units = list(_claim_units("tools/ab_eval_runner.py", text))
    assert "guarantees compliance" not in units
    assert "STOW ensures every final response is correct." not in units
    assert _unmapped_claims("tools/ab_eval_runner.py", text, _ledger()) == []


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

    activation = _read("skills/stow/references/activation-and-precedence.md")
    yaml_format = _read("skills/stow/references/format-yaml.md")
    for overclaim in (
        "keys, identifiers, and quoted text are never re-spelled or re-cased",
        "keys, identifiers, and quoted literals are protected and immutable",
        "they are not scanned or rewritten",
    ):
        assert overclaim not in "\n".join((activation, yaml_format))
    for path, text in (
        ("activation-and-precedence.md", activation),
        ("format-yaml.md", yaml_format),
    ):
        assert "G1" in text, path
        assert "G2" in text, path
        assert "named host" in text, path
        assert "actual final candidate" in text, path


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


def test_markdown_reference_does_not_overclaim_current_word_count_semantics():
    markdown = _read("skills/stow/references/format-markdown.md")
    for overclaim in (
        "counts that placeholder as one token",
        "counts a recognized token as one word",
    ):
        assert overclaim not in markdown
    assert "excluded or blanked by the current advisory scan" in markdown
    assert "exact one-token semantics" in markdown
    assert "not implemented by that scan" in markdown


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
    assert "historical 8 of 9 YAML result" not in evidence
    assert "historical raw-output result" in evidence
    assert "then-current YAML parse predicate" in evidence
    assert "current exact-content predicate" in evidence
    assert "not used to recompute" in evidence


def test_public_operationalisation_claim_preserves_benchmark_boundaries():
    readme = " ".join(_read("README.md").split()).lower()
    assert "turns a model-memory cue into an operational workflow" in readme
    assert "reconstruct and apply the named standard from latent knowledge" in readme
    assert "100% operational accounting is not 100% behavioral compliance" in readme
    assert "highest requirement-level result" in readme
    assert "name-only: 78 pass, six fail, two not_scored" in readme
    assert "stow: 80 pass, four fail, two not_scored" in readme
    assert "b fail / d pass" in readme
    assert "b partial / d pass" in readme
    assert "b pass / d fail" in readme
    assert "b pass / d pass" in readme
    for requirement_id in ("`6.4`", "`gr-2`", "`6.6`", "`5.3`"):
        assert requirement_id in readme
    assert "both name-only and stow passed the mapped dictionary" in readme
    assert "trial 2 was not rerun" in readme
    assert "name-only conditioning was cheaper" in readme
    assert "semantic overreach" in readme
    assert "repaired and regression-tested" in readme
    assert "not universal output superiority" in readme
    assert "cross-model durability remains unproved" in readme
    assert "stow >" not in readme


def test_readme_exposes_the_reconciled_runtime_architecture():
    readme = " ".join(_read("README.md").split()).lower()
    for statement in (
        "65 active canonical rules",
        "sixty-one g1 semantic owners",
        "four genuine g2 predicates",
        "16 are available in ordinary always-on prose guidance",
        "45 are cold or predicate-loaded",
        "ten advisory signals",
        "57 of the sixty-one g1 owners are behaviorally qualified",
        "one terminates at an external project-authority boundary",
        "two are explicit contextual deferrals",
        "strict profile remains locked",
    ):
        assert statement in readme


def test_readme_reports_normal_installed_skill_turn_economics_separately():
    readme = " ".join(_read("README.md").split()).lower()
    for statement in (
        "normal installed-skill runtime probe",
        "24619",
        "78,890",
        "3.2044",
        "24676",
        "142,567",
        "5.7776",
        "1.0651",
        "no post-fix case reached an order-of-magnitude ratio",
        "bounded result on one codex host",
        "logical / architectural cost",
        "cache behaviour",
        "economic cost: not_derived",
        "14,635",
        "18,218",
        "40.5540%",
        "76.9071%",
        "27,111",
        "80.9837%",
        "the measured d' package preceded the final candidate",
        "one shipped-file difference",
        "nine exact proxy tokens",
    ):
        assert statement in readme
