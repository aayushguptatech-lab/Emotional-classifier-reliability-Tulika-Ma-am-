# The Valley of Fear — Corpus README

## 1. Overview

This directory contains the **frozen corpus representation of Arthur Conan Doyle's _The Valley of Fear_** prepared for the *Tulika Ma'am Paper* research project on reliability-aware, language-specialized emotion classification in historical literary corpora.

The corpus was constructed through this auditable pipeline:

```text
SOURCE WEBSITE
      ↓
RAW NOVEL (immutable)
      ↓
CLEAN NOVEL
      ↓
DIALOGUE EXTRACTION
      ↓
SPEAKER TURN
      ↓
SENTENCE SEGMENTATION
      ↓
previous / current / next
      ↓
MASTER LITERARY CORPUS
      ↓
HUMAN ANNOTATION + DIAGNOSTIC SET
      ↓
GOLD CORPUS
```

For this text, the **corpus-building / master-corpus stage is complete and structurally frozen**.

> **Important:** "Frozen" means the VOF literary master corpus has passed its final structural audit. It does **not** mean that human emotion annotation, pragmatic annotation, model evaluation, or the entire research paper is complete.

---

## 2. Text Identity

| Field | Value |
|---|---|
| Text ID | `VOF` |
| Title | *The Valley of Fear* |
| Author | Arthur Conan Doyle |
| Publication year | 1915 |
| Language | English |
| Source platform | Project Gutenberg |
| Source identifier | Project Gutenberg eBook #3289 |
| Source page | https://www.gutenberg.org/ebooks/3289 |
| Plain-text source | https://www.gutenberg.org/cache/epub/3289/pg3289.txt |
| Raw filename | `the_valley_of_fear_raw.txt` |
| Clean filename | `the_valley_of_fear_clean.txt` |
| Frozen master | `the_valley_of_fear_master_final.csv` |

---

## 3. Final Corpus Statistics

| Measure | Final value |
|---|---:|
| Raw characters | 340,174 |
| Raw words | 60,861 |
| Raw lines | 14,548 |
| Clean characters | 320,464 |
| Clean words | 57,814 |
| Clean lines | 13,771 |
| Reconstructed dialogue turns | 1,267 |
| Final sentence rows | 2,872 |
| High-confidence sentence rows | 659 |
| Review-confidence sentence rows | 2,213 |
| Unresolved source-location rows | 52 |
| Duplicate sentence IDs | 0 |
| Empty critical fields | 0 |

---

## 4. Directory Structure

Relevant VOF files:

```text
data/
├── raw/
│   └── english/
│       └── the_valley_of_fear_raw.txt
│
├── cleaned/
│   └── english/
│       └── the_valley_of_fear_clean.txt
│
├── extracted/
│   └── english/
│       ├── the_valley_of_fear_dialogue_v2.csv
│       ├── the_valley_of_fear_dialogue_v4.csv
│       ├── the_valley_of_fear_dialogue_v5.csv
│       ├── the_valley_of_fear_dialogue_v6.csv
│       ├── the_valley_of_fear_sentence_v1.csv
│       └── the_valley_of_fear_sentence_v2.csv
│
└── final/
    └── english/
        └── the_valley_of_fear_master_final.csv
```

Audit/debug artifacts were also produced during development and are retained for traceability.

---

## 5. Source Acquisition

The source was acquired from Project Gutenberg eBook #3289:

```text
https://www.gutenberg.org/ebooks/3289
```

Plain text:

```text
https://www.gutenberg.org/cache/epub/3289/pg3289.txt
```

Acquisition script:

```text
src/01_download_english.py
```

The acquisition script verified that the download was non-empty and contained identifying text for *The Valley of Fear*.

### Raw source verification

- Characters: **340,174**
- Words: **60,861**
- Lines: **14,548**

The raw source is treated as **immutable**.

---

## 6. Metadata and Provenance

The text is registered in:

```text
metadata/english_texts.csv
```

with the following metadata:

```csv
text_id,title,author,publication_year,language,source_platform,source_id,source_url,raw_filename,verification_status
VOF,The Valley of Fear,Arthur Conan Doyle,1915,English,Project Gutenberg,3289,https://www.gutenberg.org/ebooks/3289,the_valley_of_fear_raw.txt,verified
```

Acquisition is recorded in:

