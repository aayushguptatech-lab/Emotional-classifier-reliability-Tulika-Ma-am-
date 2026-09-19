import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v6.csv"
)


TARGET_IDS = {
    "VOF_T00431",
    "VOF_T00433",
    "VOF_T01179_A",
    "VOF_T01179_B",
}


with INPUT_FILE.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


print("V6 REPAIR AUDIT")
print("================")
print(f"Total V6 turns: {len(rows):,}")
print()


found = {
    row["turn_id"]: row
    for row in rows
    if row["turn_id"] in TARGET_IDS
}


for turn_id in [
    "VOF_T00431",
    "VOF_T00433",
    "VOF_T01179_A",
    "VOF_T01179_B",
]:

    print("-" * 70)

    if turn_id not in found:
        print(f"ERROR: {turn_id} NOT FOUND")
        continue

    row = found[turn_id]

    print(f"Turn ID:              {row['turn_id']}")
    print(f"Parent turn ID:       {row['parent_turn_id']}")
    print(f"Speaker:              {row['speaker']}")
    print(f"Confidence:           {row['extraction_confidence']}")
    print(f"Unit type:            {row['unit_type']}")
    print(f"Dialogue:             {row['dialogue_text']}")
    print(f"Repair note:          {row['repair_note']}")


print()
print("-" * 70)

# Basic safety checks

if len(found) != 4:
    raise ValueError(
        "One or more repaired V6 turns are missing."
    )

if found["VOF_T00431"]["speaker"] != "the inspector":
    raise ValueError(
        "VOF_T00431 speaker repair is incorrect."
    )

if found["VOF_T00433"]["speaker"] != "White Mason":
    raise ValueError(
        "VOF_T00433 speaker repair is incorrect."
    )

if found["VOF_T01179_A"]["speaker"] != "McGinty":
    raise ValueError(
        "VOF_T01179_A speaker is incorrect."
    )

if found["VOF_T01179_B"]["speaker"] != "McMurdo":
    raise ValueError(
        "VOF_T01179_B speaker is incorrect."
    )

if found["VOF_T01179_A"]["dialogue_text"] != "Now, McMurdo!":
    raise ValueError(
        "VOF_T01179_A dialogue is incorrect."
    )

if found["VOF_T01179_B"]["dialogue_text"] != (
    "I said just now that I knew Birdy Edwards,"
):
    raise ValueError(
        "VOF_T01179_B dialogue is incorrect."
    )

if "VOF_T01179" in {
    row["turn_id"] for row in rows
}:
    raise ValueError(
        "Original VOF_T01179 incorrectly remains as an active V6 turn."
    )


print()
print("AUDIT PASSED")
print("------------")
print("All three controlled repairs are present and correct.")
print("No active VOF_T01179 parent turn remains.")
print("V6 is ready for the next audit stage.")