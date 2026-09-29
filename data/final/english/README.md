# English final corpora

This directory holds **frozen** English dialogue-turn corpora and their
validation/audit reports. Do not overwrite these files with experimental
extractions.

## Frozen current corpora

| Novel | File | Turns | Known | Unknown |
|---|---|---:|---:|---:|
| *The Valley of Fear* | `the_valley_of_fear_final_corpus.csv` | 1267 | 277 | 990 |
| *The Man Who Was Thursday* | `the_man_who_was_thursday_final_corpus.csv` | 870 | 487 | 383 |
| *The Old Wives' Tale* | `the_old_wives_tale_final_corpus.csv` | 679 | 637 | 42 |

Combined audit: `english_three_novel_final_audit.txt` (2816 turns; 1401 known; 1415 Unknown).

Unknown speakers are retained. They are not guessed.

## Earlier VOF master freeze

`the_valley_of_fear_master_final.csv` and related freeze reports are retained
as the earlier sentence-level VOF freeze. The **current frozen dialogue-turn
corpus** for cross-novel English work is `the_valley_of_fear_final_corpus.csv`.
