#!/usr/bin/env python3
"""Cold, sparse lookup for the packaged controlled dictionary.

Lookup reports closed membership and listed-form facts. It does not determine
part of speech, sense, technical-term authority, or controlled-language
conformance. Candidate scanning trusts caller-labelled editable segments.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import re
import sys
import unicodedata


DEFAULT_DICTIONARY = (
    Path(__file__).resolve().parents[1] / "rules" / "controlled-dictionary-v1.json.gz"
)
SCAN_BOUNDARY = (
    "Known dictionary matches only; unknown terms, part of speech, sense, "
    "technical-term authority, and final-output custody remain unclassified."
)
DOCUMENT_KEYS = frozenset({
    "schema_version", "normalization", "generated_counts", "records"
})
RECORD_KEYS = frozenset({
    "locator", "headword_raw", "normalized_base_key",
    "part_of_speech", "status", "construction_annotation_raw",
    "approved_forms", "form_parse_state", "meaning_or_alternatives_raw",
})
SEGMENT_KEYS = frozenset({"kind", "text"})
TOKEN_PATTERN = re.compile(r"[\w]+(?:[-'][\w]+)*", re.UNICODE)
COUNT_KEYS = frozenset({
    "records", "approved", "not_approved", "letter_sections", "approved_verbs"
})
PARTS_OF_SPEECH = frozenset({
    "n", "v", "adj", "adv", "pron", "art", "prep", "conj", "prefix",
    "unclassified",
})
FORM_STATES = frozenset({
    "not-applicable", "no-explicit-forms", "listed", "restricted-list",
    "restricted-no-other-forms", "source-separator-anomaly",
})


class DictionaryError(ValueError):
    """Dictionary data or caller input is malformed or unobservable."""


class DuplicateKeyError(ValueError):
    """A JSON object repeats a key."""


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError("duplicate JSON key %r" % key)
        value[key] = item
    return value


def normalize_key(value):
    if not isinstance(value, str):
        raise DictionaryError("lookup value must be a string")
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def _validate_document(value):
    if not isinstance(value, dict) or frozenset(value) != DOCUMENT_KEYS:
        raise DictionaryError("dictionary document keys differ")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise DictionaryError("dictionary schema_version must be 1")
    if value["normalization"] != "NFKC-casefold-whitespace":
        raise DictionaryError("dictionary normalization is unsupported")
    records = value["records"]
    if not isinstance(records, list) or not records:
        raise DictionaryError("dictionary records must be a nonempty array")
    locators = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or frozenset(record) != RECORD_KEYS:
            raise DictionaryError("dictionary record %d keys differ" % index)
        if not isinstance(record["locator"], str) or not re.fullmatch(
            r"[A-Z]:[0-9]{4}", record["locator"]
        ):
            raise DictionaryError("dictionary record %d locator differs" % index)
        if record["status"] not in {"approved", "not_approved"}:
            raise DictionaryError("dictionary record %d status differs" % index)
        if record["part_of_speech"] not in PARTS_OF_SPEECH:
            raise DictionaryError("dictionary record %d part of speech differs" % index)
        if record["form_parse_state"] not in FORM_STATES:
            raise DictionaryError("dictionary record %d form state differs" % index)
        string_fields = RECORD_KEYS - {"approved_forms"}
        if any(not isinstance(record[key], str) for key in string_fields):
            raise DictionaryError("dictionary record %d string field differs" % index)
        if not record["headword_raw"] or not record["normalized_base_key"] or not record["meaning_or_alternatives_raw"]:
            raise DictionaryError("dictionary record %d required text differs" % index)
        if record["normalized_base_key"] != normalize_key(record["headword_raw"]):
            raise DictionaryError("dictionary record %d normalized key differs" % index)
        forms = record["approved_forms"]
        if not isinstance(forms, list) or any(
            not isinstance(form, str) or not form for form in forms
        ):
            raise DictionaryError("dictionary record %d forms differ" % index)
        locators.append(record["locator"])
    if len(locators) != len(set(locators)):
        raise DictionaryError("dictionary locators must be unique")
    counts = value["generated_counts"]
    if not isinstance(counts, dict) or frozenset(counts) != COUNT_KEYS:
        raise DictionaryError("dictionary generated counts differ")
    if any(type(counts[key]) is not int or counts[key] < 0 for key in COUNT_KEYS):
        raise DictionaryError("dictionary generated count types differ")
    if counts.get("records") != len(records):
        raise DictionaryError("dictionary record count differs")
    if counts.get("approved") != sum(r["status"] == "approved" for r in records):
        raise DictionaryError("dictionary approved count differs")
    if counts.get("not_approved") != sum(r["status"] == "not_approved" for r in records):
        raise DictionaryError("dictionary not-approved count differs")
    if counts.get("approved_verbs") != sum(
        r["status"] == "approved" and r["part_of_speech"] == "v" for r in records
    ):
        raise DictionaryError("dictionary approved-verb count differs")
    if counts.get("letter_sections") != len({
        locator.split(":", 1)[0] for locator in locators
    }):
        raise DictionaryError("dictionary section count differs")
    return value


def load_dictionary(path=DEFAULT_DICTIONARY):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            value = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        raise DictionaryError("dictionary could not be read: %s" % error) from error
    return _validate_document(value)


def _construction_keys(record):
    annotation = record["construction_annotation_raw"]
    if not annotation:
        return ()
    candidate = annotation.strip().strip("()").strip()
    normalized = normalize_key(candidate)
    base = record["normalized_base_key"]
    if normalized.startswith("or "):
        return (normalize_key(normalized[3:]),)
    if base == normalized or base in normalized.split() or any(
        token.startswith(base) for token in normalized.split() if len(base) >= 4
    ):
        return (normalized,)
    return (normalize_key(base + " " + normalized),)


def _indices(data):
    headwords = {}
    forms = {}
    surfaces = {}
    records = {record["locator"]: record for record in data["records"]}
    for record in data["records"]:
        locator = record["locator"]
        base = record["normalized_base_key"]
        headwords.setdefault(base, []).append(locator)
        surfaces.setdefault(base, []).append(locator)
        for construction in _construction_keys(record):
            surfaces.setdefault(construction, []).append(locator)
        for form in record["approved_forms"]:
            key = normalize_key(form)
            forms.setdefault(key, []).append(locator)
            surfaces.setdefault(key, []).append(locator)
    for table in (headwords, forms, surfaces):
        for key, values in table.items():
            table[key] = tuple(dict.fromkeys(values))
    return records, headwords, forms, surfaces


def _classification(records, headword_match, form_match):
    statuses = {record["status"] for record in records}
    if len(statuses) > 1:
        return "AMBIGUOUS"
    if statuses == {"not_approved"}:
        return "KNOWN_NOT_APPROVED_CANDIDATE"
    if form_match and not headword_match:
        return "FORM_LISTED"
    return "KNOWN_APPROVED_CANDIDATE"


def lookup(data, term):
    key = normalize_key(term)
    records, headwords, forms, surfaces = _indices(data)
    locators = surfaces.get(key, ())
    selected = [records[locator] for locator in locators]
    classification = "UNKNOWN"
    if selected:
        classification = _classification(
            selected, key in headwords, key in forms
        )
    return {
        "query": term,
        "normalized_key": key,
        "classification": classification,
        "records": selected,
        "boundary": SCAN_BOUNDARY,
    }


def check_form(data, headword, form):
    base_key = normalize_key(headword)
    form_key = normalize_key(form)
    records, headwords, _forms, _surfaces = _indices(data)
    selected = [
        records[locator] for locator in headwords.get(base_key, ())
        if records[locator]["status"] == "approved"
    ]
    if not selected:
        classification = "UNKNOWN"
    else:
        matches = [
            record for record in selected
            if form_key in {normalize_key(item) for item in record["approved_forms"]}
        ]
        classification = "FORM_LISTED" if matches else "FORM_UNKNOWN"
        if matches:
            selected = matches
    return {
        "headword": headword,
        "form": form,
        "classification": classification,
        "records": selected,
        "boundary": SCAN_BOUNDARY,
    }


def _validate_candidate(candidate):
    if not isinstance(candidate, dict) or frozenset(candidate) != {
        "schema_version", "segments"
    }:
        raise DictionaryError("candidate keys differ")
    if type(candidate["schema_version"]) is not int or candidate["schema_version"] != 1:
        raise DictionaryError("candidate schema_version must be 1")
    if not isinstance(candidate["segments"], list) or not candidate["segments"]:
        raise DictionaryError("candidate segments must be a nonempty array")
    editable = 0
    for index, segment in enumerate(candidate["segments"]):
        if not isinstance(segment, dict) or frozenset(segment) != SEGMENT_KEYS:
            raise DictionaryError("candidate segment %d keys differ" % index)
        if segment["kind"] not in {"editable", "protected"}:
            raise DictionaryError("candidate segment %d kind differs" % index)
        if not isinstance(segment["text"], str):
            raise DictionaryError("candidate segment %d text must be a string" % index)
        editable += segment["kind"] == "editable"
    if not editable:
        raise DictionaryError("candidate has zero editable segments")


def scan(data, candidate):
    _validate_candidate(candidate)
    records, headwords, forms, surfaces = _indices(data)
    max_words = max(len(key.split()) for key in surfaces)
    findings = []
    for segment_index, segment in enumerate(candidate["segments"]):
        if segment["kind"] != "editable":
            continue
        text = segment["text"]
        tokens = list(TOKEN_PATTERN.finditer(text))
        position = 0
        while position < len(tokens):
            found = None
            consumed = 0
            remaining = len(tokens) - position
            for width in range(min(max_words, remaining), 0, -1):
                start = tokens[position].start()
                end = tokens[position + width - 1].end()
                key = normalize_key(text[start:end])
                locators = surfaces.get(key)
                if not locators:
                    continue
                selected = [records[locator] for locator in locators]
                classification = _classification(
                    selected, key in headwords, key in forms
                )
                if classification in {"KNOWN_NOT_APPROVED_CANDIDATE", "AMBIGUOUS"}:
                    found = {
                        "segment_index": segment_index,
                        "start": start,
                        "end": end,
                        "surface": text[start:end],
                        "normalized_key": key,
                        "classification": classification,
                        "records": selected,
                    }
                    position += width
                    break
                consumed = width
                position += width
                break
            if found:
                findings.append(found)
            elif consumed:
                continue
            else:
                position += 1
    return {
        "status": "REVIEW" if findings else "NO_KNOWN_DICTIONARY_FINDINGS",
        "findings": findings,
        "boundary": SCAN_BOUNDARY,
    }


def _load_candidate(path):
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        raise DictionaryError("candidate could not be read: %s" % error) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    subparsers = parser.add_subparsers(dest="command", required=True)
    lookup_parser = subparsers.add_parser("lookup")
    lookup_parser.add_argument("term")
    form_parser = subparsers.add_parser("form")
    form_parser.add_argument("headword")
    form_parser.add_argument("form")
    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--segments", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        data = load_dictionary(args.dictionary)
        if args.command == "lookup":
            result = lookup(data, args.term)
        elif args.command == "form":
            result = check_form(data, args.headword, args.form)
        else:
            result = scan(data, _load_candidate(args.segments))
    except DictionaryError as error:
        result = {"status": "UNKNOWN", "error": str(error), "findings": []}
        print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
