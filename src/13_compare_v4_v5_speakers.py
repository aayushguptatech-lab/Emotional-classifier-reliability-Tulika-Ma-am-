import csv
from pathlib import Path

V4_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4.csv"
)

V5_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_v4_v5_speaker_changes.csv"
)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


print("Reading V4 and V5...")
v4_rows = read_csv(V4_FILE)
v5_rows = read_csv(V5_FILE)

print(f"V4 rows: {len(v4_rows):,}")
print(f"V5 rows: {len(v5_rows):,}")

v4_by_id = {row["turn_id"]: row for row in v4_rows}
v5_by_id = {row["turn_id"]: row for row in v5_rows}

changes = []

for turn_id, v4 in v4_by_id.items():
    if turn_id not in v5_by_id:
        continue

    v5 = v5_by_id[turn_id]

    old_speaker = v4.get("speaker", "").strip()
    new_speaker = v5.get("speaker", "").strip()

    old_confidence = v4.get("extraction_confidence", "").strip()
    new_confidence = v5.get("extraction_confidence", "").strip()

    if old_speaker != new_speaker or old_confidence != new_confidence:
        changes.append(
            {
                "turn_id": turn_id,
                "old_speaker": old_speaker,
                "new_speaker": new_speaker,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "dialogue": v5.get("dialogue", ""),
            }
        )

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = [
        "turn_id",
        "old_speaker",
        "new_speaker",
        "old_confidence",
        "new_confidence",
        "dialogue",
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(changes)

print()
print("V4 → V5 COMPARISON COMPLETE")
print("-----------------------------")
print(f"Changed turns: {len(changes):,}")
print(f"Output: {OUTPUT_FILE}")

print()
print("CHANGES")
print("-------")

for row in changes:
    print(
        f"{row['turn_id']} | "
        f"{row['old_speaker']} -> {row['new_speaker']} | "
        f"{row['old_confidence']} -> {row['new_confidence']}"
    )

print()
print("No source files were modified.")