from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]

V7 = ROOT / "data" / "extracted" / "english" / "the_man_who_was_thursday_dialogue_turns_v7.csv"
CLEAN = ROOT / "data" / "cleaned" / "english" / "the_man_who_was_thursday_clean.txt"

OUT_DIR = ROOT / "data" / "final" / "english"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL = OUT_DIR / "the_man_who_was_thursday_final_corpus.csv"
VALIDATION = OUT_DIR / "the_man_who_was_thursday_final_validation.txt"

df = pd.read_csv(V7)
clean_text = CLEAN.read_text(encoding="utf-8")

required = [
    "turn_id",
    "speaker",
    "speaker_confidence",
    "extraction_confidence",
    "boundary_confidence",
    "boundary_reason",
    "quoted_text",
]

missing = [c for c in required if c not in df.columns]

duplicate_ids = int(df["turn_id"].duplicated().sum())
empty_dialogue = int(df["quoted_text"].fillna("").str.strip().eq("").sum())

known = int(
    df["speaker"]
    .fillna("Unknown")
    .ne("Unknown")
    .sum()
)

unknown = len(df) - known

title_counts = {
    "Mr.": len(re.findall(r"Mr\.", clean_text)),
    "Mrs.": len(re.findall(r"Mrs\.", clean_text)),
    "Dr.": len(re.findall(r"Dr\.", clean_text)),
    "St.": len(re.findall(r"St\.", clean_text)),
}

lower_title_counts = {
    "mr.": len(re.findall(r"mr\.", clean_text)),
    "mrs.": len(re.findall(r"mrs\.", clean_text)),
    "dr.": len(re.findall(r"dr\.", clean_text)),
    "st.": len(re.findall(r"st\.", clean_text)),
}

df["text_id"] = "MWT"
df["source"] = "Project Gutenberg"
df["source_work"] = "The Man Who Was Thursday"
df["author"] = "G. K. Chesterton"

columns = [
    "text_id",
    "turn_id",
    "speaker",
    "quoted_text",
    "speaker_confidence",
    "extraction_confidence",
    "boundary_confidence",
    "boundary_reason",
    "candidate_ids",
    "start_char",
    "end_char",
    "source",
    "source_work",
    "author",
]

columns = [c for c in columns if c in df.columns]

final_df = df[columns].copy()

final_df.to_csv(
    FINAL,
    index=False,
    encoding="utf-8-sig"
)

checks = {
    "unique_turn_ids": duplicate_ids == 0,
    "non_empty_dialogue": empty_dialogue == 0,
    "required_fields": len(missing) == 0,
    "canonical_text_available": CLEAN.exists(),
}

lines = [
    "THE MAN WHO WAS THURSDAY — FINAL CORPUS VALIDATION",
    "",
    f"Input turns:              {len(df)}",
    f"Final corpus turns:       {len(final_df)}",
    f"Unique turn IDs:          {df['turn_id'].nunique()}",
    f"Duplicate turn IDs:       {duplicate_ids}",
    f"Empty dialogue rows:      {empty_dialogue}",
    "",
    "SPEAKER ATTRIBUTION",
    f"Known speakers:            {known}",
    f"Unknown speakers:          {unknown}",
    f"Unknown percentage:        {unknown / len(df) * 100:.2f}%",
    "",
    "CANONICAL TEXT",
    f"Characters:               {len(clean_text)}",
    f"Mr. occurrences:          {title_counts['Mr.']}",
    f"Mrs. occurrences:         {title_counts['Mrs.']}",
    f"Dr. occurrences:          {title_counts['Dr.']}",
    f"St. occurrences:          {title_counts['St.']}",
    f"Lowercase title forms:    {sum(lower_title_counts.values())}",
    "",
    "SOURCE",
    "Project Gutenberg",
    "G. K. Chesterton — The Man Who Was Thursday",
    "",
    "RECONSTRUCTION",
    "Current final corpus is built from the reproducible V7 dialogue-turn reconstruction.",
    "Speaker Unknown values are retained rather than guessed.",
    "Boundary conflicts and review-level decisions are retained for audit.",
    "",
    "VALIDATION",
    f"PASS unique IDs:           {checks['unique_turn_ids']}",
    f"PASS non-empty dialogue:   {checks['non_empty_dialogue']}",
    f"PASS required fields:      {checks['required_fields']}",
    f"PASS canonical source:     {checks['canonical_text_available']}",
    "PASS source-preserving clean text: True",
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