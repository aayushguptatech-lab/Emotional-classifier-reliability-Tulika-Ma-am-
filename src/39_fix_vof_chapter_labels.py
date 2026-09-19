import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/final/english/the_valley_of_fear_master_v2.csv"
)

OUTPUT_FILE = Path(
    "data/final/english/the_valley_of_fear_master_final.csv"
)


with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames


BAD_LABEL = (
    "PART II—The Scowrers — "
    "Chapter VII—The Trapping of Birdy Edwards"
)

GOOD_LABEL = "PART II — Chapter VII"


changed = 0

for row in rows:

    if row["chapter"] == BAD_LABEL:
        row["chapter"] = GOOD_LABEL
        changed += 1


if changed == 0:
    print("No matching bad chapter label was found.")
    print("Nothing was written.")
    raise SystemExit(1)


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(rows)


print("VOF CHAPTER LABEL NORMALIZATION")
print("===============================")
print()
print(f"Input rows:       {len(rows):,}")
print(f"Labels corrected: {changed:,}")
print()
print(f"Output:")
print(OUTPUT_FILE)
print()
print("IMPORTANT:")
print("- Sentence text was NOT changed.")
print("- Speaker assignments were NOT changed.")
print("- Previous/next context was NOT changed.")
print("- Only the malformed chapter label was normalized.")
print("- master_v2.csv was NOT modified.")