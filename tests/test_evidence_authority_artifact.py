"""Regression guard for the additive evidence / authority / artifact-state
extension (EVD, AUT, ART). Proves each new primary rule is reachable through
the registry and the corpus, carries a conforming and a non-conforming example
(the RED/GREEN fixture pair), is honestly review-fallback, never joins the
always-on hot path, and that its composition conflict record and deep-guidance
reference are wired.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import os

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.join(REPO, "skills", "stow")
REGISTRY = os.path.join(SKILL, "rules", "registry.yaml")
CONFLICTS = os.path.join(SKILL, "rules", "conflicts.yaml")
ROUTING = os.path.join(SKILL, "rules", "routing.yaml")
KERNEL = os.path.join(SKILL, "SKILL.md")
REFERENCE = os.path.join(SKILL, "references", "evidence-and-authority.md")

NEW_IDS = [
    "STOW-EVD-001", "STOW-EVD-002", "STOW-EVD-003", "STOW-EVD-004",
    "STOW-AUT-001", "STOW-AUT-002", "STOW-AUT-003",
    "STOW-ART-001",
]
BAND = {
    "EVD": "accuracy", "AUT": "accuracy", "ART": "contract",
}
CATEGORY = {
    "EVD": "evidence", "AUT": "authority", "ART": "artifact-state",
}


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return YAML(typ="safe").load(fh)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


REGISTRY_DATA = _load(REGISTRY)
RECORDS = {r["id"]: r for r in REGISTRY_DATA["records"]}
CONFLICT_DATA = _load(CONFLICTS)


def _prefix(rid):
    return rid.split("-")[1]


def test_all_eight_new_records_present():
    for rid in NEW_IDS:
        assert rid in RECORDS, "missing new record %s" % rid
    assert REGISTRY_DATA["generated_counts"]["primary_total"] == 104


def test_new_records_are_authored_and_hashed():
    import hashlib
    for rid in NEW_IDS:
        w = RECORDS[rid]["wording"]
        assert w["baseline_kind"] == "authored", rid
        assert w["active_version"] == "authored-baseline", rid
        assert w["candidates"] == [], rid
        assert w["rewrite_status"] == "deferred", rid
        got = hashlib.sha256(w["baseline_text"].encode("utf-8")).hexdigest()
        assert got == w["baseline_text_sha256"], rid


def test_new_records_band_category_and_enforcement():
    for rid in NEW_IDS:
        rec = RECORDS[rid]
        pfx = _prefix(rid)
        assert rec["category"] == CATEGORY[pfx], rid
        assert rec["precedence"] == BAND[pfx], rid
        enf = rec["enforcement"]
        assert enf["kind"] == "semantic-review", rid
        assert enf["status"] == "review-fallback", rid
        assert enf["validator"] is None, rid


def test_new_records_are_conditional_and_off_the_hot_path():
    for rid in NEW_IDS:
        act = RECORDS[rid]["activation"]
        assert act["kind"] == "conditional", rid
        assert act["always_on_for_prose"] is False, rid
        assert act["predicate"].strip(), rid
        assert act.get("applicability"), rid
        assert act.get("exception"), rid


def test_new_records_have_no_registry_conflict_edges():
    # New-to-existing conflicts live only as composition CFL entries, so every
    # new record keeps conflicts: [] and needs no reciprocal edge on a frozen rule.
    for rid in NEW_IDS:
        assert RECORDS[rid]["conflicts"] == [], rid


def test_each_new_rule_reaches_its_corpus_with_a_red_green_pair():
    for rid in NEW_IDS:
        ref = RECORDS[rid]["corpus_ref"]
        module = os.path.join(SKILL, ref.split("#", 1)[0].replace("/", os.sep))
        assert os.path.isfile(module), "%s -> missing %s" % (rid, ref)
        text = _read(module)
        # anchor present exactly once
        assert text.count("## " + rid) == 1, rid
        # baseline byte-present
        assert RECORDS[rid]["wording"]["baseline_text"] in text, rid
        # the anchored section carries both a conforming and a non-conforming line
        section = text.split("## " + rid, 1)[1].split("\n## ", 1)[0]
        assert "**Conforming:**" in section, "%s lacks a GREEN example" % rid
        assert "**Non-conforming:**" in section, "%s lacks a RED example" % rid


def test_aut004_precedence_recorded_as_composition_conflict():
    entries = {e["id"]: e for e in CONFLICT_DATA["conflicts"]}
    assert "CFL-021" in entries, "AUT-004 precedence record missing"
    cfl = entries["CFL-021"]
    assert cfl["origin"] == "composition"
    assert "registry_resolution" not in cfl
    refs = {p["ref"] for p in cfl["participants"]}
    assert "STOW-AUT-001" in refs
    assert cfl["winner"]["band"] == "contract"


def test_deep_reference_exists_and_is_routed():
    assert os.path.isfile(REFERENCE)
    kernel = _read(KERNEL)
    assert "references/evidence-and-authority.md" in kernel, \
        "kernel activation map does not route the new reference"
    routes = _load(ROUTING)["routes"]
    targets = [ref for r in routes for ref in r["references"]]
    assert "references/evidence-and-authority.md" in targets, \
        "routing.yaml does not carry the new reference route"
