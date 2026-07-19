# Controlled-technical writing profile — application reference

This reference is compressed application guidance for the controlled-technical
writing profile: **when and where** each rule fires, **which output region** it
governs, **how STOW checks it**, and a link to the corpus file that holds the
full normative text. It does not restate the rules themselves — read the linked
corpus file for the wording that governs.

**Guided, not conformant.** This profile is *guided*. STOW applies the checks
below as best-effort shaping of prose. Passing them is not a claim of full
conformance to any controlled-language standard, and it does not certify the
output against the external standard the rules trace to. Treat a clean pass as
"shaped toward the controlled-technical rules", not "verified compliant".

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

## WRD — words

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| WRD-001 | A content word appears in prose | all prose | semantic-review · `approved-word-lookup` | see corpus/words/stow-wrd-001.md |
| WRD-002 | An approved word is used in some part of speech | all prose | parser · `pos-matches-dictionary` | see corpus/words/stow-wrd-002.md |
| WRD-003 | An approved word carries a particular sense | all prose | semantic-review · `approved-sense-only` | see corpus/words/stow-wrd-003.md |
| WRD-004 | An inflected verb or adjective form appears | all prose | parser · `approved-inflection-only` | see corpus/words/stow-wrd-004.md |
| WRD-005 | A non-dictionary word appears | procedural or descriptive prose | semantic-review · `technical-noun-category-membership` | see corpus/words/stow-wrd-005.md |
| WRD-006 | An unapproved word appears | all prose | semantic-review · `technical-noun-context-check` | see corpus/words/stow-wrd-006.md |
| WRD-007 | A technical-noun token is functioning as a verb | all prose | parser · `no-technical-noun-as-verb` | see corpus/words/stow-wrd-007.md |
| WRD-008 | A technical noun is selected where a company, industry, or field term exists | all prose | heuristic · `company-term-preferred` | see corpus/words/stow-wrd-008.md |
| WRD-009 | A coined or multi-word technical noun appears | all prose | deterministic · `technical-noun-max-3-words` (limit 3) | see corpus/words/stow-wrd-009.md |
| WRD-010 | A candidate technical noun looks regional, slang, or jargon | all prose | semantic-review · `no-slang-or-jargon-noun` | see corpus/words/stow-wrd-010.md |
| WRD-011 | Two or more synonymous nouns name one referent across the text | all prose | heuristic · `consistent-term-per-referent` | see corpus/words/stow-wrd-011.md |
| WRD-012 | A non-dictionary verb appears | procedural or descriptive prose | semantic-review · `technical-verb-category-membership` | see corpus/words/stow-wrd-012.md |
| WRD-013 | A technical-verb token is functioning as a noun | all prose | parser · `no-technical-verb-as-noun` | see corpus/words/stow-wrd-013.md |
| WRD-014 | A word has a spelling variant (skips quoted text) | all prose | deterministic · `american-english-spelling` | see corpus/words/stow-wrd-014.md |

WRD-011 and WRD-014 carry recorded conflict resolutions (with the presentation
layer and with protected regions respectively); the corpus file states the
resolution.

## MWN — multi-word nouns

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| MWN-001 | A noun phrase built from stacked nouns or modifiers appears | all prose | parser · `multiword-noun-max-3-words` (limit 3) | see corpus/multiword-nouns/stow-mwn-001.md |
| MWN-002 | A technical noun runs past three words | all prose | heuristic · `long-technical-noun-shorten-or-hyphenate` | see corpus/multiword-nouns/stow-mwn-002.md |

## VRB — verbs, voice, and tense

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| VRB-001 | A verb token appears | all prose | parser · `approved-verb-form-only` | see corpus/verbs/stow-vrb-001.md |
| VRB-002 | A verb carries tense or aspect marking | all prose | parser · `approved-tense-only` | see corpus/verbs/stow-vrb-002.md |
| VRB-003 | A past-participle form appears | all prose | parser · `participle-as-adjective-only` | see corpus/verbs/stow-vrb-003.md |
| VRB-004 | An auxiliary combines with a main verb | all prose | parser · `no-auxiliary-complex-construction` | see corpus/verbs/stow-vrb-004.md |
| VRB-005 | An `-ing` word appears | all prose | parser · `ing-only-as-technical-noun` | see corpus/verbs/stow-vrb-005.md |
| VRB-006 | A clause is in the passive voice | all prose | parser · `active-voice-required-unless-agentless-descriptive` | see corpus/verbs/stow-vrb-006.md |
| VRB-007 | An action is expressed as a noun or other part of speech | all prose | heuristic · `prefer-verb-over-nominalization` | see corpus/verbs/stow-vrb-007.md |

## SEN — sentences, lists, and articles

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| SEN-001 | Each sentence in prose | all prose | semantic-review · `sentence-clarity-heuristic` | see corpus/sentences/stow-sen-001.md |
| SEN-002 | A contraction or a dropped word appears | all prose | deterministic · `no-contractions-no-word-omission` | see corpus/sentences/stow-sen-002.md |
| SEN-003 | A sentence packs complex or enumerated content | all prose | heuristic · `vertical-list-formatting` | see corpus/sentences/stow-sen-003.md |
| SEN-004 | Adjacent sentences share a related topic | all prose | heuristic · `approved-connectors-only` | see corpus/sentences/stow-sen-004.md |
| SEN-005 | A noun or multi-word noun appears without an article or demonstrative | all prose | parser · `article-and-demonstrative-usage` | see corpus/sentences/stow-sen-005.md |

## STY — writing-practice consistency

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| STY-001 | A sentence where a word-for-word swap does not hold | all prose | semantic-review · `rewrite-construction-preserve-meaning` | see corpus/style/stow-sty-001.md |
| STY-002 | An approved word's sense and part of speech in context | all prose | semantic-review · `restricted-meaning-and-pos-check` | see corpus/style/stow-sty-002.md |
| STY-003 | A verb-plus-particle pairing appears | all prose | parser · `no-phrasal-verbs` | see corpus/style/stow-sty-003.md |
| STY-004 | Recurring content or terminology across the text | all prose | heuristic · `consistent-wording-for-recurring-content` | see corpus/style/stow-sty-004.md |

STY-004 carries a recorded conflict resolution with the presentation layer; the
corpus file states it.

## GEN — general recommendations

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| GEN-001 | A clause boundary where the conjunction `that` could be dropped | all prose | heuristic · `retain-that-conjunction` | see corpus/general/stow-gen-001.md |
| GEN-002 | The preposition `with` appears | all prose | heuristic · `with-ambiguity-check` | see corpus/general/stow-gen-002.md |
| GEN-003 | A pronoun appears | all prose | parser · `approved-and-unambiguous-pronoun` | see corpus/general/stow-gen-003.md |
| GEN-004 | The pronoun `this` appears | all prose | heuristic · `this-referent-clarity` | see corpus/general/stow-gen-004.md |
| GEN-005 | A word resembling a cross-language cognate appears | all prose | semantic-review · `false-friend-check` | see corpus/general/stow-gen-005.md |
| GEN-006 | A Latin-derived abbreviation appears | all prose | deterministic · `no-latin-abbreviations` | see corpus/general/stow-gen-006.md |
| GEN-007 | Gendered or non-inclusive wording appears | all prose | deterministic · `gender-neutral-language` | see corpus/general/stow-gen-007.md |
| GEN-008 | A possessive construction appears | all prose | heuristic · `possessive-correctness` | see corpus/general/stow-gen-008.md |