```text
logs/provenance_log.csv
```

The provenance record records source, files, status, and verification notes.

---

## 7. Cleaning

Cleaner:

```text
src/03_clean_english.py
```

The Gutenberg wrapper was removed using the exact start/end markers:

```text
*** START OF THE PROJECT GUTENBERG EBOOK THE VALLEY OF FEAR ***
```

```text
*** END OF THE PROJECT GUTENBERG EBOOK THE VALLEY OF FEAR ***
```

### Raw → clean

| Measure | Raw | Clean |
|---|---:|---:|
| Characters | 340,174 | 320,464 |
| Words | 60,861 | 57,814 |
| Lines | 14,548 | 13,771 |

The cleaning process removes Gutenberg boilerplate/license material while preserving the novel.

No modernization was performed. Original spelling, punctuation, quotation marks, literary wording, and chapter structure were retained.

Physical line wrapping remains in the clean source and is handled programmatically.

---

## 8. Dialogue Extraction

The primary analysis unit is a **speaker-attributed sentence**, so dialogue turns were reconstructed before sentence segmentation.

Architecture:

```text
clean novel
    ↓
quotation spans
    ↓
dialogue candidates
    ↓
speaker recovery
    ↓
speaker turns
    ↓
sentence segmentation
```

### Dialogue pattern inspection

The clean source contained:

- ASCII double quotes: **0**
- left curly quotes `“`: **1,592**
- right curly quotes `”`: **1,554**
- detected curly quoted spans: **1,554**
- multi-line quotation spans: **690**
- quotation spans followed by common attribution verbs: **322**

The inspection demonstrated that quotation marks alone cannot safely define every speaker turn.

---

## 9. Speaker-Turn Reconstruction Rules

The VOF pipeline follows these rules:

1. A quotation span is a dialogue candidate.
2. Explicit speaker attribution is recovered where possible.
3. Attribution may occur after or before a quotation.
4. Quoted material split by attribution is reconstructed where appropriate.
5. Long speeches remain one turn even when they contain multiple sentences.
6. Multi-paragraph speeches remain one turn.
7. A physical newline is not automatically a turn boundary.
8. `Unknown` is legitimate when a speaker cannot be recovered reliably.
9. `extraction_confidence` is kept separate from the speaker field.
10. Sentence segmentation happens only after turn reconstruction.

---

## 10. Extraction Development History

### V2

```text
data/extracted/english/the_valley_of_fear_dialogue_v2.csv
```

- Quotation spans: **1,554**
- Reconstructed turns: **1,266**
- Known speakers: **299**
- Unknown speakers: **967**
- High confidence: **299**
- Review confidence: **967**

### V3

A stricter replacement attempt collapsed the extraction to only **45 turns**. This was clearly over-restrictive.

**V3 is therefore not used as the corpus.**

### V4

V4 preserved the V2 turn structure while improving speaker recovery:

- Turns: **1,266**
- Known speakers: **281**
- Unknown speakers: **985**
- High confidence: **281**
- Review confidence: **985**

### V5

V5 normalized obvious attribution modifiers while preserving turn structure:

- Turns: **1,266**
- Known speakers: **272**
- Unknown/review: **994**

Examples of normalization:

```text
Holmes in his most → Holmes
White Mason cordially → White Mason
McMurdo in cold fury → McMurdo
Baldwin with an oath → Baldwin
McGinty with an oath → McGinty
```

Clearly fragmentary candidates were moved to `Unknown`/review instead of being retained as false speaker names.

---

## 11. Internal Speaker-Boundary Audit

The boundary audit identified **23 potential internal speaker-boundary cases**.

Manual review resulted in:

- **20 KEEP**
- **3 REPAIR**

Repairs:

```text
VOF_T00431 → the inspector
VOF_T00433 → White Mason
```

and:

```text
VOF_T01179
    ↓
VOF_T01179_A → McGinty
VOF_T01179_B → McMurdo
```

The two child turns retain:

```text
parent_turn_id = VOF_T01179
```

Final reconstructed dialogue turns:

**1,267**

Nested/reported quotations were not automatically split when they remained part of a continuous outer speaker's speech.

---

## 12. Sentence Segmentation

Script:

```text
src/21_segment_v6_sentences_english.py
```

Output:

```text
data/extracted/english/the_valley_of_fear_sentence_v1.csv
```

Results:

