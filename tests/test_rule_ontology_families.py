import os
from ruamel.yaml import YAML
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
ONT = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")
def _load(p):
    y = YAML(typ="safe")
    with open(p, encoding="utf-8") as fh: return y.load(fh)

# Authoritative 57-family map, one entry per line, grouped in the repo's canonical
# prefix order (WRD, MWN, VRB, SEN, PRC, DSC, SAF, PCT, STY, GEN, ACT, PRO, EVD,
# AUT, ART) -- matching EXPECTED_COUNTS in tests/test_registry.py.
FAMILY_MAP = {
 # WRD (14)
 "STOW-WRD-001": "approved-vocabulary",
 "STOW-WRD-002": "part-of-speech-discipline",
 "STOW-WRD-003": "word-sense-and-meaning",
 "STOW-WRD-004": "inflectional-forms",
 "STOW-WRD-005": "technical-term-admission",
 "STOW-WRD-006": "technical-term-admission",
 "STOW-WRD-007": "part-of-speech-discipline",
 "STOW-WRD-008": "technical-noun-formation",
 "STOW-WRD-009": "technical-noun-formation",
 "STOW-WRD-010": "technical-noun-formation",
 "STOW-WRD-011": "terminology-consistency",
 "STOW-WRD-012": "technical-term-admission",
 "STOW-WRD-013": "part-of-speech-discipline",
 "STOW-WRD-014": "spelling-and-orthography",
 # MWN (2)
 "STOW-MWN-001": "multi-word-noun-formation",
 "STOW-MWN-002": "multi-word-noun-formation",
 # VRB (7)
 "STOW-VRB-001": "verb-inflection-and-tense",
 "STOW-VRB-002": "verb-inflection-and-tense",
 "STOW-VRB-003": "nonfinite-verb-form-role",
 "STOW-VRB-004": "verb-inflection-and-tense",
 "STOW-VRB-005": "nonfinite-verb-form-role",
 "STOW-VRB-006": "grammatical-voice",
 "STOW-VRB-007": "action-expressed-as-verb",
 # SEN (5)
 "STOW-SEN-001": "sentence-clarity-and-length",
 "STOW-SEN-002": "explicit-complete-wording",
 "STOW-SEN-003": "vertical-list-formatting",
 "STOW-SEN-004": "sentence-cohesion-connectors",
 "STOW-SEN-005": "explicit-complete-wording",
 # PRC (5)
 "STOW-PRC-001": "sentence-length-limits",
 "STOW-PRC-002": "instruction-form-and-decomposition",
 "STOW-PRC-003": "instruction-form-and-decomposition",
 "STOW-PRC-004": "instruction-form-and-decomposition",
 "STOW-PRC-005": "note-content-discipline",
 # DSC (6)
 "STOW-DSC-001": "information-sequencing",
 "STOW-DSC-002": "information-sequencing",
 "STOW-DSC-003": "sentence-length-limits",
 "STOW-DSC-004": "paragraph-structure",
 "STOW-DSC-005": "paragraph-structure",
 "STOW-DSC-006": "paragraph-structure",
 # SAF (3)
 "STOW-SAF-001": "safety-instruction-anatomy",
 "STOW-SAF-002": "safety-instruction-anatomy",
 "STOW-SAF-003": "safety-instruction-anatomy",
 # PCT (7)
 "STOW-PCT-001": "punctuation-mechanics",
 "STOW-PCT-002": "punctuation-mechanics",
 "STOW-PCT-003": "punctuation-mechanics",
 "STOW-PCT-004": "sentence-length-measurement",
 "STOW-PCT-005": "sentence-length-measurement",
 "STOW-PCT-006": "sentence-length-measurement",
 "STOW-PCT-007": "sentence-length-measurement",
 # STY (4)
 "STOW-STY-001": "meaning-preserving-substitution",
 "STOW-STY-002": "approved-word-usage",
 "STOW-STY-003": "approved-word-usage",
 "STOW-STY-004": "terminology-consistency",
 # GEN (8)
 "STOW-GEN-001": "function-word-disambiguation",
 "STOW-GEN-002": "function-word-disambiguation",
 "STOW-GEN-003": "pronoun-reference",
 "STOW-GEN-004": "pronoun-reference",
 "STOW-GEN-005": "word-choice-clarity",
 "STOW-GEN-006": "word-choice-clarity",
 "STOW-GEN-007": "inclusive-language",
 "STOW-GEN-008": "possessive-form",
 # ACT (11)
 "STOW-ACT-001": "action-positioning",
 "STOW-ACT-002": "action-list-formatting",
 "STOW-ACT-003": "action-positioning",
 "STOW-ACT-004": "concision-and-focus",
 "STOW-ACT-005": "progress-and-status-reporting",
 "STOW-ACT-006": "effort-estimation",
 "STOW-ACT-007": "progress-and-status-reporting",
 "STOW-ACT-008": "progress-and-status-reporting",
 "STOW-ACT-009": "action-list-formatting",
 "STOW-ACT-010": "concision-and-focus",
 "STOW-ACT-011": "action-list-formatting",
 # PRO (24)
 "STOW-PRO-001": "punctuation-and-typography",
 "STOW-PRO-002": "sourcing-and-attribution",
 "STOW-PRO-003": "heading-style",
 "STOW-PRO-004": "banned-lexicon",
 "STOW-PRO-005": "grounding-and-specificity",
 "STOW-PRO-006": "concision-and-redundancy",
 "STOW-PRO-007": "structural-variation",
 "STOW-PRO-008": "self-reference-and-narration",
 "STOW-PRO-009": "register-and-tone",
 "STOW-PRO-010": "punctuation-and-typography",
 "STOW-PRO-011": "banned-lexicon",
 "STOW-PRO-012": "banned-lexicon",
 "STOW-PRO-013": "authorial-register",
 "STOW-PRO-014": "authorial-register",
 "STOW-PRO-015": "authorial-register",
 "STOW-PRO-016": "heading-formulation",
 "STOW-PRO-017": "non-fabrication",
 "STOW-PRO-018": "non-fabrication",
 "STOW-PRO-019": "non-fabrication",
 "STOW-PRO-020": "ai-stylistic-tells",
 "STOW-PRO-021": "ai-stylistic-tells",
 "STOW-PRO-022": "ai-stylistic-tells",
 "STOW-PRO-023": "quotation-fidelity",
 "STOW-PRO-024": "evidence-reporting-discipline",
 # EVD (4)
 "STOW-EVD-001": "verification-and-calibration",
 "STOW-EVD-002": "verification-and-calibration",
 "STOW-EVD-003": "verification-and-calibration",
 "STOW-EVD-004": "operation-reporting-integrity",
 # AUT (3)
 "STOW-AUT-001": "embedded-instruction-authority",
 "STOW-AUT-002": "statement-and-decision-provenance",
 "STOW-AUT-003": "statement-and-decision-provenance",
 # ART (1)
 "STOW-ART-001": "artifact-revision-safety",
}

def test_family_matches_authoritative_map():
    ont = _load(ONT)["rules"]
    assert len(FAMILY_MAP) == 104
    for rid, fam in FAMILY_MAP.items():
        assert ont[rid]["family"] == fam, f"{rid}: {ont[rid].get('family')} != {fam}"
