## Structural and Statistical Patterns

Beyond lexical tells, AI text exhibits measurable structural uniformity that human writing does not.

### Paragraph Length Uniformity
AI aims for visual symmetry. Paragraphs tend toward identical sentence counts (typically 3-4 sentences each). Human writing varies paragraph length based on sub-topic complexity.
- **Threshold:** If all paragraphs in a section are within 15% of each other in word count, the section is likely AI-generated.
- **Exception:** Bulleted lists, tables, and template fields are structurally uniform by design.

### Sentence Length Uniformity (Burstiness)
Human writing alternates between short, punchy sentences and long, clause-heavy ones. AI sentences cluster uniformly around 15-20 words.
- **Threshold:** If a 500-word block contains no sentences under 8 words or over 30 words, it lacks human burstiness.
- **Human baseline:** Human text exhibits 3+ distinct syntactic patterns per 100 words. AI text shows 1.5 or fewer.

### Transition Density
AI over-relies on transition words and adverbial clauses to maintain flow between paragraphs.
- **Threshold:** If more than 30% of paragraphs in an article begin with a transition word or adverbial clause, the text is structurally artificial.

### Opening-Word Repetition
Three or more consecutive paragraphs starting with the same word or phrase pattern indicates mechanical generation. Vary opening words.

### Segmental Entropy
AI maintains flat stylistic consistency from introduction through conclusion. Human writers naturally vary pacing, complexity, and sentence structure between sections.
- **Threshold:** Calculate sentence length variance separately for the introduction, body, and conclusion. If variance differs by less than 10% across all three segments, the text was likely generated as a single pass by AI.
- **Why this matters:** Human introductions tend to be tighter and more declarative. Human body sections are denser with longer sentences. Human conclusions shift register. AI maintains a monotone throughout.

### Contrasting Parallelism Overuse
2025-era models overuse sequential contrasting structures to simulate punchy emphasis:
- "It's not X, it's Y."
- "It's not about X, it's about Y."
- "The issue isn't X. The issue is Y."
- **Threshold:** More than two contrasting parallelisms in a 500-word block.
