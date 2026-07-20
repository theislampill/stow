# Controlled-technical writing profile: application reference

This reference is compressed application guidance for the controlled-technical
writing profile: **when and where** each rule fires, **which output region** it
governs, **how STOW checks it**, and a link to the corpus file that holds the
full normative text. It does not restate the rules themselves: read the linked
corpus file for the wording that governs.

**Guided, not conformant.** This profile is *guided*. STOW applies the checks
below as best-effort shaping of prose. Passing them is not a claim of full
conformance to any controlled-language standard, and it does not certify the
output against the external standard the rules trace to. Treat a clean pass as
*shaped toward the controlled-technical rules*, not *verified compliant*.

**Activation gate (shared by every rule here).** These are profile-precedence
rules. They apply only when a controlled-technical writing profile is active and
the response contains prose. They govern prose only and skip the protected
regions: code, structured data, quoted text, and identifiers. Unless a row says
otherwise, the region is *all prose*; the two exceptions are called out
explicitly.

**How to read each entry.** Every row names the *observable trigger* (the output
feature that invokes the check), the *region*, *how STOW checks it* (the
enforcement kind plus the named validator, with any numeric limit), and the
*corpus_ref* for the governing text. The controlled-technical rules are grouped
below as WRD (words), MWN (multi-word nouns), VRB (verbs, voice, tense), SEN
(sentences, lists, articles), STY (writing-practice consistency), and GEN
(general recommendations).

## WRD: words

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| WRD-001 | A content word appears in prose | all prose | semantic-review · `approved-word-lookup` | see corpus/words/selection.md#STOW-WRD-001 |
| WRD-002 | An approved word is used in some part of speech | all prose | parser · `pos-matches-dictionary` | see corpus/words/selection.md#STOW-WRD-002 |
| WRD-003 | An approved word carries a particular sense | all prose | semantic-review · `approved-sense-only` | see corpus/words/selection.md#STOW-WRD-003 |
| WRD-004 | An inflected verb or adjective form appears | all prose | parser · `approved-inflection-only` | see corpus/words/selection.md#STOW-WRD-004 |
| WRD-005 | A non-dictionary word appears | procedural or descriptive prose | semantic-review · `technical-noun-category-membership` | see corpus/words/approved-tables.md#STOW-WRD-005 |
| WRD-006 | An unapproved word appears | all prose | semantic-review · `technical-noun-context-check` | see corpus/words/selection.md#STOW-WRD-006 |
| WRD-007 | A technical-noun token is functioning as a verb | all prose | parser · `no-technical-noun-as-verb` | see corpus/words/selection.md#STOW-WRD-007 |
| WRD-008 | A technical noun is selected where a company, industry, or field term exists | all prose | heuristic · `company-term-preferred` | see corpus/words/usage.md#STOW-WRD-008 |
| WRD-009 | A coined or multi-word technical noun appears | all prose | deterministic · `technical-noun-max-3-words` (limit 3) | see corpus/words/usage.md#STOW-WRD-009 |
| WRD-010 | A candidate technical noun looks regional, slang, or jargon | all prose | semantic-review · `no-slang-or-jargon-noun` | see corpus/words/usage.md#STOW-WRD-010 |
| WRD-011 | Two or more synonymous nouns name one referent across the text | all prose | heuristic · `consistent-term-per-referent` | see corpus/words/usage.md#STOW-WRD-011 |
| WRD-012 | A non-dictionary verb appears | procedural or descriptive prose | semantic-review · `technical-verb-category-membership` | see corpus/words/usage.md#STOW-WRD-012 |
| WRD-013 | A technical-verb token is functioning as a noun | all prose | parser · `no-technical-verb-as-noun` | see corpus/words/usage.md#STOW-WRD-013 |
| WRD-014 | A word has a spelling variant (skips quoted text) | all prose | deterministic · `american-english-spelling` | see corpus/words/usage.md#STOW-WRD-014 |

WRD-011 and WRD-014 carry recorded conflict resolutions (with the presentation
layer and with protected regions respectively); the corpus file states the
resolution.

## MWN: multi-word nouns

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| MWN-001 | A noun phrase built from stacked nouns or modifiers appears | all prose | parser · `multiword-noun-max-3-words` (limit 3) | see corpus/multiword-nouns.md#STOW-MWN-001 |
| MWN-002 | A technical noun runs past three words | all prose | heuristic · `long-technical-noun-shorten-or-hyphenate` | see corpus/multiword-nouns.md#STOW-MWN-002 |

