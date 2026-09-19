import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_valley_of_fear_internal_boundary_review.csv"
)


with INPUT_FILE.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    rows = list(csv.DictReader(f))


print()
print(f"Total cases: {len(rows)}")
print()


for i, row in enumerate(rows, start=1):

    print("=" * 100)
    print(f"CASE {i}")
    print(f"Turn ID: {row['turn_id']}")
    print(f"Current speaker: {row['speaker']}")
    print(
        f"Internal attribution: "
        f"{row['internal_attributions']}"
    )

    print()
    print("DIALOGUE:")
    print(row["dialogue_text"][:1200])

    print()
    print("SOURCE CONTEXT:")
    print(row["source_context"][:1800])

    print()


print("=" * 100)
print("END OF REVIEW")