- Dialogue turns: **1,267**
- Sentence rows: **2,872**
- Average sentences/turn: **2.27**
- Maximum sentences/turn: **40**
- Turns with review flags: **123**

The segmentation protects common abbreviations such as:

```text
mr. mrs. ms. dr. prof. sr. jr. st. no. messrs. etc. i.e. e.g.
```

Sentence IDs preserve their parent turn:

```text
VOF_T00001_S01
VOF_T00001_S02
...
```

---

## 13. Previous / Current / Next Context

Context generation produced:

```text
data/extracted/english/the_valley_of_fear_sentence_v2.csv
```

Every sentence can have:

```text
previous_text
current_text
next_text
```

### Critical rule

> **Context never crosses a speaker-turn boundary.**

Thus, previous/next context is drawn only from the same `turn_id`.

The context audit confirmed the relationships and passed.

---

## 14. Structural Sentence Audit

The structural audit confirmed:

- Sentence rows: **2,872**
- Unique turn IDs: **1,267**
- Unique sentence IDs: **2,872**
- Empty `current_text`: **0**
- Empty `turn_id`: **0**
- Empty `sentence_id`: **0**
- Empty `speaker`: **0**
- Duplicate sentence IDs: **0**
- Turns with zero sentences: **0**
- Sentence-numbering problems: **0**
- All V6 turns represented: **1,267 / 1,267**

**Structural audit: PASSED**

---

## 15. Extraction Confidence

The final sentence corpus contains:

```text
high   = 659
review = 2,213
```

Confidence is retained because speaker recovery is not equally certain for every extracted turn.

`Unknown` is retained rather than silently deleting uncertain material.

This supports the project's reliability-aware design.

---

## 16. Chapter Metadata

Final chapter labels use normalized forms:

```text
PART I — Chapter I
PART I — Chapter II
PART I — Chapter III
PART I — Chapter IV
PART I — Chapter V
PART I — Chapter VI
PART I — Chapter VII

PART II — Chapter I
PART II — Chapter II
PART II — Chapter III
PART II — Chapter IV
PART II — Chapter V
PART II — Chapter VI
PART II — Chapter VII
```

During the final audit, one malformed intermediate label was found:

```text
PART II—The Scowrers — Chapter VII—The Trapping of Birdy Edwards
```

It was normalized to:

```text
PART II — Chapter VII
```

Exactly **12 rows** required this label-only correction.

No sentence text, speaker assignment, or context value was changed.

---

## 17. Source-Location Matching

The robust master-building stage attempted to locate sentence text within the clean source.

Results:

- Total sentence rows: **2,872**
- Unresolved source-location rows: **52**

Evidence methods included:

```text
full
beginning_5
beginning_8
beginning_12
ending_5
ending_8
ending_12
unresolved
```

The 52 unresolved cases are source-position matching limitations. They are **not missing corpus rows**.

The final structural audit passed while retaining these cases.

---

## 18. Frozen Master

Final file:

```text
data/final/english/the_valley_of_fear_master_final.csv
```

This is the file to use for downstream annotation and analysis.

The master contains the sentence-level literary corpus plus its turn/context/metadata fields.

The frozen master should be treated as **immutable**.

If an error is discovered later, create a new documented version rather than silently modifying the frozen file.

---

## 19. Final Freeze Audit

The final audit was run against:

```text
data/final/english/the_valley_of_fear_master_final.csv
```

The audit reported:

```text
Rows: 2,872

Schema:
PASS

Sentence IDs:
PASS — all unique

Sentence numbering:
PASS

Previous/next context:
PASS

T01179 repair:
PASS

Extraction-confidence values:
PASS

Chapter-label consistency:
PASS

Unresolved source locations:
52

Metadata consistency:
PASS

FINAL FREEZE VERDICT
====================
STRUCTURAL FREEZE AUDIT PASSED
```

Freeze report:

```text
data/final/english/the_valley_of_fear_freeze_report_final.csv
```

### Final status

**THE VALLEY OF FEAR — STRUCTURALLY FROZEN**

---

## 20. What "Completed" Means

### Completed

- Raw source acquisition
- Source verification
- Provenance registration
- Cleaning
- Dialogue candidate extraction
- Speaker-turn reconstruction
- Speaker recovery
- Internal boundary review
- Boundary repair
- Sentence segmentation
- Stable sentence IDs
- Previous/current/next context
- Chapter metadata
- Structural audits
- Final freeze audit

