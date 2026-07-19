#!/usr/bin/env python3
"""Generate skills/stow/references/rule-index.md from the rule registry.

The index is a source-name-free listing of every primary record: id, title,
category, and precedence. It carries NO per-domain totals and NO source-project
names -- only STOW-authored metadata fields are read (never wording.baseline_*).

Usage:
  gen_rule_index.py            regenerate the index in place
  gen_rule_index.py --check    regenerate into memory and diff against the file;
                               exit nonzero (and print a diff) if it has drifted
"""

import argparse
import difflib
import os
import sys

from ruamel.yaml import YAML

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO_ROOT, "skills", "stow", "rules", "registry.yaml")
INDEX = os.path.join(REPO_ROOT, "skills", "stow", "references", "rule-index.md")


def _cell(text):
    return str(text).replace("|", "\\|")


def load_records(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as fh:
        data = yaml.load(fh)
    return data["records"], data["generated_counts"]["primary_total"]


def render(records, primary_total):
    lines = []
    lines.append("# STOW rule index")
    lines.append("")
    lines.append("Generated from `skills/stow/rules/registry.yaml` by "
                 "`tools/gen_rule_index.py`. Do not edit by hand.")
    lines.append("")
    lines.append("Primary records: %d" % primary_total)
    lines.append("")
    lines.append("| id | title | category | precedence |")
    lines.append("| --- | --- | --- | --- |")
    for r in records:
        lines.append("| %s | %s | %s | %s |" % (
            _cell(r["id"]), _cell(r["title"]),
            _cell(r["category"]), _cell(r["precedence"])))
    lines.append("")
    return "\n".join(lines)


def build():
    records, total = load_records(REGISTRY)
    return render(records, total)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the committed index is current; nonzero on drift")
    args = parser.parse_args(argv)

    content = build()

    if args.check:
        if not os.path.isfile(INDEX):
            print("rule-index.md is missing; run gen_rule_index.py", file=sys.stderr)
            return 1
        with open(INDEX, encoding="utf-8") as fh:
            current = fh.read()
        if current != content:
            diff = difflib.unified_diff(
                current.splitlines(True), content.splitlines(True),
                fromfile="rule-index.md (committed)",
                tofile="rule-index.md (regenerated)")
            sys.stdout.writelines(diff)
            print("\nrule-index.md is out of date; run gen_rule_index.py",
                  file=sys.stderr)
            return 1
        print("rule-index.md is current")
        return 0

    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print("wrote %s" % INDEX)
    return 0


if __name__ == "__main__":
    sys.exit(main())