## VRB: verbs, voice, and tense

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| VRB-001 | A verb token appears | all prose | parser · `approved-verb-form-only` | see corpus/verbs/technical-verbs.md#STOW-VRB-001 |
| VRB-002 | A verb carries tense or aspect marking | all prose | parser · `approved-tense-only` | see corpus/verbs/technical-verbs.md#STOW-VRB-002 |
| VRB-003 | A past-participle form appears | all prose | parser · `participle-as-adjective-only` | see corpus/verbs/technical-verbs.md#STOW-VRB-003 |
| VRB-004 | An auxiliary combines with a main verb | all prose | parser · `no-auxiliary-complex-construction` | see corpus/verbs/technical-verbs.md#STOW-VRB-004 |
| VRB-005 | An `-ing` word appears | all prose | parser · `ing-only-as-technical-noun` | see corpus/verbs/technical-verbs.md#STOW-VRB-005 |
| VRB-006 | A clause is in the passive voice | all prose | parser · `active-voice-required-unless-agentless-descriptive` | see corpus/verbs/verb-forms.md#STOW-VRB-006 |
| VRB-007 | An action is expressed as a noun or other part of speech | all prose | heuristic · `prefer-verb-over-nominalization` | see corpus/verbs/verb-forms.md#STOW-VRB-007 |

## SEN: sentences, lists, and articles

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| SEN-001 | Each sentence in prose | all prose | semantic-review · `sentence-clarity-heuristic` | see corpus/sentences.md#STOW-SEN-001 |
| SEN-002 | A contraction or a dropped word appears | all prose | deterministic · `no-contractions-no-word-omission` | see corpus/sentences.md#STOW-SEN-002 |
| SEN-003 | A sentence packs complex or enumerated content | all prose | heuristic · `vertical-list-formatting` | see corpus/sentences.md#STOW-SEN-003 |
| SEN-004 | Adjacent sentences share a related topic | all prose | heuristic · `approved-connectors-only` | see corpus/sentences.md#STOW-SEN-004 |
| SEN-005 | A noun or multi-word noun appears without an article or demonstrative | all prose | parser · `article-and-demonstrative-usage` | see corpus/sentences.md#STOW-SEN-005 |

## STY: writing-practice consistency

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| STY-001 | A sentence where a word-for-word swap does not hold | all prose | semantic-review · `rewrite-construction-preserve-meaning` | see corpus/style/economy.md#STOW-STY-001 |
| STY-002 | An approved word's sense and part of speech in context | all prose | semantic-review · `restricted-meaning-and-pos-check` | see corpus/style/consistency.md#STOW-STY-002 |
| STY-003 | A verb-plus-particle pairing appears | all prose | parser · `no-phrasal-verbs` | see corpus/style/economy.md#STOW-STY-003 |
| STY-004 | Recurring content or terminology across the text | all prose | heuristic · `consistent-wording-for-recurring-content` | see corpus/style/consistency.md#STOW-STY-004 |

STY-004 carries a recorded conflict resolution with the presentation layer; the
corpus file states it.

## GEN: general recommendations

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| GEN-001 | A clause boundary where the conjunction `that` could be dropped | all prose | heuristic · `retain-that-conjunction` | see corpus/general-practice.md#STOW-GEN-001 |
| GEN-002 | The preposition `with` appears | all prose | heuristic · `with-ambiguity-check` | see corpus/general-practice.md#STOW-GEN-002 |
| GEN-003 | A pronoun appears | all prose | parser · `approved-and-unambiguous-pronoun` | see corpus/general-practice.md#STOW-GEN-003 |
| GEN-004 | The pronoun `this` appears | all prose | heuristic · `this-referent-clarity` | see corpus/general-practice.md#STOW-GEN-004 |
| GEN-005 | A word resembling a cross-language cognate appears | all prose | semantic-review · `false-friend-check` | see corpus/general-practice.md#STOW-GEN-005 |
| GEN-006 | A Latin-derived abbreviation appears | all prose | deterministic · `no-latin-abbreviations` | see corpus/general-practice.md#STOW-GEN-006 |
| GEN-007 | Gendered or non-inclusive wording appears | all prose | deterministic · `gender-neutral-language` | see corpus/general-practice.md#STOW-GEN-007 |
| GEN-008 | A possessive construction appears | all prose | heuristic · `possessive-correctness` | see corpus/general-practice.md#STOW-GEN-008 |
