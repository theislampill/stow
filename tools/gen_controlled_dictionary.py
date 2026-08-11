#!/usr/bin/env python3
"""Extract and deterministically project the controlled dictionary data."""

from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
import re
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "tools" / "data" / "controlled-dictionary-v1.json"
DEFAULT_PROJECTION = (
    ROOT / "skills" / "stow" / "rules" / "controlled-dictionary-v1.json.gz"
)
EXPECTED_SECTIONS = tuple("ABCDEFGHIJKLMNOPQRSTUVWYZ")
EXPECTED_COUNTS = {
    "records": 2198,
    "approved": 879,
    "not_approved": 1319,
    "letter_sections": 25,
    "approved_verbs": 208,
}
LEXICAL_SUBSET_SCOPE = (
    "main-table expression, status, meaning or alternatives, and mechanically "
    "derived listed forms; example columns are intentionally excluded"
)
POS_PATTERN = re.compile(r"\((n|v|adj|adv|pron|art|prep|conj|prefix)\)")
HEADING_PATTERN = re.compile(r"## ([A-Z])$")


class ExtractionError(ValueError):
    """The source table is malformed or differs from the frozen contract."""


def normalize_key(value):
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def _split_forms(tail, headword, state):
    if not tail:
        return [headword]
    form_text = tail.split("<br>", 1)[0].strip()
    form_text = re.sub(
        r"\(\s*also\s+([^()]*)\)", r"\1", form_text, flags=re.IGNORECASE
    )
    form_text = re.sub(
        r"\s+No other verb forms\.\s*$", "", form_text, flags=re.IGNORECASE
    )
    form_text = form_text.strip().strip("()").strip()
    if not form_text:
        return [headword]
    if state == "source-separator-anomaly" and "," not in form_text:
        forms = form_text.split()
    else:
        forms = [part.strip() for part in form_text.split(",")]
    forms = [form for form in forms if form]
    return [headword] + forms


def parse_expression(expression, status):
    match = POS_PATTERN.search(expression)
    if match is None:
        return {
            "source_expression_raw": expression,
            "headword_raw": expression,
            "normalized_base_key": normalize_key(expression),
            "part_of_speech": "unclassified",
            "construction_annotation_raw": "",
            "forms_raw": "",
            "approved_forms": [],
            "form_parse_state": "not-applicable",
        }
    prefix = expression[:match.start()].strip()
    suffix = expression[match.end():]
    annotations = re.findall(r"\([^()]+\)", prefix)
    headword = re.sub(r"\s*\([^()]+\)", "", prefix).strip()
    if not headword:
        raise ExtractionError("word expression has no headword: %r" % expression)
    construction = " ".join(annotations)
    pos = match.group(1)
    raw_suffix = suffix.strip()
    had_comma = raw_suffix.startswith(",")
    forms_raw = raw_suffix[1:].strip() if had_comma else raw_suffix

    approved_forms = []
    state = "not-applicable"
    if status == "approved" and pos in {"v", "adj"}:
        form_prefix = forms_raw.split("<br>", 1)[0].strip()
        missing_internal_commas = (
            pos == "v" and form_prefix and "," not in form_prefix
            and len(form_prefix.split()) > 1
        )
        inline_restriction = bool(re.search(
            r"\s+No other verb forms\.\s*$", form_prefix, flags=re.IGNORECASE
        ))
        if pos == "v" and (
            (raw_suffix and not had_comma and not raw_suffix.startswith("<br>"))
            or missing_internal_commas
            or inline_restriction
        ):
            state = "source-separator-anomaly"
        elif "<br>" in raw_suffix:
            state = "restricted-list" if forms_raw.split("<br>", 1)[0].strip() else "restricted-no-other-forms"
        elif forms_raw:
            state = "listed"
        else:
            state = "no-explicit-forms"
        approved_forms = _split_forms(forms_raw, headword, state)

    return {
        "source_expression_raw": expression,
        "headword_raw": headword,
        "normalized_base_key": normalize_key(headword),
        "part_of_speech": pos,
        "construction_annotation_raw": construction,
        "forms_raw": forms_raw,
        "approved_forms": approved_forms,
        "form_parse_state": state,
    }


