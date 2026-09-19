import csv
from pathlib import Path
from collections import Counter


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_speaker_audit.csv"
)


def main():

    print("Reading V4 dialogue turns...")

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    known_rows = [
        row
        for row in rows
        if row["speaker"].strip()
        and row["speaker"].strip() != "Unknown"
    ]

    print(f"Total V4 turns: {len(rows):,}")
    print(f"Known-speaker turns: {len(known_rows):,}")
    print()

    print("SPEAKER FREQUENCY")
    print("-----------------")

    counts = Counter(
        row["speaker"].strip()
        for row in known_rows
    )

    for speaker, count in counts.most_common():

        print(
            f"{count:4d} | {speaker}"
        )

    print()
    print("Writing complete known-speaker audit...")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "turn_id",
        "speaker",
        "dialogue_text",
        "extraction_confidence",
        "source",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in known_rows:

            writer.writerow(
                {
                    field: row.get(
                        field,
                        "",
                    )
                    for field in fieldnames
                }
            )

    print()
    print(
        f"Audit file: {OUTPUT_FILE}"
    )
    print()
    print(
        "No source files were modified."
    )


if __name__ == "__main__":
    main()