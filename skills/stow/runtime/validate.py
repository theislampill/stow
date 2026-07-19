#!/usr/bin/env python3
"""Deterministic structured-output validators for JSON, JSONL, and YAML.

This module is PACKAGED into the shipped skill. It is import-closed: it imports
only the Python standard library and ``ruamel.yaml``. It never imports from a
repository tool, the repo root, or any sibling module, so it runs unchanged from
inside an extracted artifact where only the artifact is on ``sys.path``.

Each validator returns a :class:`Result`. The command line interface exits 0
when a file is valid and nonzero (with a clear message) when it is not. Warnings
are advisory and never change the exit status.

JSON contract
    Exactly one JSON value. Rejects a leading BOM (U+FEFF), the non-finite
    literals ``NaN`` / ``Infinity`` / ``-Infinity`` (and any numeric literal that
    overflows to a non-finite float), ``//`` and ``/* */`` comments, trailing
    commas, duplicate object keys, and a wrapping Markdown code fence.

JSONL contract
    One JSON value per non-empty line, parsed independently, with no wrapping
    array. Failures are reported by line number. A single trailing newline (and
    incidental blank lines) are accepted.

YAML contract
    Parsed with ``ruamel.yaml`` ``YAML(typ='safe')`` pinned to version 1.2.
    Custom (non-core) tags, anchors, and aliases are rejected. Ambiguous
    scalars are reported as warnings, not failures. Duplicate keys are detected
    by a node-level walk that compares the RAW SOURCE TOKEN of each scalar key
    (its ``node.value`` plus resolved tag) -- never the resolved Python value --
    so ``1:`` and ``1.0:`` remain distinct keys, ``0x10:`` and ``16:`` remain
    distinct keys, and only the same token appearing twice is a duplicate.
"""

import argparse
import io
import json
import math
import sys

from ruamel.yaml import YAML
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #

class Result:
    """Outcome of one validation.

    ``ok``       -- True when there are no errors.
    ``errors``   -- human-readable failure messages (nonzero exit).
    ``warnings`` -- advisory notes (never affect the exit status).
    ``data``     -- optional structured detail (e.g. per-line errors, the raw
                    key tokens collected from a YAML root mapping).
    """

    def __init__(self, ok, errors=None, warnings=None, data=None):
        self.ok = bool(ok)
        self.errors = list(errors or [])
        self.warnings = list(warnings or [])
        self.data = dict(data or {})

    def __repr__(self):
        return "Result(ok=%r, errors=%r, warnings=%r)" % (
            self.ok, self.errors, self.warnings)


BOM = "﻿"


# --------------------------------------------------------------------------- #
# Shared JSON strictness hooks
# --------------------------------------------------------------------------- #

def _no_duplicate_pairs(pairs):
    """``object_pairs_hook`` that rejects duplicate keys instead of last-wins."""
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError("duplicate object key: %r" % (key,))
        seen.add(key)
    return dict(pairs)


def _reject_constant(name):
    """``parse_constant`` hook: NaN / Infinity / -Infinity are not allowed."""
    raise ValueError("non-finite JSON constant not allowed: %s" % name)


def _strict_float(token):
    """``parse_float`` hook: reject any literal that is not a finite number."""
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("non-finite number literal not allowed: %s" % token)
    return value


def _loads_strict(text):
    """``json.loads`` with duplicate-key, non-finite, and comment strictness.

    Standard ``json`` already rejects comments and trailing commas; the hooks add
    duplicate-key and non-finite rejection on top.
    """
    return json.loads(
        text,
        object_pairs_hook=_no_duplicate_pairs,
        parse_constant=_reject_constant,
        parse_float=_strict_float,
    )


# --------------------------------------------------------------------------- #
# JSON
# --------------------------------------------------------------------------- #

def validate_json(text):
    errors = []

    if text.startswith(BOM):
        errors.append("leading BOM (U+FEFF) is not allowed")
        text = text[len(BOM):]

    if text.lstrip().startswith("```"):
        errors.append("Markdown code fence detected; emit raw JSON, not a fenced block")
        return Result(False, errors)

    try:
        _loads_strict(text)
    except ValueError as exc:  # JSONDecodeError is a ValueError subclass
        errors.append("JSON parse error: %s" % exc)

    return Result(len(errors) == 0, errors)


# --------------------------------------------------------------------------- #
# JSONL
# --------------------------------------------------------------------------- #

def validate_jsonl(text):
    errors = []
    line_errors = []

    if text.startswith(BOM):
        line_errors.append((1, "leading BOM (U+FEFF) is not allowed"))
        text = text[len(BOM):]

    for lineno, raw_line in enumerate(text.split("\n"), start=1):
        line = raw_line.rstrip("\r")  # tolerate CRLF endings
        if line.strip() == "":
            continue  # blank / trailing lines carry no record
        try:
            _loads_strict(line)
        except ValueError as exc:
            line_errors.append((lineno, "JSON parse error: %s" % exc))

    for lineno, message in line_errors:
        errors.append("line %d: %s" % (lineno, message))

    return Result(len(line_errors) == 0, errors, data={"line_errors": line_errors})


