import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)


TARGET_TURNS = [
    "VOF_T00005",
    "VOF_T00006",
    "VOF_T00540",
    "VOF_T00546",
    "VOF_T00594",
    "VOF_T00758",
    "VOF_T00759",
    "VOF_T00894",
    "VOF_T00978",
    "VOF_T01182",
    "VOF_T01186",
    "VOF_T01266",
]


with INPUT_FILE.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


print("SENTENCE SEGMENTATION AUDIT")
print("============================")
print(f"Total sentence rows: {len(rows):,}")
print()


for turn_id in TARGET_TURNS:

    turn_rows = [
        row
        for row in rows
        if row["turn_id"] == turn_id
    ]

    print("=" * 80)
    print(f"TURN: {turn_id}")

    if not turn_rows:
        print("ERROR: TURN NOT FOUND")
        continue

    first = turn_rows[0]

    print(f"Speaker: {first['speaker']}")
    print(f"Number of sentences: {len(turn_rows)}")
    print()

    for row in turn_rows:
        print(
            f"{row['sentence_id']}: "
            f"{row['current_text']}"
        )

    print()


print("=" * 80)
print("END OF SENTENCE AUDIT")