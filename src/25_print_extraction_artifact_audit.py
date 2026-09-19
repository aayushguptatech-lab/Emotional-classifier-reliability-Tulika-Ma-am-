import csv
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_extraction_artifact_audit_v2.csv"
)

print("EXTRACTION ARTIFACT REVIEW")
print("==========================")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Audit file not found: {INPUT_FILE}"
    )

with INPUT_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Potential artifact rows: {len(rows)}")
print()

for i, row in enumerate(rows, start=1):
    print("=" * 80)
    print(f"CASE {i}")
    print(f"Text ID:       {row['text_id']}")
    print(f"Turn ID:       {row['turn_id']}")
    print(f"Sentence ID:   {row['sentence_id']}")
    print(f"Speaker:       {row['speaker']}")
    print(f"Pattern:       {row['pattern']}")
    print(f"Fragment:      {row['fragment']}")
    print(f"Position:      {row['start_position']} - {row['end_position']}")
    print(f"Current text:  {row['current_text']}")
    print()

print("=" * 80)
print("END OF ARTIFACT REVIEW")