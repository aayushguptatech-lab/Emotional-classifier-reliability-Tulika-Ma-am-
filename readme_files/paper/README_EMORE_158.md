# Emotion Classifier Reliability Across Time and Language

A controlled, human-validated study of emotion-classifier reliability under temporal (historical English) and cross-lingual (historical Hindi) distribution shift.

## Citation

```bibtex
@inproceedings{sharma2026emotion,
  title     = {Emotion Classifier Reliability Across Time and Language},
  author    = {Sharma, Tulika},
  booktitle = {Proceedings of the EMORE Workshop at the International Conference
               on Affective Computing and Intelligent Interaction Workshops (ACIIW)},
  year      = {2026},
  publisher = {IEEE},
  note      = {Paper 158}
}
```

## Overview

The study uses a two-arm design.

- **Primary model:** [`tabularisai/multilingual-sentiment-analysis`](https://huggingface.co/tabularisai/multilingual-sentiment-analysis) (XLM-RoBERTa), applied to **both** languages.
- **Baseline:** [`j-hartmann/emotion-english-distilroberta-base`](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base), English-only DistilRoBERTa.

Two corpora of literary dialogue provide the shifted distributions:

- **English:** Arthur Conan Doyle, *The Valley of Fear* (1915) — 172 dialogue turns, sourced from Project Gutenberg.
- **Hindi:** Premchand, *Gaban* (1936) — 1044 dialogue turns, sourced from Hindi Samay (hindisamay.com).

**Headline finding — surface-lexical over-prediction.** Emotion keywords appearing in pragmatically neutral lines trigger spurious non-neutral labels. A line that merely *mentions* fear is classified as fearful, regardless of its actual pragmatic force. This failure mode recurs across both the temporal and the cross-lingual shift, and it is the dominant source of disagreement with human annotators in both.

## Repository contents

**Notebook**

- `EMORE_158_Analysis_Code.ipynb` — the full analysis, from corpus acquisition through prediction, reliability validation, and figure export. Stored outputs are included, so the results can be read without re-running.

**Consensus annotation data** (the human ground truth; these must be supplied — the notebook does not regenerate them)

- `manual_annotations_50turns.csv` — English, baseline arm. 50 turns selected for the j-hartmann evaluation. Columns: `turn_idx`, `manual_label`.
- `english_tab_validation_annotated.csv` — English, multilingual arm. 50 turns selected for the tabularisai evaluation. Columns: `turn_idx`, `text`, `human_label`.
- `gaban_validation_annotated.csv` — Hindi. 50 turns from *Gaban*. Columns: `turn_id`, `text`, `human_label`.

**Generated outputs** (produced by a run; included here for reference)

- `fig_confusion_matrices.pdf` — main-paper Figure 2.
- `fig_confidence_decay.pdf` — supplementary figure.
- `fig_english_distribution.pdf`, `fig_hindi_distribution.pdf` — emotion distributions (Section 6).

A run also regenerates the intermediate prediction files (`english_tab_pred.csv`, `gaban_pred.csv`, `validation_summary.csv`, and the corpus turn tables), which are not checked in.

## Requirements

Python 3 with:

```
transformers
torch
pandas
scikit-learn
matplotlib
numpy
requests
beautifulsoup4
```

Runs on **CPU in a few minutes**. No GPU required. There is **no training or fine-tuning** — inference only, using the two pretrained checkpoints above.

## How to run

The notebook acquires both source texts over the network at runtime (Project Gutenberg for the English novel, hindisamay.com for the Hindi chapters). The three consensus-annotation CSVs are the human labels and cannot be regenerated, so they must be supplied by hand.

**Colab (as used for the paper)**

1. Upload `EMORE_158_Analysis_Code.ipynb` and the three annotation CSVs.
2. **Runtime > Run all.**

**Local**

1. `pip install transformers torch pandas scikit-learn matplotlib numpy requests beautifulsoup4`
2. Place the three annotation CSVs in the working directory alongside the notebook.
3. Run the notebook top to bottom.

Prediction is deterministic: both models run in `eval` mode with argmax decoding and no sampling, so a given input yields the same label on every run.

## What it produces

| Notebook section | Artifact | Paper |
|---|---|---|
| Section 5 (5.4) | `validation_summary.csv` — the three-way Cohen's kappa table | Main paper, Table I |
| Section 5.5 | `fig_confusion_matrices.pdf` — per-configuration confusion matrices | Main paper, Figure 2 |
| Section 5.6 | `fig_confidence_decay.pdf` — confidence characterization outside the top-50 probe | Supplementary figure |

## Key results

| Model / Language | Cohen's kappa | Agreement | Over-prediction |
|---|---|---|---|
| j-hartmann / English | 0.803 | 0.84 | 0.12 |
| tabularisai / English | 0.276 | 0.38 | 0.34 |
| tabularisai / Hindi | 0.141 | 0.22 | 0.52 |

Corpus neutral rates: **English 50.6%**, **Hindi 49.0%**.

Reliability degrades sharply as the primary model moves away from the English-only baseline condition, and the over-prediction rate rises in step with it — consistent with the surface-lexical failure described above.

## Data and provenance

Both source texts are in the **public domain**. *The Valley of Fear* (1915) is distributed by Project Gutenberg. *Gaban* (1936) is by Premchand, who died in 1936; the text is sourced from Hindi Samay (hindisamay.com).

The annotations are **consensus labels produced by native speakers** of the respective language. Each unit was labeled **in isolation** — annotators saw only the text the model sees, with no surrounding narrative context. This matters for interpreting the kappa values: the human labels are subject to the same context poverty as the model's inputs, so the disagreement measured is not an artifact of humans having more context than the classifier.

## License

MIT. See [LICENSE](LICENSE).

## Contact

Tulika Sharma
Computer Science and Engineering, PSIT, Kanpur, India
stulika029@gmail.com
