#!/usr/bin/env python3
"""Generate the README domain/family navigation view from the ontology sidecar.

One marked region in README.md is owned by this generator:

  <!-- ONTOLOGY-NAV:BEGIN --> ... <!-- ONTOLOGY-NAV:END -->

Everything between the markers is replaced wholesale; everything outside is
authored prose, exactly like ``gen_readme_catalog.py``'s marked regions. The
source is the cold ontology sidecar (``skills/stow/rules/rule-ontology.yaml``),
a read-only overlay over the frozen registry: this generator never writes
``registry.yaml`` and only reads its ``id`` and ``title`` fields to label each
row. Deterministic (domain, family, and rule id are each sorted), so
``--check`` proves the committed README matches the sidecar.

The view prints no per-domain or per-family counts and no numeric rule
counts anywhere: it is a navigation aid, not a census, matching how
``gen_readme_catalog.py`` deliberately prints no counts either.
"""

import io
import os
import sys

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
ONTOLOGY = os.path.join(REPO, "skills", "stow", "rules", "rule-ontology.yaml")
README = os.path.join(REPO, "README.md")

# Connector words that stay lowercase in a title-cased domain/family label,
# except when they open the label.
_CONNECTORS = frozenset({"and", "of", "the", "in", "for", "to", "on"})


def _label(slug):
    """Turn a hyphenated slug into a readable heading, e.g.
    ``evidence-and-integrity`` -> ``Evidence and Integrity``."""
    words = slug.split("-")
    out = []
    for index, word in enumerate(words):
        if index > 0 and word in _CONNECTORS:
            out.append(word)
        else:
            out.append(word.capitalize())
    return " ".join(out)


def _rule_meta():
    yaml = YAML(typ="safe")
    with open(ONTOLOGY, encoding="utf-8") as fh:
        data = yaml.load(fh)
    return data["rules"]


def _titles():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        records = yaml.load(fh)["records"]
    return {r["id"]: r["title"].strip().rstrip(".") for r in records}


def _grouped():
    """domain -> family -> [rule ids], built from the sidecar only."""
    by_domain = {}
    for rule_id, fields in _rule_meta().items():
        domain = fields["domain"]
        family = fields["family"]
        by_domain.setdefault(domain, {}).setdefault(family, []).append(rule_id)
    return by_domain


def build_nav():
    by_domain = _grouped()
    titles = _titles()
    parts = [""]
    for domain in sorted(by_domain):
        parts.append("<details>")
        parts.append("<summary><b>%s</b></summary>" % _label(domain))
        parts.append("")
        families = by_domain[domain]
        for family in sorted(families):
            parts.append("**%s**" % _label(family))
            parts.append("")
            parts.append("| Rule | Title |")
            parts.append("|---|---|")
            for rule_id in sorted(families[family]):
                parts.append("| `%s` | %s |" % (rule_id, titles[rule_id]))
            parts.append("")
        parts.append("</details>")
        parts.append("")
    return "\n".join(parts)


def _splice(text, begin, end, body):
    b = text.index(begin) + len(begin)
    e = text.index(end)
    return text[:b] + "\n" + body + text[e:]


def render(text):
    return _splice(text, "<!-- ONTOLOGY-NAV:BEGIN -->", "<!-- ONTOLOGY-NAV:END -->",
                   build_nav())


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    with io.open(README, encoding="utf-8", newline="") as fh:
        current = fh.read()
    rendered = render(current)
    if "--check" in argv:
        if current != rendered:
            print("README ontology navigation is STALE relative to the sidecar -- regenerate")
            return 1
        print("README ontology navigation is current")
        return 0
    with io.open(README, "w", encoding="utf-8", newline="") as fh:
        fh.write(rendered)
    print("wrote the README domain/family navigation view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
