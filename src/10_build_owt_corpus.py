from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]

CLEAN = ROOT / "data" / "cleaned" / "english" / "the_old_wives_tale_clean.txt"

EXTRACTED = ROOT / "data" / "extracted" / "english"

OUT_DIR = ROOT / "data" / "final" / "english"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL = OUT_DIR / "the_old_wives_tale_final_corpus.csv"
VALIDATION = OUT_DIR / "the_old_wives_tale_final_validation.txt"


def find_best_turn_file():
    files = sorted(
        EXTRACTED.glob("the_old_wives_tale_dialogue_turns*.csv")
    )

    if not files:
        raise FileNotFoundError(
            "No OWT dialogue-turn CSV found."
        )

    print("Candidate turn files:")
    for f in files:
        print(" ", f.name)

    return files[-1]


INPUT = find_best_turn_file()

df = pd.read_csv(INPUT)

clean_text = CLEAN.read_text(
    encoding="utf-8"
)

required_options = [
    "turn_id",
    "speaker",
]

dialogue_options = [
    "quoted_text",
    "dialogue_text",
    "dialogue",
]

missing_required = [
    c for c in required_options
    if c not in df.columns
]

dialogue_column = next(
    (
        c for c in dialogue_options
        if c in df.columns
    ),
    None
)

if missing_required:
    raise ValueError(
        f"Missing required fields: {missing_required}"
    )

if dialogue_column is None:
    raise ValueError(
        "No dialogue text column found."
    )

df["speaker"] = (
    df["speaker"]
    .fillna("Unknown")
    .astype(str)
    .replace("", "Unknown")
)

df[dialogue_column] = (
    df[dialogue_column]
    .fillna("")
    .astype(str)
)

duplicate_ids = int(
    df["turn_id"].duplicated().sum()
)

empty_dialogue = int(
    df[dialogue_column]
    .str.strip()
    .eq("")
    .sum()
)

known = int(
    df["speaker"]
    .ne("Unknown")
    .sum()
)

unknown = len(df) - known

if "start_char" in df.columns and "end_char" in df.columns:

    invalid_spans = int(
        (
            (pd.to_numeric(df["start_char"], errors="coerce") < 0)
            |
            (
                pd.to_numeric(
                    df["end_char"],
                    errors="coerce"
                )
                >
                len(clean_text)
            )
            |
            (
                pd.to_numeric(
                    df["start_char"],
                    errors="coerce"
                )
                >
                pd.to_numeric(
                    df["end_char"],
                    errors="coerce"
                )
            )
        ).sum()
    )

else:

    invalid_spans = 0


df["text_id"] = "OWT"
df["source"] = "Project Gutenberg"
df["source_work"] = "The Old Wives' Tale"
df["author"] = "Arnold Bennett"

output_columns = [
    "text_id",
    "turn_id",
    "speaker",
    dialogue_column,
    "source",
    "source_work",
    "author",
]

for column in [
    "speaker_confidence",
    "extraction_confidence",
    "boundary_confidence",
    "boundary_reason",
    "candidate_ids",
    "start_char",
    "end_char",
]:
    if column in df.columns:
        output_columns.append(column)

final_df = df[output_columns].copy()

final_df.to_csv(
    FINAL,
    index=False,
    encoding="utf-8-sig"
)

checks = {
    "unique_ids": duplicate_ids == 0,
    "non_empty_dialogue": empty_dialogue == 0,
    "required_fields": len(missing_required) == 0,
    "dialogue_column": dialogue_column is not None,
    "canonical_source": CLEAN.exists(),
    "valid_spans": invalid_spans == 0,
}

lines = [
    "THE OLD WIVES' TALE — FINAL CORPUS VALIDATION",
    "",
    f"Input turn file:          {INPUT.name}",
    f"Input turns:              {len(df)}",
    f"Final corpus turns:       {len(final_df)}",
    f"Unique turn IDs:          {df['turn_id'].nunique()}",
    f"Duplicate turn IDs:       {duplicate_ids}",
    f"Empty dialogue rows:      {empty_dialogue}",
    "",
    "SPEAKER ATTRIBUTION",
    f"Known speakers:           {known}",
    f"Unknown speakers:         {unknown}",
    f"Unknown percentage:       {unknown / len(df) * 100:.2f}%",
    "",
    "CANONICAL TEXT",
    f"Characters:               {len(clean_text)}",
    "",
    "SOURCE",
    "Project Gutenberg",
    "Arnold Bennett — The Old Wives' Tale",
    "",
    "VALIDATION",
    f"PASS unique IDs:          {checks['unique_ids']}",
    f"PASS non-empty dialogue:  {checks['non_empty_dialogue']}",
    f"PASS required fields:     {checks['required_fields']}",
    f"PASS dialogue column:     {checks['dialogue_column']}",
    f"PASS canonical source:    {checks['canonical_source']}",
    f"PASS valid spans:         {checks['valid_spans']}",
    "",
    "NOTE",
    "Existing OWT extraction and audit artifacts are retained.",
    "Unknown speaker values are not guessed or silently replaced.",
    "",
    "FINAL CSV:",
    str(FINAL.relative_to(ROOT)),
    "",
    "VALIDATION:",
    str(VALIDATION.relative_to(ROOT)),
]

VALIDATION.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("\n".join(lines))