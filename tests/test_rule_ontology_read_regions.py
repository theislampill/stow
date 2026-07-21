import os
from ruamel.yaml import YAML
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
ONT = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")
def _load(p):
    y = YAML(typ="safe")
    with open(p, encoding="utf-8") as fh: return y.load(fh)

# Expected read_regions per ONTOLOGY-DESIGN.md section 3. SAF-002 = [prose] (prose-form,
# excludes structured-data per the explicit "NOT uniformly widened" directive).
READ_REGIONS = {
  "STOW-SAF-001": ["prose", "code", "structured-data"],
  "STOW-SAF-002": ["prose"],
  "STOW-SAF-003": ["prose", "code", "structured-data"],
  "STOW-PCT-005": ["prose", "identifiers"],
  "STOW-PCT-006": ["prose", "quoted-text", "identifiers", "titles", "placards", "labels", "proper-nouns"],
  "STOW-EVD-001": ["prose", "code", "structured-data", "tool-result"],
  "STOW-EVD-002": ["prose", "code", "structured-data"],
  "STOW-EVD-003": ["prose", "code", "structured-data"],
  "STOW-EVD-004": ["prose", "code", "structured-data"],
  "STOW-ART-001": ["prose", "code", "structured-data", "config"],
  "STOW-AUT-001": ["prose", "code", "structured-data", "quoted-text", "tool-result", "log"],
  "STOW-AUT-002": ["prose", "structured-data"],
  "STOW-AUT-003": ["prose", "structured-data"],
  "STOW-PRO-002": ["prose", "code", "structured-data"],
  "STOW-PRO-017": ["prose", "code", "structured-data"],
  "STOW-PRO-018": ["prose", "code", "structured-data"],
  "STOW-PRO-019": ["prose", "code", "structured-data"],
  "STOW-PRO-023": ["prose", "quoted-text"],
  "STOW-PRO-024": ["prose", "structured-data"],
}

def test_read_regions_content_matches_design():
    ont = _load(ONT)["rules"]
    assert set(READ_REGIONS) == {rid for rid, v in ont.items() if "read_regions" in v}
    for rid, expected in READ_REGIONS.items():
        assert list(ont[rid]["read_regions"]) == list(expected), rid
