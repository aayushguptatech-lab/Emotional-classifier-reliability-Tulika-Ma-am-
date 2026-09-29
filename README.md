# Emotion Classifier Reliability — Literary Dialogue Corpora

Research repository for Tulika Ma'am. This project builds **reproducible literary dialogue corpora** for studying emotion-classifier reliability under historical English and historical Hindi distribution shift.

This README documents **corpus construction**. The original EMORE@ACII2026 paper snapshot is preserved at `readme_files/paper/README_EMORE_158.md` (notebook, figures, and 50-turn annotation files remain in the repository root).

## Methodological rules

- Never invent speaker identities.
- Never silently modify canonical source text.
- Preserve `Unknown` / review cases when attribution is uncertain.
- Do not delete useful experimental artifacts merely because they are imperfect.
- Clearly distinguish frozen files from experimental / provisional files.
- Do not overwrite validated English results with experimental results.
- Do not fabricate missing data.
- Do not call a corpus final/validated if it has known contamination.

## Novels

**English:** *The Valley of Fear* (Arthur Conan Doyle); *The Man Who Was Thursday* (G. K. Chesterton); *The Old Wives' Tale* (Arnold Bennett).

**Hindi:** *गबन* (प्रेमचंद); *कंकाल* (जयशंकर प्रसाद); *तितली* (जयशंकर प्रसाद).

## Repository structure

```text
data/raw/          immutable downloaded sources
data/cleaned/      source-preserving cleaned texts
data/extracted/    intermediate extraction, audit, and review artifacts
data/final/        frozen English corpora; Hindi snapshots (see notes)
src/               acquisition, cleaning, extraction, audit scripts
reports/           project status and archived dumps
metadata/          source catalogue
logs/              provenance log
readme_files/      per-text and paper notes
```

## English corpus status — FROZEN

Unknown speakers are retained rather than guessed.

| Novel | File | Turns | Known | Unknown |
|---|---|---:|---:|---:|
| *The Valley of Fear* | `data/final/english/the_valley_of_fear_final_corpus.csv` | 1267 | 277 | 990 |
| *The Man Who Was Thursday* | `data/final/english/the_man_who_was_thursday_final_corpus.csv` | 870 | 487 | 383 |
| *The Old Wives' Tale* | `data/final/english/the_old_wives_tale_final_corpus.csv` | 679 | 637 | 42 |

Combined audit: `data/final/english/english_three_novel_final_audit.txt`

English total: **2816 turns**, **1401 known**, **1415 Unknown**.

An earlier VOF sentence-level freeze (`the_valley_of_fear_master_final.csv`) is retained. The current frozen *dialogue-turn* corpus is the 1267-row file above.

The paper snapshot historically reported **172** VOF turns. No reproducible selection rule for 172 was recovered. That figure is a documented historical claim, not an undocumented filter.

## Hindi corpus status — NOT FROZEN

Filenames containing `_final` are pipeline snapshots, **not** validated final corpora.

### Gaban — PROVISIONAL

- 5 chapters in `data/raw/hindi/gaban/`; cleaned `data/cleaned/hindi/gaban_clean.txt`
- Snapshot: `data/final/hindi/gaban_dialogue_final.csv` (1010 turns)
- Review: `gaban_dialogue_review.csv`; note: `gaban_final_validation.txt`
- Known limitation: narrative contamination remains.

### Kankal — EXPERIMENTAL

- 31 parts in `data/raw/hindi/kankal/`
- `data/final/hindi/kankal_dialogue_final.csv` (51 turns) is **not** validated.

### Titli — EXPERIMENTAL

- 28 Wikisource pages retrieved; pages **2.6, 2.7, 2.8** returned 404
- Candidates: `data/final/hindi/titli_dialogue_candidates.csv` (419) — **not** validated.

See `data/final/hindi/README.md` and `reports/PROJECT_STATUS.md`.

## Retained experimental / audit artifacts

- English intermediates under `data/extracted/english/`
- VOF rebuilt snapshots (`*_rebuilt.csv`)
- `the_valley_of_fear_dialogue_v2_experimental_08b.csv` (experimental; historical V2 restored)
- Gaban v8/v9 and segmented snapshots
- Concatenated dumps under `reports/archives/`

## Reproducibility

Python 3 with `requirements.txt`. Frozen English producers:

- VOF: `src/08v_build_final_vof_corpus.py`
- MWT: `src/09_build_mwt_corpus.py`
- OWT: `src/10_build_owt_corpus.py`
- Combined audit: `src/11_cross_corpus_final_audit.py`

Hindi builders (`src/13_*` through `src/22_*`) are experimental; running them may overwrite Hindi snapshots. Several `src/` files share numeric prefixes and were not mass-renamed.

## Paper snapshot (EMORE@ACII2026)

`EMORE_158_Analysis_Code.ipynb` plus `manual_annotations_50turns.csv`, `english_tab_validation_annotated.csv`, `gaban_validation_annotated.csv`. That snapshot is **not** the frozen three-novel English corpus.

## License

MIT. See [LICENSE](LICENSE).
