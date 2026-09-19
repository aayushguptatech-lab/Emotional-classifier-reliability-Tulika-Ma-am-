import csv
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_extraction_artifact_audit_v2.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_joined_word_review.csv"
)

REVIEW_PATTERNS = {
    "suspicious_joined_common_words",
    "missing_space_after_comma",
    "missing_space_after_semicolon",
    "missing_space_after_colon",
    "missing_space_after_period",
}

rows = []

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        pattern = row.get("pattern", "").strip()

        if pattern in REVIEW_PATTERNS:
            rows.append(row)


fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "pattern",
    "fragment",
    "start_position",
    "end_position",
    "suggested_spacing",
    "decision",
    "review_notes",
]


OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)


print("JOINED-WORD REVIEW PREPARED")
print("============================")
print(f"Input audit rows:       {sum(1 for _ in open(INPUT_FILE, encoding='utf-8')) - 1:,}")
print(f"Review candidates:      {len(rows):,}")
print(f"Output: {OUTPUT_FILE}")
print()
print("No corpus file was modified.")