# --------------------------------------------------------------------------- #
# YAML
# --------------------------------------------------------------------------- #

# YAML 1.2 core schema tags. Anything else (a custom ``!tag`` or the merge key
# ``<<``) is rejected.
_CORE_TAGS = frozenset([
    "tag:yaml.org,2002:null",
    "tag:yaml.org,2002:bool",
    "tag:yaml.org,2002:int",
    "tag:yaml.org,2002:float",
    "tag:yaml.org,2002:str",
    "tag:yaml.org,2002:seq",
    "tag:yaml.org,2002:map",
])

# Plain scalars a reader is likely to misread (the YAML "Norway problem" and the
# one-letter bool-ish tokens). Advisory only.
_AMBIGUOUS_SCALARS = frozenset(["yes", "no", "on", "off", "y", "n"])


def _new_yaml():
    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    # We do our OWN token-level duplicate detection below; the built-in
    # resolved-value comparison would wrongly flag 1 vs 1.0 as a duplicate.
    yaml.allow_duplicate_keys = True
    return yaml


def _scalar_key_tokens(mapping_node):
    """Raw source tokens of a mapping's scalar keys, in order."""
    tokens = []
    for key_node, _value_node in mapping_node.value:
        if isinstance(key_node, ScalarNode):
            tokens.append(key_node.value)
    return tokens


def _walk_node(node, errors, warnings, seen_ids):
    """Recurse the representation graph collecting structural violations."""
    node_id = id(node)
    if node_id in seen_ids:
        # The same node object reached twice means an alias resolved to it.
        errors.append("alias/anchor reuse is not allowed (YAML alias detected)")
        return
    seen_ids.add(node_id)

    anchor = getattr(node, "anchor", None)
    # In ruamel the anchor is a (possibly empty) string; a truthy value means an
    # anchor was declared on this node.
    if anchor:
        errors.append("anchors are not allowed (found &%s)" % anchor)

    if node.tag not in _CORE_TAGS:
        errors.append("custom / non-core tag is not allowed: %s" % node.tag)

    if isinstance(node, MappingNode):
        counts = {}
        for key_node, value_node in node.value:
            if isinstance(key_node, ScalarNode):
                token = (key_node.tag, key_node.value)
                counts[token] = counts.get(token, 0) + 1
            _walk_node(key_node, errors, warnings, seen_ids)
            _walk_node(value_node, errors, warnings, seen_ids)
        for (tag, raw), n in counts.items():
            if n > 1:
                errors.append(
                    "duplicate key: same source token %r (tag %s) appears %d times"
                    % (raw, tag, n))
    elif isinstance(node, SequenceNode):
        for child in node.value:
            _walk_node(child, errors, warnings, seen_ids)
    elif isinstance(node, ScalarNode):
        if node.tag == "tag:yaml.org,2002:str" \
                and node.value.strip().lower() in _AMBIGUOUS_SCALARS:
            warnings.append(
                "ambiguous scalar %r resolves to a string under YAML 1.2 but is "
                "easily misread as a boolean" % node.value)


def validate_yaml(text):
    errors = []
    warnings = []
    data = {}

    if text.startswith(BOM):
        errors.append("leading BOM (U+FEFF) is not allowed")
        text = text[len(BOM):]

    yaml = _new_yaml()
    try:
        documents = list(yaml.compose_all(io.StringIO(text)))
    except Exception as exc:  # noqa: BLE001 - surface any parser failure as an error
        errors.append("YAML parse error: %s" % exc)
        return Result(False, errors, warnings, data)

    root_tokens = []
    for index, node in enumerate(documents):
        if node is None:
            continue
        if index == 0 and isinstance(node, MappingNode):
            root_tokens = _scalar_key_tokens(node)
        _walk_node(node, errors, warnings, seen_ids=set())

    data["root_key_tokens"] = root_tokens
    data["document_count"] = len(documents)
    # De-duplicate identical messages (an anchored+aliased node yields two).
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    return Result(len(errors) == 0, errors, warnings, data)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

VALIDATORS = {
    "json": validate_json,
    "jsonl": validate_jsonl,
    "yaml": validate_yaml,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a structured-output file (JSON, JSONL, or YAML).")
    parser.add_argument("--format", required=True, choices=sorted(VALIDATORS),
                        help="the structured format to validate against")
    parser.add_argument("file", help="path to the file to validate")
    args = parser.parse_args(argv)

    try:
        with open(args.file, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        print("INVALID (%s): cannot read %s: %s" % (args.format, args.file, exc),
              file=sys.stderr)
        return 2

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print("INVALID (%s): %s is not valid UTF-8: %s" % (args.format, args.file, exc),
              file=sys.stderr)
        return 2

    result = VALIDATORS[args.format](text)

    for warning in result.warnings:
        print("WARN: %s" % warning)

    if result.ok:
        print("VALID (%s): %s" % (args.format, args.file))
        return 0

    print("INVALID (%s): %s" % (args.format, args.file), file=sys.stderr)
    for error in result.errors:
        print("  %s" % error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