### Not yet completed

These belong to later research stages:

1. Human emotion annotation
2. Pragmatic annotation
3. Independent double annotation
4. Human-human inter-annotator agreement
5. Adjudication
6. Diagnostic challenge-set construction
7. Confidence-stratified validation
8. Model prediction generation
9. Human-model agreement
10. Isolated-sentence vs context-window experiments
11. Final gold corpus

Therefore:

```text
VOF literary corpus construction → COMPLETE
VOF structural freeze            → COMPLETE
Entire research study            → NOT COMPLETE
```

---

## 21. Later Annotation Layer

The broader research specification defines seven primary emotion classes:

```text
Anger
Disgust
Fear
Joy
Sadness
Surprise
Neutral
```

The later pragmatic annotation layer is intended to record phenomena such as:

- cue present
- cue
- negated/cancelled
- emotion asserted
- attributed
- mentioned/evoked
- resolution

The frozen literary corpus itself should not be retroactively modified to encode those labels.

---

## 22. Diagnostic Phenomena

The broader methodology emphasizes cases such as:

```text
“I fear him.”
“I don’t fear him.”
“Never fear.”
“Fear is a powerful weapon.”
“She was afraid.”
“There’s my pistol.”
“He slammed the door.”
```

These illustrate why emotion classification cannot safely be reduced to keyword matching.

Negation, attribution, mention/evocation, idiomatic usage, charged objects, and implicit emotion require contextual interpretation.

The VOF corpus preserves sentence, turn, speaker, and context structure for this later work.

---

## 23. Reproducibility Principles

The VOF corpus follows these principles:

### Raw source first
The downloaded source is preserved before cleaning.

### No modernization
Historical spelling and punctuation are not modernized.

### Stable IDs
IDs are stable and are not reused.

### Turn hierarchy
Sentence IDs retain their parent dialogue-turn relationship.

### Turn-bounded context
Previous/next context never crosses a speaker boundary.

### Explicit uncertainty
`Unknown` and `review` remain visible.

### Audits do not silently mutate data
Audit scripts inspect rather than silently repair the corpus.

### Versioned finalization
The frozen master is written separately from intermediate versions.

---

## 24. Important Intermediate Files

```text
data/raw/english/the_valley_of_fear_raw.txt

data/cleaned/english/the_valley_of_fear_clean.txt

data/extracted/english/the_valley_of_fear_dialogue_v2.csv
data/extracted/english/the_valley_of_fear_dialogue_v4.csv
data/extracted/english/the_valley_of_fear_dialogue_v5.csv
data/extracted/english/the_valley_of_fear_dialogue_v6.csv

data/extracted/english/the_valley_of_fear_sentence_v1.csv
data/extracted/english/the_valley_of_fear_sentence_v2.csv

data/final/english/the_valley_of_fear_master_v2.csv
data/final/english/the_valley_of_fear_master_unresolved.csv

data/final/english/the_valley_of_fear_master_final.csv
data/final/english/the_valley_of_fear_freeze_report_final.csv
```

Intermediate files are development/audit artifacts. The final downstream file is:

```text
the_valley_of_fear_master_final.csv
```

---

## 25. Recommended Downstream Use

For annotation, diagnostics, and model evaluation, use:

```text
data/final/english/the_valley_of_fear_master_final.csv
```

Do not substitute earlier dialogue or sentence versions for the frozen master.

The frozen VOF master is now the stable literary-corpus layer for the next stages of the project.

---

## 26. Final Summary

| Item | Status |
|---|---|
| Text | *The Valley of Fear* |
| Author | Arthur Conan Doyle |
| Publication year | 1915 |
| Language | English |
| Source | Project Gutenberg #3289 |
| Final dialogue turns | 1,267 |
| Final sentence rows | 2,872 |
| High-confidence rows | 659 |
| Review-confidence rows | 2,213 |
| Unresolved source locations | 52 |
| Structural freeze | **PASSED** |
| Frozen master | `the_valley_of_fear_master_final.csv` |
| Human emotion annotation | Pending |
| Gold corpus | Pending |
| Model evaluation | Pending |

**Final corpus status: FROZEN FOR THE LITERARY CORPUS-CONSTRUCTION STAGE.**
