# Project status

Research corpus construction for Tulika Ma'am. This document separates
**completed/frozen**, **provisional**, **experimental**, and **remaining**
work. It does not replace validation files under `data/final/`.

Last synchronized: 2026-09-29.

## Methodological rules in force

- Never invent speaker identities.
- Never silently modify canonical source text.
- Preserve `Unknown` / review cases when attribution is uncertain.
- Do not delete useful experimental artifacts merely because they are imperfect.
- Distinguish frozen files from experimental/provisional files.
- Do not overwrite validated English results with experimental results.
- Do not fabricate missing data.
- Do not call a corpus final/validated if it has known contamination.

## Completed / frozen

### English dialogue-turn corpora

The English phase is frozen at the current reproducible stage.

| Novel | Final CSV | Turns | Known | Unknown | Validation |
|---|---|---:|---:|---:|---|
| *The Valley of Fear* (Arthur Conan Doyle) | `data/final/english/the_valley_of_fear_final_corpus.csv` | 1267 | 277 | 990 | `the_valley_of_fear_final_validation.txt` |
| *The Man Who Was Thursday* (G. K. Chesterton) | `data/final/english/the_man_who_was_thursday_final_corpus.csv` | 870 | 487 | 383 | `the_man_who_was_thursday_final_validation.txt` |
| *The Old Wives' Tale* (Arnold Bennett) | `data/final/english/the_old_wives_tale_final_corpus.csv` | 679 | 637 | 42 | `the_old_wives_tale_final_validation.txt` |

Combined audit: `data/final/english/english_three_novel_final_audit.txt`

English total: **2816 turns**, **1401 known**, **1415 Unknown**.

Raw and cleaned English sources are present under `data/raw/english/` and
`data/cleaned/english/`. Intermediate extraction/audit CSVs under
`data/extracted/english/` are retained for reproducibility.

An earlier VOF sentence-level freeze (`the_valley_of_fear_master_final.csv`)
is also retained. It is not a substitute for the current 1267-turn dialogue
corpus.

### Paper analysis snapshot (EMORE@ACII2026)

Camera-ready notebook, figures, and three consensus-annotation CSVs remain
in the repository root. Those files document a **different, smaller**
evaluation snapshot (historical claim: VOF 172 turns / Gaban 1044 turns) and
must not overwrite the frozen literary corpora above.

## Provisional

### Gaban — प्रेमचंद

- Source retrieval completed for 5 chapters (`data/raw/hindi/gaban/`).
- Cleaned source: `data/cleaned/hindi/gaban_clean.txt`.
- Current snapshot: `data/final/hindi/gaban_dialogue_final.csv` (1010 turns).
- Review: `data/final/hindi/gaban_dialogue_review.csv`.
- Validation: `data/final/hindi/gaban_final_validation.txt`.
- **Not frozen.** Narrative contamination remains.
- Earlier v8/v9 and segmented snapshots are retained as audit history.

## Experimental

### Kankal — जयशंकर प्रसाद

- 31 source parts retrieved: `data/raw/hindi/kankal/`.
- Experimental output: `data/final/hindi/kankal_dialogue_final.csv` (51 turns).
- The 51-turn file is **not** a validated corpus.

### Titli — जयशंकर प्रसाद

- 28 Wikisource pages retrieved; pages 2.6, 2.7, 2.8 returned 404.
- Raw evidence: `data/raw/hindi/titli/`.
- Experimental candidates: `data/final/hindi/titli_dialogue_candidates.csv` (419).
- **Not** a validated corpus.

### VOF experimental reconstruction (08b)

On 2026-09-29, uncommitted working copies of

- `data/extracted/english/the_valley_of_fear_dialogue_v2.csv`
- `data/extracted/english/the_valley_of_fear_dialogue_v2_review.csv`

were 1554-row experimental outputs from `src/08b_reconstruct_dialogue_v2_english.py`,
which would have overwritten the historical 1267-row V2 artifacts. Those
experimental copies were saved as:

- `data/extracted/english/the_valley_of_fear_dialogue_v2_experimental_08b.csv`
- `data/extracted/english/the_valley_of_fear_dialogue_v2_review_experimental_08b.csv`

The historical V2 files were restored from git. Do not rerun `08b` against
the historical V2 filenames.

## Remaining work

1. **Do not begin by expanding Hindi coverage.** First stabilize Gaban:
   reduce narrative contamination, preserve Unknown where attribution is
   uncertain, and produce a reviewed (not guessed) Gaban dialogue corpus.
2. Rebuild Kankal extraction against the 31 retrieved parts with
   conservative speaker rules. Do not treat 51 turns as complete.
3. Resolve Titli source gaps (Wikisource 2.6 / 2.7 / 2.8 = 404) and only
   then validate candidates.
4. Keep English frozen unless a documented, auditable defect is found in
   the frozen files themselves.
5. Optional later: reconcile the paper's 172-turn VOF / 1044-turn Gaban
   claims with the current reproducible corpora. The 172-turn figure has no
   recovered selection rule in this repository.

## Script numbering collisions

Several `src/` scripts share numeric prefixes because English VOF scripts
(`01`–`39`) and later MWT/OWT/Hindi scripts were numbered independently.
Examples: `09_recover_speakers_english.py` vs `09_build_mwt_corpus.py`;
`21_segment_v6_sentences_english.py` vs `21_build_kankal_hindi.py`.
Filenames were **not** mass-renamed, to preserve research history.

## Files intentionally retained

- All `data/raw/`, `data/cleaned/`, `data/extracted/`, `data/final/` research
  artifacts, including imperfect Hindi snapshots and duplicate raw copies
  (`gaban_chapter_*.html.txt`, `titli_001.html`).
- Root paper notebook, figures, and annotation CSVs.
- Concatenated script/inventory dumps under `reports/archives/`.

## Files excluded from GitHub

- Virtualenv (`.venv/`), editor caches (`.kilo/`, `.vscode/`, `.idea/`).
- Bytecode, pytest/mypy caches, `.env`, OS junk.
- No API keys, tokens, or credentials were found in the working tree.
