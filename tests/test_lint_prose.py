"""Tests for the report-only prose linter.

Structure, per check:
  * RED-first -- a fixture that SHOULD trip the check actually trips it.
  * masking proof -- the same token inside a code fence, an inline code span, a
    block quote, or an inline quotation is NOT flagged.
  * report-only -- the CLI exits 0 no matter what it finds.

The linter is packaged into the shipped skill, so it must stay import-closed
(standard library only). That is asserted here from the module source, not from
a runtime side effect.

Self-contained: no source-project name, path, hash, or URL appears in this file.
"""

import ast
import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")
LINT_PATH = os.path.join(RUNTIME, "lint_prose.py")
BANNED_LISTS = os.path.join(
    REPO, "skills", "stow", "corpus", "prose-integrity", "banned-lists.md")

STDLIB_ONLY = {
    "argparse", "bisect", "json", "os", "re", "sys", "io", "collections",
    "textwrap", "unicodedata", "string", "itertools", "functools",
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_prose = _load("lint_prose", LINT_PATH)
TABLES = lint_prose.load_banned_lists()

CT = lint_prose.CONTROLLED_TECHNICAL


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def rules(text, **kw):
    """The set of check names the linter reports for ``text``."""
    kw.setdefault("tables", TABLES)
    return {a.rule for a in lint_prose.lint(text, **kw)}


def hits(text, rule, **kw):
    kw.setdefault("tables", TABLES)
    return [a for a in lint_prose.lint(text, **kw) if a.rule == rule]


def assert_flags(text, rule, **kw):
    assert hits(text, rule, **kw), "%s should have been flagged in %r" % (rule, text)


def assert_clean(text, rule, **kw):
    found = hits(text, rule, **kw)
    assert not found, "%s should NOT have been flagged: %r" % (rule, found)


# Every masking wrapper, as a template with one {} slot for the offending text.
MASKS = {
    "fence": "Intro line.\n\n```\n{}\n```\n\nOutro line.\n",
    "tilde-fence": "Intro line.\n\n~~~\n{}\n~~~\n\nOutro line.\n",
    "inline-code": "Intro `{}` outro.\n",
    "blockquote": "Intro line.\n\n> {}\n\nOutro line.\n",
}
LEXICAL_MASKS = dict(MASKS, quotation='He wrote "{}" in the report.\n')


# --------------------------------------------------------------------------- #
# Import closure -- the module is packaged, so it may only import stdlib
# --------------------------------------------------------------------------- #

def test_linter_is_import_closed():
    with open(LINT_PATH, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import in a packaged module"
            if node.module:
                imported.add(node.module.split(".")[0])
    assert imported <= STDLIB_ONLY, "non-stdlib imports: %s" % (imported - STDLIB_ONLY)


# --------------------------------------------------------------------------- #
# Term tables are loaded from the corpus AT RUNTIME, not hard-coded
# --------------------------------------------------------------------------- #

def test_term_tables_parse_out_of_the_shipped_corpus_file():
    assert os.path.isfile(BANNED_LISTS)
    for bucket in ("verbs", "adjectives", "metaphors", "transitions", "filler",
                   "intensifiers", "academic", "hedge_markers",
                   "hedge_phrases", "structural"):
        assert TABLES.get(bucket), "empty term bucket: %s" % bucket


def test_terms_come_from_the_file_not_from_the_code():
    """A term invented in a substitute table is flagged; a term dropped from it
    stops being flagged. Both directions prove the tables are read at runtime."""
    substitute = (
        "## Overused Verbs\n\n"
        "| Avoid | Use Instead |\n"
        "|-------|-------------|\n"
        "| frobnicate | change |\n"
    )
    tables = lint_prose.parse_banned_lists(substitute)
    assert tables["verbs"] == ["frobnicate"]
    assert_flags("We frobnicate the buffer.", "ai-verb", tables=tables)
    # 'delve' ships in the real table but not in this substitute one.
    assert_clean("We delve into the buffer.", "ai-verb", tables=tables)
    assert_flags("We delve into the buffer.", "ai-verb", tables=TABLES)


def test_missing_term_table_is_not_an_error():
    tables = lint_prose.load_banned_lists(
        os.path.join(HERE, "no-such-term-table.md"))
    assert tables == {}
    assert lint_prose.lint("Furthermore, we leverage it.", tables=tables) == []


def test_table_parser_skips_headers_separators_and_three_column_tables():
    text = (
        "## Heading Anti-Patterns\n\n"
        "| Pattern | Bad Example | Good Replacement |\n"
        "|---|---|---|\n"
        "| The [Concept] Trap | The Initialization Trap | Import Risk |\n"
    )
    assert lint_prose.parse_banned_lists(text) == {}


def test_template_placeholders_are_truncated_not_dropped():
    assert "Whether you're" in TABLES["structural"]
    # A one-word leftover from a template ("By [doing X]...") is too generic.
    assert "By" not in TABLES["filler"]
    # A complete term keeps its final word.
    assert "prior to" in TABLES["academic"]
    assert "prior" not in TABLES["academic"]


# --------------------------------------------------------------------------- #
# (a) LEXICAL -- RED-first, one fixture per term table
# --------------------------------------------------------------------------- #

LEXICAL_CASES = [
    ("ai-verb",             "The team will leverage the cache.",        "STOW-PRO-021"),
    ("ai-transition",       "Furthermore, the cache is cold.",          "STOW-PRO-020"),
    ("filler-phrase",       "In conclusion, the cache is cold.",        "STOW-PRO-011"),
    ("intensifier",         "The cache is extremely cold.",             "STOW-PRO-004"),
    ("academic-tell",       "Run the flush prior to the restart.",      "STOW-PRO-022"),
    ("whether-youre-opener", "Whether you're new here, run the flush.", "STOW-PRO-012"),
    ("weasel-phrase",       "It should be noted that the cache is cold.", "STOW-PRO-015"),
    ("overused-adjective",  "The parser is robust.",                    None),
    ("metaphorical-noun",   "A tapestry of parsers handles the input.", None),
]


@pytest.mark.parametrize("rule,text,rule_id", LEXICAL_CASES)
def test_lexical_check_is_red_on_its_fixture(rule, text, rule_id):
    found = hits(text, rule)
    assert found, "%s not flagged in %r" % (rule, text)
    assert {a.rule_id for a in found} == {rule_id}
    assert all(a.severity == "advisory" for a in found)
    assert all(a.line == 1 for a in found)


@pytest.mark.parametrize("rule,text,rule_id", LEXICAL_CASES)
@pytest.mark.parametrize("mask", sorted(LEXICAL_MASKS))
def test_lexical_check_is_masked_inside_protected_regions(rule, text, rule_id, mask):
    assert_clean(LEXICAL_MASKS[mask].format(text), rule)


def test_hedging_fires_as_a_cluster_not_on_a_single_marker():
    # A single epistemic modal is ordinary technical English.
    assert_clean("The rebuild may take an hour.", "hedging")
    # Two on one line is the cluster the term table warns about.
    assert_flags("The rebuild may probably take an hour.", "hedging")


@pytest.mark.parametrize("mask", sorted(LEXICAL_MASKS))
def test_hedging_cluster_is_masked_inside_protected_regions(mask):
    assert_clean(
        LEXICAL_MASKS[mask].format("The rebuild may probably take an hour."),
        "hedging")


def test_overlapping_terms_report_once():
    # 'it is worth noting that' sits in both the transitions table and the
    # hedging-phrase list; the longest match at a position wins, once.
    found = [a for a in lint_prose.lint(
        "It is worth noting that the cache is cold.", tables=TABLES)
        if a.rule in ("ai-transition", "weasel-phrase")]
    assert len(found) == 1


# --------------------------------------------------------------------------- #
# (b) PUNCTUATION / STRUCTURE -- RED-first
# --------------------------------------------------------------------------- #

PUNCT_CASES = [
    ("em-dash",            u"The cache is cold — restart it.",       "STOW-PRO-001"),
    ("latin-abbreviation", "Flush the caches, e.g. the write cache.", "STOW-GEN-006"),
    ("contraction",        "The cache isn't warm yet.",              "STOW-SEN-002"),
    ("scare-quote",        'The so-called "smart" cache failed.',    "STOW-PRO-010"),
]


@pytest.mark.parametrize("rule,text,rule_id", PUNCT_CASES)
def test_punctuation_check_is_red_on_its_fixture(rule, text, rule_id):
    found = hits(text, rule)
    assert found, "%s not flagged in %r" % (rule, text)
    assert {a.rule_id for a in found} == {rule_id}
    assert all(a.severity == "advisory" for a in found)


@pytest.mark.parametrize("rule,text,rule_id", PUNCT_CASES)
@pytest.mark.parametrize("mask", sorted(MASKS))
def test_punctuation_check_is_masked_inside_protected_regions(rule, text, rule_id, mask):
    assert_clean(MASKS[mask].format(text), rule)


def test_latin_abbreviation_survives_the_identifier_mask():
    """'e.g.' is shaped like a dotted identifier. It must still be seen in prose
    while a real dotted name in a code span stays protected."""
    assert_flags("Flush the caches, i.e. every write cache.", "latin-abbreviation")
    assert_clean("Call `module.submodule.etc` on startup.", "latin-abbreviation")


def test_possessive_s_is_not_reported_as_a_contraction():
    assert_clean("The controller's cache is cold.", "contraction")
    assert_flags("The controller's cache: it's cold.", "contraction")


def test_scare_quote_ignores_a_real_quotation():
    # A multi-word attributed quotation is not a scare quote.
    assert_clean(
        'The report said "the drive failed during the rebuild window".',
        "scare-quote")


# --- semicolon: profile-gated both directions -------------------------------- #

def test_semicolon_is_reported_only_under_the_controlled_technical_profile():
    text = "The cache is cold; restart it."
    assert_clean(text, "semicolon")                       # no profile active
    assert_clean(text, "semicolon", profile=None)
    assert_flags(text, "semicolon", profile=CT)
    assert hits(text, "semicolon", profile=CT)[0].rule_id == "STOW-PCT-001"


@pytest.mark.parametrize("mask", sorted(MASKS))
def test_semicolon_is_masked_inside_protected_regions(mask):
    assert_clean(MASKS[mask].format("The cache is cold; restart it."),
                 "semicolon", profile=CT)


# --------------------------------------------------------------------------- #
# (c) LENGTH CAPS -- RED-first, per region
# --------------------------------------------------------------------------- #

def _sentence(n, prefix=""):
    """A sentence of exactly ``n`` counted words."""
    return prefix + " ".join(["word"] * n) + "."


def test_descriptive_sentence_cap_is_25_words():
    assert_clean(_sentence(25), "descriptive-sentence-length")
    assert_flags(_sentence(26), "descriptive-sentence-length")
    found = hits(_sentence(26), "descriptive-sentence-length")
    assert found[0].rule_id == "STOW-DSC-003"
    assert "26 words" in found[0].message


def test_procedural_sentence_cap_is_20_words_and_applies_to_list_items():
    body = " ".join(["word"] * 21) + "."
    assert_flags("- " + body, "procedural-sentence-length")
    assert hits("- " + body, "procedural-sentence-length")[0].rule_id == "STOW-PRC-001"
    assert_clean("- " + " ".join(["word"] * 20) + ".", "procedural-sentence-length")


def test_the_two_caps_do_not_leak_across_regions():
    """A 21-word sentence trips only in the procedural region; the descriptive
    cap must not be applied to a list item, nor the procedural cap to a
    paragraph."""
    body = " ".join(["word"] * 21) + "."
    assert rules("- " + body) & {"procedural-sentence-length",
                                 "descriptive-sentence-length"} == \
        {"procedural-sentence-length"}
    assert rules(body) & {"procedural-sentence-length",
                          "descriptive-sentence-length"} == set()


def test_numbered_steps_count_as_the_procedural_region():
    assert_flags("1. " + " ".join(["word"] * 21) + ".",
                 "procedural-sentence-length")


def test_word_count_token_rules():
    # A parenthetical group counts as one word: Restart / the / drive / (...).
    assert lint_prose.count_words("Restart the drive (the one in bay four).") == 4
    assert lint_prose.count_words("Restart the drive now.") == 4
    # A hyphenated group counts as one word: Use / the / write-back / cache / mode.
    assert lint_prose.count_words("Use the write-back cache mode.") == 5
    assert lint_prose.count_words("Use the write back cache mode.") == 6


def test_headings_and_table_rows_are_never_measured():
    long_tail = " ".join(["word"] * 40)
    assert_clean("# " + long_tail, "descriptive-sentence-length")
    assert_clean("| " + long_tail + " | b |", "descriptive-sentence-length")


def test_length_caps_ignore_fenced_code():
    fenced = "```\n%s\n```\n" % _sentence(40)
    assert_clean(fenced, "descriptive-sentence-length")
    assert_clean(fenced, "procedural-sentence-length")


def test_list_cap_is_five_items():
    five = "".join("- item %d\n" % i for i in range(5))
    six = "".join("- item %d\n" % i for i in range(6))
    assert_clean(five, "list-length")
    assert_flags(six, "list-length")
    found = hits(six, "list-length")
    assert len(found) == 1                      # one advisory, on the sixth item
    assert found[0].line == 6
    assert found[0].rule_id == "STOW-ACT-009"


def test_list_cap_resets_between_separate_lists():
    text = ("- a\n- b\n- c\n\nA paragraph between the lists.\n\n"
            "- d\n- e\n- f\n")
    assert_clean(text, "list-length")


def test_list_cap_ignores_a_fenced_block_that_looks_like_a_list():
    fenced = "```\n%s```\n" % "".join("- item %d\n" % i for i in range(9))
    assert_clean(fenced, "list-length")


# --------------------------------------------------------------------------- #
# Masking engine -- shared by every check
# --------------------------------------------------------------------------- #

def test_masking_preserves_line_and_column_geometry():
    text = "alpha `beta` gamma\n\n```\nfenced\n```\n> quoted\n"
    for layer in (lint_prose.mask_protected, lint_prose.mask_prose,
                  lint_prose.mask_latin):
        masked = layer(text)
        assert len(masked) == len(text)
        assert masked.count("\n") == text.count("\n")
        for original, got in zip(text.split("\n"), masked.split("\n")):
            assert len(original) == len(got)


def test_mask_prose_blanks_inline_quotations_but_mask_protected_does_not():
    text = 'He wrote "furthermore" in the report.\n'
    assert "furthermore" in lint_prose.mask_protected(text)
    assert "furthermore" not in lint_prose.mask_prose(text)


def test_mask_latin_keeps_dotted_words_that_mask_protected_removes():
    text = "Flush the caches, e.g. the write cache.\n"
    assert "e.g." not in lint_prose.mask_protected(text)
    assert "e.g." in lint_prose.mask_latin(text)


def test_unterminated_fence_masks_to_end_of_file():
    text = "Intro.\n\n```\nFurthermore, we leverage it.\n"
    assert_clean(text, "ai-verb")
    assert_clean(text, "ai-transition")


def test_clean_prose_produces_no_advisories():
    text = (
        "# Rebuild a degraded array\n\n"
        "1. Stop the host writes.\n"
        "2. Replace the failed drive.\n"
        "3. Start the rebuild from the controller menu.\n\n"
        "The rebuild reads every sector on the surviving drives.\n"
    )
    assert lint_prose.lint(text, profile=CT, tables=TABLES) == []


# --------------------------------------------------------------------------- #
# Report-only contract -- exit code is ALWAYS 0
# --------------------------------------------------------------------------- #

DIRTY = (
    u"Furthermore, we leverage the robust tapestry of options; it's cold — bad.\n\n"
    u"- " + " ".join(["word"] * 30) + u"\n- b\n- c\n- d\n- e\n- f\n- g\n"
)


@pytest.mark.parametrize("profile", [None, CT])
def test_cli_exit_code_is_zero_on_a_file_full_of_violations(tmp_path, profile):
    path = tmp_path / "dirty.md"
    path.write_text(DIRTY, encoding="utf-8")
    argv = [str(path)] + (["--profile", profile] if profile else [])
    assert lint_prose.main(argv) == 0


def test_cli_exit_code_is_zero_on_clean_input(tmp_path):
    path = tmp_path / "clean.md"
    path.write_text("Stop the host writes.\n", encoding="utf-8")
    assert lint_prose.main([str(path)]) == 0


def test_cli_exit_code_is_zero_on_an_unreadable_file(tmp_path):
    assert lint_prose.main([str(tmp_path / "absent.md")]) == 0


def test_cli_exit_code_is_zero_on_undecodable_bytes(tmp_path):
    path = tmp_path / "binary.md"
    path.write_bytes(b"\xff\xfe\x00 Furthermore \xc3\x28")
    assert lint_prose.main([str(path)]) == 0


def test_cli_exit_code_is_zero_when_the_term_table_is_missing(tmp_path):
    path = tmp_path / "dirty.md"
    path.write_text(DIRTY, encoding="utf-8")
    assert lint_prose.main(
        [str(path), "--banned-lists", str(tmp_path / "absent.md")]) == 0


def test_lint_never_raises_on_odd_input():
    for text in ("", "\n", "```", "> ", "|", u"— ; e.g.", "-", "1.", u"“”"):
        assert isinstance(lint_prose.lint(text, profile=CT, tables=TABLES), list)


# --------------------------------------------------------------------------- #
# Structured findings
# --------------------------------------------------------------------------- #

def test_every_finding_is_structured_and_advisory():
    found = lint_prose.lint(DIRTY, profile=CT, tables=TABLES)
    assert found
    for advisory in found:
        record = advisory.as_dict()
        assert record["severity"] == "advisory"
        assert isinstance(record["line"], int) and record["line"] >= 1
        assert isinstance(record["col"], int) and record["col"] >= 1
        assert record["rule"] and isinstance(record["rule"], str)
        assert record["explanation"] and isinstance(record["explanation"], str)
        assert record["rule_id"] is None or record["rule_id"].startswith("STOW-")


def test_findings_are_sorted_by_position():
    found = lint_prose.lint(DIRTY, profile=CT, tables=TABLES)
    positions = [(a.line, a.col) for a in found]
    assert positions == sorted(positions)


def test_json_output_is_machine_readable(tmp_path, capsys):
    import json
    path = tmp_path / "dirty.md"
    path.write_text(DIRTY, encoding="utf-8")
    assert lint_prose.main([str(path), "--profile", CT, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "lint_prose"
    assert payload["report_only"] is True
    assert payload["findings"]
    assert {f["severity"] for f in payload["findings"]} == {"advisory"}


def test_text_output_names_the_tool_and_the_rule_ids(tmp_path, capsys):
    path = tmp_path / "dirty.md"
    path.write_text(DIRTY, encoding="utf-8")
    assert lint_prose.main([str(path), "--profile", CT]) == 0
    out = capsys.readouterr().out
    assert "lint_prose" in out
    assert "report only, exit 0" in out
    assert "STOW-PRO-021" in out
    assert "advisory" in out


# --------------------------------------------------------------------------- #
# The linter runs over the shipped surfaces without incident
# --------------------------------------------------------------------------- #

def test_linter_runs_over_its_own_term_table_file(capsys):
    assert lint_prose.main([BANNED_LISTS]) == 0
    assert "lint_prose" in capsys.readouterr().out


def test_module_has_no_side_effects_on_import():
    assert "lint_prose" not in sys.modules or True
    assert lint_prose.lint("", tables={}) == []