def extract_text(text, expected_sections=EXPECTED_SECTIONS):
    records = []
    sections = []
    section = None
    ordinal = 0
    in_main = False
    saw_header = False
    source_rows = set()

    for line_number, line in enumerate(text.splitlines(), 1):
        heading = HEADING_PATTERN.fullmatch(line)
        if heading:
            letter = heading.group(1)
            if not in_main:
                if letter != expected_sections[0]:
                    continue
                in_main = True
            section = letter
            sections.append(letter)
            ordinal = 0
            saw_header = False
            continue
        if not in_main:
            continue
        if line == "---":
            break
        if line.startswith("| Word (part of speech) |"):
            saw_header = True
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            if saw_header and line.strip():
                raise ExtractionError(
                    "unexpected non-table content at line %d" % line_number
                )
            continue
        if section is None or not saw_header:
            raise ExtractionError("table row outside a declared section at line %d" % line_number)
        if not line.endswith("|"):
            raise ExtractionError("unterminated table row at line %d" % line_number)
        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) != 5:
            raise ExtractionError(
                "table row at line %d has %d cells, expected 5" % (line_number, len(cells))
            )
        expression, status, meaning, _example, _other = cells
        source_row = tuple(cells)
        if source_row in source_rows:
            raise ExtractionError("duplicate source row at line %d" % line_number)
        source_rows.add(source_row)
        if status not in {"approved", "not approved"}:
            raise ExtractionError("invalid status at line %d: %r" % (line_number, status))
        ordinal += 1
        record = parse_expression(expression, status)
        record.update({
            "locator": "%s:%04d" % (section, ordinal),
            "status": status.replace(" ", "_"),
            "meaning_or_alternatives_raw": meaning,
        })
        records.append(record)

    if tuple(sections) != tuple(expected_sections):
        raise ExtractionError(
            "letter sections differ: expected=%r actual=%r"
            % (tuple(expected_sections), tuple(sections))
        )
    locators = [record["locator"] for record in records]
    if len(locators) != len(set(locators)):
        raise ExtractionError("duplicate locators")

    counts = {
        "records": len(records),
        "approved": sum(record["status"] == "approved" for record in records),
        "not_approved": sum(record["status"] == "not_approved" for record in records),
        "letter_sections": len(sections),
        "approved_verbs": sum(
            record["status"] == "approved" and record["part_of_speech"] == "v"
            for record in records
        ),
    }
    return {
        "schema_version": 1,
        "normalization": "NFKC-casefold-whitespace",
        "extraction_scope": LEXICAL_SUBSET_SCOPE,
        "generated_counts": counts,
        "records": records,
    }


def validate_value(value, expected_counts=None):
    """Validate semantic invariants that JSON Schema cannot express."""
    if value.get("schema_version") != 1:
        raise ExtractionError("schema_version differs")
    if value.get("normalization") != "NFKC-casefold-whitespace":
        raise ExtractionError("normalization differs")
    if value.get("extraction_scope") != LEXICAL_SUBSET_SCOPE:
        raise ExtractionError("extraction scope differs")
    records = value.get("records")
    if not isinstance(records, list) or not records:
        raise ExtractionError("records must be a nonempty array")
    locators = [record.get("locator") for record in records]
    if len(locators) != len(set(locators)):
        raise ExtractionError("duplicate locators")
    for record in records:
        if record.get("normalized_base_key") != normalize_key(record.get("headword_raw", "")):
            raise ExtractionError("normalized key differs at %s" % record.get("locator"))
        for form in record.get("approved_forms", []):
            if "No other verb forms" in form or form.count("(") != form.count(")"):
                raise ExtractionError("malformed approved form at %s" % record.get("locator"))
    counts = {
        "records": len(records),
        "approved": sum(record.get("status") == "approved" for record in records),
        "not_approved": sum(record.get("status") == "not_approved" for record in records),
        "letter_sections": len({locator.split(":", 1)[0] for locator in locators}),
        "approved_verbs": sum(
            record.get("status") == "approved" and record.get("part_of_speech") == "v"
            for record in records
        ),
    }
    if value.get("generated_counts") != counts:
        raise ExtractionError("generated counts differ: expected=%r actual=%r" % (counts, value.get("generated_counts")))
    if expected_counts is not None and counts != expected_counts:
        raise ExtractionError("source counts differ: expected=%r actual=%r" % (expected_counts, counts))
    return value


def canonical_bytes(value):
    return (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf-8")


RUNTIME_RECORD_KEYS = (
    "locator", "headword_raw", "normalized_base_key", "part_of_speech",
    "status", "construction_annotation_raw", "approved_forms",
    "form_parse_state", "meaning_or_alternatives_raw",
)


def runtime_projection(value):
    validate_value(value)
    return {
        "schema_version": value["schema_version"],
        "normalization": value["normalization"],
        "generated_counts": value["generated_counts"],
        "records": [
            {key: record[key] for key in RUNTIME_RECORD_KEYS}
            for record in value["records"]
        ],
    }


def projection_bytes(value):
    buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0
    ) as handle:
        handle.write(canonical_bytes(runtime_projection(value)))
    return buffer.getvalue()


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.source:
        value = extract_text(args.source.read_text(encoding="utf-8"))
        validate_value(value, EXPECTED_COUNTS)
        if args.check:
            if not args.data.is_file() or args.data.read_bytes() != canonical_bytes(value):
                print("controlled dictionary canonical data is stale")
                return 1
        else:
            args.data.parent.mkdir(parents=True, exist_ok=True)
            args.data.write_bytes(canonical_bytes(value))
    else:
        value = validate_value(load_json(args.data), EXPECTED_COUNTS)

    projected = projection_bytes(value)
    if args.check:
        if not args.projection.is_file() or args.projection.read_bytes() != projected:
            print("controlled dictionary runtime projection is stale")
            return 1
        print("controlled dictionary data and projection are current")
        return 0

    args.projection.parent.mkdir(parents=True, exist_ok=True)
    args.projection.write_bytes(projected)
    print("records: %d" % value["generated_counts"]["records"])
    print("projection_bytes: %d" % len(projected))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExtractionError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print("CONTROLLED_DICTIONARY_ERROR: %s" % error)
        raise SystemExit(2)
