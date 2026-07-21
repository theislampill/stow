import os
from ruamel.yaml import YAML
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REG = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
ONT = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")

def _load(p):
    y = YAML(typ="safe")
    with open(p, encoding="utf-8") as fh:
        return y.load(fh)

REG_IDS = [r["id"] for r in _load(REG)["records"]]
PLANES = {"output","measurement","safety","evidence","authority","artifact-operation"}
PLANE_COUNTS = {"output":79,"measurement":7,"safety":3,"evidence":13,"authority":1,"artifact-operation":1}
NINETEEN = {
 "STOW-SAF-001","STOW-SAF-002","STOW-SAF-003","STOW-PCT-005","STOW-PCT-006",
 "STOW-EVD-001","STOW-EVD-002","STOW-EVD-003","STOW-EVD-004","STOW-ART-001",
 "STOW-AUT-001","STOW-AUT-002","STOW-AUT-003","STOW-PRO-002","STOW-PRO-017",
 "STOW-PRO-018","STOW-PRO-019","STOW-PRO-023","STOW-PRO-024"}

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
