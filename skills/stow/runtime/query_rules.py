#!/usr/bin/env python3
"""Look up one STOW rule by id (optional acceleration, never a contract path).

    python runtime/query_rules.py STOW-PCT-006

Prints the registry record's key fields, the profiles that include the rule
(through their guidance_rules or their selector), and the anchored corpus
section sliced from the rule's corpus module. Exit 2 with a clear message for an
unknown id.

Stdlib only. The registry is YAML, but this helper never imports a YAML library:
it locates the single record block by the id line and reads the few flat fields
it needs by hand. profiles.json is plain JSON. This tool is not shipped (it is
outside the runtime allowlist in tools/build_skill.py) and no kernel path reads
it; it only speeds up manual rule lookups.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)                       # .../skills/stow
REGISTRY = os.path.join(SKILL_DIR, "rules", "registry.yaml")
PROFILES = os.path.join(SKILL_DIR, "rules", "profiles.json")

ID_RE = re.compile(r"^  - id:\s*(\S+)\s*$")


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _record_block(text, rid):
    """The lines of the record whose ``id`` equals ``rid``, or None."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        match = ID_RE.match(line)
        if match and match.group(1) == rid:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if ID_RE.match(lines[j]):
            end = j
            break
    return lines[start:end]


def _parse_record(block):
    """Read the flat fields this helper reports from a record block."""
    rec = {"id": None, "title": None, "category": None,
           "predicate": None, "enforcement_status": None,
           "corpus_ref": None, "conflicts": []}
    section = None
    for line in block:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if indent == 4 and stripped.endswith(":") and ":" in stripped:
            section = stripped[:-1]
        if line.startswith("  - id:"):
            rec["id"] = _unquote(line.split(":", 1)[1])
            section = None
        elif line.startswith("    title:"):
            rec["title"] = _unquote(line.split(":", 1)[1])
            section = None
        elif line.startswith("    category:"):
            rec["category"] = _unquote(line.split(":", 1)[1])
            section = None
        elif line.startswith("    corpus_ref:"):
            rec["corpus_ref"] = _unquote(line.split(":", 1)[1])
            section = None
        elif line.startswith("      predicate:") and section == "activation":
            rec["predicate"] = _unquote(line.split(":", 1)[1])
        elif line.startswith("      status:") and section == "enforcement":
            rec["enforcement_status"] = _unquote(line.split(":", 1)[1])
        elif line.startswith("      - rule:") and section == "conflicts":
            rec["conflicts"].append(_unquote(line.split(":", 1)[1]))
    return rec


def _profiles_including(rid, category):
    """Profiles whose guidance_rules or selector include the rule."""
    with open(PROFILES, encoding="utf-8") as handle:
        data = json.load(handle)
    prefix = rid.split("-")[1] if "-" in rid else ""
    hits = []
    for prof in data.get("profiles", []):
        reasons = []
        if rid in (prof.get("guidance_rules") or []):
            reasons.append("guidance_rules")
        includes = prof.get("includes") or {}
        if prefix and prefix in (includes.get("category_prefixes") or []):
            reasons.append("selector category %s" % prefix)
        if reasons:
            hits.append((prof["id"], ", ".join(reasons)))
    return hits


def _corpus_section(corpus_ref, rid):
    """Slice the module from the ``## <ID>`` heading to the next ``## STOW-``."""
    if not corpus_ref:
        return ""
    module = corpus_ref.split("#", 1)[0]
    path = os.path.join(SKILL_DIR, *module.split("/"))
    if not os.path.isfile(path):
        return ""
    lines = open(path, encoding="utf-8").read().splitlines()
    head = ("## " + rid).lower()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == head:
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip().lower().startswith("## stow-"):
            end = j
            break
    return "\n".join(lines[start:end]).rstrip()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Corpus sections carry verbatim source wording that may include non-ASCII
    # characters; keep output UTF-8 regardless of the host console codepage.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    if len(argv) != 1:
        print("usage: query_rules.py STOW-XXX-NNN", file=sys.stderr)
        return 2
    rid = argv[0].strip()

    with open(REGISTRY, encoding="utf-8") as handle:
        text = handle.read()
    block = _record_block(text, rid)
    if block is None:
        print("unknown rule id: %s" % rid, file=sys.stderr)
        return 2

    rec = _parse_record(block)
    profiles = _profiles_including(rid, rec["category"])
    section = _corpus_section(rec["corpus_ref"], rid)

    print("id: %s" % rec["id"])
    print("title: %s" % (rec["title"] or ""))
    print("category: %s" % (rec["category"] or ""))
    print("activation predicate: %s" % (rec["predicate"] or ""))
    print("enforcement status: %s" % (rec["enforcement_status"] or ""))
    print("conflicts: %s" % (", ".join(rec["conflicts"]) if rec["conflicts"] else "none"))
    if profiles:
        print("profiles including this rule:")
        for pid, why in profiles:
            print("  %s (%s)" % (pid, why))
    else:
        print("profiles including this rule: none")
    print("corpus section (%s):" % (rec["corpus_ref"] or "none"))
    print(section if section else "(section not found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
