import csv
import re
from pathlib import Path


SENTENCE_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v2.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_unmatched_diagnosis.csv"
)


def normalize(text):
    """
    Normalize only whitespace for source comparison.
    Original corpus text is NOT modified.
    """
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact(text):
    """
    More aggressive comparison form used ONLY for diagnosis.
    Removes whitespace and normalizes curly/straight apostrophes.
    """
    text = normalize(text)

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", "", text).lower()


with SENTENCE_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)


clean_text = CLEAN_FILE.read_text(encoding="utf-8")

normalized_clean = normalize(clean_text)
compact_clean = compact(clean_text)

diagnosis_rows = []

for row in rows:

    sentence = normalize(row["current_text"])

    # First comparison: normal whitespace normalization.
    normal_found = normalized_clean.find(sentence) != -1

    # Second comparison: ignore whitespace and common quote/dash differences.
    compact_sentence = compact(sentence)
    compact_found = compact_clean.find(compact_sentence) != -1

    if not normal_found:
        if compact_found:
            reason = "found_after_aggressive_normalization"
        else:
            reason = "not_found_even_after_aggressive_normalization"

        diagnosis_rows.append({
            "text_id": row["text_id"],
            "turn_id": row["turn_id"],
            "sentence_id": row["sentence_id"],
            "speaker": row["speaker"],
            "current_text": row["current_text"],
            "normal_match": normal_found,
            "aggressive_match": compact_found,
            "diagnosis": reason,
        })


fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "normal_match",
    "aggressive_match",
    "diagnosis",
]

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(diagnosis_rows)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

normal_count = sum(
    row["normal_match"] is True
    for row in diagnosis_rows
)

aggressive_count = sum(
    row["aggressive_match"] is True
    for row in diagnosis_rows
)

not_found_count = sum(
    row["aggressive_match"] is False
    for row in diagnosis_rows
)


print("VOF UNMATCHED-SENTENCE DIAGNOSIS")
print("================================")
print()
print(f"Total sentence rows:                 {len(rows):,}")
print(f"Currently unmatched:                 {len(diagnosis_rows):,}")
print(f"Recovered by aggressive normalization: {aggressive_count:,}")
print(f"Still not found:                     {not_found_count:,}")

print()
print("FIRST 30 DIAGNOSIS CASES")
print("------------------------")

for row in diagnosis_rows[:30]:

    text = row["current_text"]

    if len(text) > 180:
        text = text[:180] + "..."

    print()
    print(
        f"{row['sentence_id']} | "
        f"{row['speaker']} | "
        f"{row['diagnosis']}"
    )
    print(f"  {text}")

print()
print(f"Full diagnosis saved to:")
print(f"{OUTPUT_FILE}")

print()
print("IMPORTANT:")
print("- No corpus file was modified.")
print("- sentence_v2.csv was NOT modified.")
print("- This is diagnosis only.")