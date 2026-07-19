"""Leak gate for the STOW-authored operational qualifier fields.

activation.applicability and activation.exception are STOW-authored
compressions, like titles. They must carry the CLASS of a source condition
without importing its wording: the exact bounds and phrasing stay Tier-3
behind the corpus_ref. This gate makes that mechanical: no qualifier value
may contain a four-word verbatim run from any protected baseline_text, and
none may carry an all-caps acronym token or a bare partition numeral.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import os
import re

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")

NGRAM = 4


def _records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        return yaml.load(fh)["records"]


RECORDS = _records()


def _norm_words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def _windows(words, n):
    for i in range(len(words) - n + 1):
        yield " ".join(words[i:i + n])


def _qualifier_fields():
    out = []
    for record in RECORDS:
        activation = record.get("activation") or {}
        for field in ("applicability", "exception"):
            value = activation.get(field)
            if value:
                out.append((record["id"], field, value))
    return out


QUALIFIERS = _qualifier_fields()


def test_qualifier_fields_exist():
    assert QUALIFIERS, "no operational qualifiers found in the registry"


def test_no_qualifier_reproduces_a_baseline_fragment():
    baselines = " \n ".join(
        " ".join(_norm_words(r["wording"]["baseline_text"])) for r in RECORDS)
    for rule_id, field, value in QUALIFIERS:
        for window in _windows(_norm_words(value), NGRAM):
            assert window not in baselines, (
                "%s %s carries a %d-word verbatim baseline fragment: %r"
                % (rule_id, field, NGRAM, window))


def test_no_qualifier_carries_an_allcaps_acronym():
    """Uppercase source-vocabulary acronyms belong to the protected corpus,
    never to authored qualifier fields."""
    for rule_id, field, value in QUALIFIERS:
        assert not re.search(r"\b[A-Z]{2,}\b", value), (
            "%s %s carries an all-caps token" % (rule_id, field))


def test_no_qualifier_carries_a_bare_numeral():
    """Partition counts and numeric bounds stay in the corpus; the qualifier
    states the condition's class, not its number."""
    for rule_id, field, value in QUALIFIERS:
        assert not re.search(r"\d", value), (
            "%s %s carries a numeral" % (rule_id, field))


def test_qualifiers_are_compact():
    for rule_id, field, value in QUALIFIERS:
        assert len(value) <= 120, (
            "%s %s runs %d chars; qualifiers are one compact clause"
            % (rule_id, field, len(value)))
