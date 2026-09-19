import csv
from pathlib import Path


REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1_review.csv"
)


with REVIEW_FILE.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


print("SENTENCE SEGMENTATION REVIEW")
print("============================")
print(f"Review rows: {len(rows):,}")
print()


for number, row in enumerate(rows, start=1):

    print("=" * 80)
    print(f"CASE {number}")
    print(f"Turn ID:       {row['turn_id']}")
    print(f"Speaker:       {row['speaker']}")
    print(f"Sentences:     {row['sentence_count']}")
    print(f"Reason:        {row['review_reason']}")
    print()
    print("Dialogue:")
    print(row["dialogue_text"])
    print()


print("=" * 80)
print("END OF REVIEW")