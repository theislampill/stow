import os
import sys
from ruamel.yaml import YAML
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REG = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
ONT = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")

sys.path.insert(0, HERE)
from test_rule_ontology_read_regions import READ_REGIONS  # single source of truth for the 19

def _load(p):
    y = YAML(typ="safe")
    with open(p, encoding="utf-8") as fh:
        return y.load(fh)

REG_IDS = [r["id"] for r in _load(REG)["records"]]
PLANES = {"output","measurement","safety","evidence","authority","artifact-operation"}
PLANE_COUNTS = {"output":79,"measurement":7,"safety":3,"evidence":13,"authority":1,"artifact-operation":1}
DOMAINS = {"terminology-and-grammar","prose-and-presentation","procedures-and-descriptions","safety","evidence-and-integrity","structured-artifacts-and-interchange","action-progress-state","contract-and-authority"}
REL_TYPES = {"related-to","see-also","specializes","overlaps","cross-references","tag","parent-of","exception-to","measurement-for"}
NINETEEN = set(READ_REGIONS)

def test_every_registry_id_has_one_ontology_entry():
    ont = _load(ONT)["rules"]
    assert sorted(ont.keys()) == sorted(REG_IDS)

def test_plane_values_and_counts():
    from collections import Counter
    ont = _load(ONT)["rules"]
    got = Counter(v["plane"] for v in ont.values())
    assert set(got) <= PLANES
    assert dict(got) == PLANE_COUNTS

def test_read_regions_only_on_the_nineteen():
    ont = _load(ONT)["rules"]
    have = {rid for rid, v in ont.items() if "read_regions" in v}
    assert have == NINETEEN

def test_every_rule_has_domain_and_family():
    ont = _load(ONT)["rules"]
    for rid, v in ont.items():
        assert v.get("domain"), rid
        assert v.get("family"), rid

def test_relations_reference_valid_ids_and_never_self():
    data = _load(ONT)
    ids = set(data["rules"])
    for e in data["relations"]:
        assert e["a"] in ids and e["b"] in ids
        assert e["a"] != e["b"]

def test_domains_from_enum():
    ont = _load(ONT)["rules"]
    assert {v["domain"] for v in ont.values()} <= DOMAINS

def test_relation_types_from_enum():
    data = _load(ONT)
    assert {e["type"] for e in data["relations"]} <= REL_TYPES
