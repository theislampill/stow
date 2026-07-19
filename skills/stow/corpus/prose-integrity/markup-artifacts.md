## Hallucinated Markup Artifacts

When AI generates wikitext, it sometimes hallucinates citation markup from its training data. These are 100% confidence indicators of unedited AI output:

| Artifact | Origin |
|----------|--------|
| `oaicite` | OpenAI ChatGPT citation placeholder |
| `contentReference` | OpenAI internal reference tag |
| `grok_card` | xAI Grok citation tag |
| `attributableIndex` | AI attribution tracking artifact |
| `turn0search0` | ChatGPT search result placeholder |

Any occurrence of these strings in wikitext means the text was pasted from an AI tool without editing. Zero tolerance.
