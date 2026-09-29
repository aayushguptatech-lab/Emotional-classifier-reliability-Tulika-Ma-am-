from pathlib import Path
import csv
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]

V1_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue.csv"
)

V4_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue_v4.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "historical_v1_v4_comparison.csv"
)


def load(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def norm(text):
    return " ".join(
        text.split()
    ).strip()


def main():

    print("=" * 70)
    print("VOF — V1 vs HISTORICAL V4")
    print("=" * 70)

    v1 = load(V1_FILE)
    v4 = load(V4_FILE)

    print(f"\nV1 rows : {len(v1):,}")
    print(f"V4 rows : {len(v4):,}")

    # ---------------------------------------------------------
    # Dialogue text lookup
    # ---------------------------------------------------------

    v1_texts = Counter(
        norm(row["dialogue_text"])
        for row in v1
    )

    v4_texts = Counter(
        norm(row["dialogue_text"])
        for row in v4
    )

    shared = (
        set(v1_texts)
        &
        set(v4_texts)
    )

    print(
        f"\nShared dialogue strings: {len(shared):,}"
    )

    # ---------------------------------------------------------
    # V4 records made from multiple V1 records
    # ---------------------------------------------------------

    v1_index = {}

    for i, row in enumerate(v1):

        text = norm(
            row["dialogue_text"]
        )

        v1_index.setdefault(
            text,
            []
        ).append(i)

    merged = []

    for i, row in enumerate(v4):

        text = norm(
            row["dialogue_text"]
        )

        if text in v1_index:
            continue

        # Find consecutive V1 records whose combined text
        # equals the V4 dialogue.
        parts = text.split()

        found = None

        for start in range(len(v1)):

            combined = ""

            for end in range(
                start,
                min(
                    start + 10,
                    len(v1)
                )
            ):

                piece = norm(
                    v1[end]["dialogue_text"]
                )

                combined = (
                    piece
                    if not combined
                    else combined + " " + piece
                )

                if combined == text:

                    found = (
                        start,
                        end
                    )

                    break

                if len(combined) > len(text):
                    break

            if found:
                break

        if found:

            start, end = found

            if end > start:

                merged.append({
                    "v4_turn_id": row["turn_id"],
                    "v4_speaker": row["speaker"],
                    "v1_start_index": start,
                    "v1_end_index": end,
                    "v1_count": end - start + 1,
                    "v4_dialogue": row["dialogue_text"],
                    "v1_dialogue": " || ".join(
                        v1[j]["dialogue_text"]
                        for j in range(
                            start,
                            end + 1
                        )
                    ),
                })

    print(
        f"\nV4 records detected as merges of V1 records: "
        f"{len(merged):,}"
    )

    print(
        "\nFirst 30 detected merges:"
    )

    for row in merged[:30]:

        print(
            "\n"
            f"{row['v4_turn_id']} | "
            f"{row['v4_speaker']} | "
            f"V1 rows "
            f"{row['v1_start_index'] + 1}-"
            f"{row['v1_end_index'] + 1}\n"
            f"V4: {row['v4_dialogue'][:300]!r}\n"
            f"V1: {row['v1_dialogue'][:500]!r}"
        )

    # ---------------------------------------------------------
    # V1 records absent as exact strings from V4
    # ---------------------------------------------------------

    absent = []

    for i, row in enumerate(v1):

        text = norm(
            row["dialogue_text"]
        )

        if text not in v4_texts:

            absent.append({
                "v1_index": i,
                "turn_id": row["turn_id"],
                "speaker": row["speaker"],
                "dialogue_text": row["dialogue_text"],
            })

    print(
        f"\nV1 rows whose exact dialogue is absent from V4: "
        f"{len(absent):,}"
    )

    print(
        "\nFirst 40 absent V1 records:"
    )

    for row in absent[:40]:

        print(
            "\n"
            f"V1 index: {row['v1_index'] + 1}\n"
            f"{row['turn_id']} | "
            f"{row['speaker']}\n"
            f"{row['dialogue_text'][:350]!r}"
        )

    # ---------------------------------------------------------
    # Output machine-readable comparison
    # ---------------------------------------------------------

    fields = [
        "v4_turn_id",
        "v4_speaker",
        "v1_start_index",
        "v1_end_index",
        "v1_count",
        "v4_dialogue",
        "v1_dialogue",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(merged)

    print(
        "\nCreated:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "COMPARISON COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()