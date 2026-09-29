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

OLD_V2_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue_v2.csv"
)

NEW_V2_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue_v2.csv"
)


def load(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def normalize(text):
    return " ".join(
        text.split()
    ).strip()


def main():

    print("=" * 70)
    print("VOF — V1 / V2 STRUCTURAL COMPARISON")
    print("=" * 70)

    if not V1_FILE.exists():
        raise FileNotFoundError(V1_FILE)

    if not OLD_V2_FILE.exists():
        raise FileNotFoundError(OLD_V2_FILE)

    v1 = load(V1_FILE)

    # The current reconstruction has overwritten the historical filename.
    # Therefore we only compare V1 against the current V2 structure here.
    v2 = load(NEW_V2_FILE)

    print(f"\nV1 rows: {len(v1):,}")
    print(f"Current V2 rows: {len(v2):,}")

    # ---------------------------------------------------------
    # V1 unit types
    # ---------------------------------------------------------

    print("\nV1 unit types:")

    for key, count in Counter(
        row.get("unit_type", "")
        for row in v1
    ).most_common():

        print(
            f"  {key}: {count:,}"
        )

    # ---------------------------------------------------------
    # V2 unit types
    # ---------------------------------------------------------

    print("\nV2 unit types:")

    for key, count in Counter(
        row.get("unit_type", "")
        for row in v2
    ).most_common():

        print(
            f"  {key}: {count:,}"
        )

    # ---------------------------------------------------------
    # Dialogue length comparison
    # ---------------------------------------------------------

    v1_lengths = [
        len(row.get("dialogue_text", ""))
        for row in v1
    ]

    v2_lengths = [
        len(row.get("dialogue_text", ""))
        for row in v2
    ]

    print("\nLength comparison:")

    print(
        f"  V1 >100 chars  : "
        f"{sum(x > 100 for x in v1_lengths):,}"
    )

    print(
        f"  V2 >100 chars  : "
        f"{sum(x > 100 for x in v2_lengths):,}"
    )

    print(
        f"  V1 >300 chars  : "
        f"{sum(x > 300 for x in v1_lengths):,}"
    )

    print(
        f"  V2 >300 chars  : "
        f"{sum(x > 300 for x in v2_lengths):,}"
    )

    print(
        f"  V1 >500 chars  : "
        f"{sum(x > 500 for x in v1_lengths):,}"
    )

    print(
        f"  V2 >500 chars  : "
        f"{sum(x > 500 for x in v2_lengths):,}"
    )

    print(
        f"  V1 >1000 chars : "
        f"{sum(x > 1000 for x in v1_lengths):,}"
    )

    print(
        f"  V2 >1000 chars : "
        f"{sum(x > 1000 for x in v2_lengths):,}"
    )

    # ---------------------------------------------------------
    # Shared dialogue texts
    # ---------------------------------------------------------

    v1_texts = Counter(
        normalize(row.get("dialogue_text", ""))
        for row in v1
    )

    v2_texts = Counter(
        normalize(row.get("dialogue_text", ""))
        for row in v2
    )

    shared = (
        set(v1_texts)
        &
        set(v2_texts)
    )

    print(
        "\nShared normalized dialogue strings:"
    )

    print(
        f"  {len(shared):,}"
    )

    # ---------------------------------------------------------
    # Exact sequential correspondence
    # ---------------------------------------------------------

    sequential_matches = 0

    limit = min(
        len(v1),
        len(v2)
    )

    for i in range(limit):

        a = normalize(
            v1[i].get(
                "dialogue_text",
                ""
            )
        )

        b = normalize(
            v2[i].get(
                "dialogue_text",
                ""
            )
        )

        if a == b:
            sequential_matches += 1

    print(
        "\nSequential dialogue matches:"
    )

    print(
        f"  {sequential_matches:,} "
        f"of first {limit:,}"
    )

    # ---------------------------------------------------------
    # V1 rows that are absent from V2
    # ---------------------------------------------------------

    missing_from_v2 = []

    for row in v1:

        text = normalize(
            row.get(
                "dialogue_text",
                ""
            )
        )

        if text and text not in v2_texts:
            missing_from_v2.append(row)

    print(
        "\nV1 dialogue strings absent from V2:"
    )

    print(
        f"  {len(missing_from_v2):,}"
    )

    print(
        "\nFirst 25 absent examples:"
    )

    for row in missing_from_v2[:25]:

        print(
            "\n"
            f"{row.get('turn_id')} | "
            f"{row.get('speaker')}\n"
            f"{row.get('dialogue_text', '')[:300]!r}"
        )

    # ---------------------------------------------------------
    # V2 rows with suspiciously long text
    # ---------------------------------------------------------

    print(
        "\nCurrent V2 longest records:"
    )

    longest = sorted(
        v2,
        key=lambda r: len(
            r.get(
                "dialogue_text",
                ""
            )
        ),
        reverse=True
    )

    for row in longest[:15]:

        print(
            "\n"
            f"{row.get('turn_id')} | "
            f"{row.get('speaker')} | "
            f"{len(row.get('dialogue_text', ''))} chars\n"
            f"{row.get('dialogue_text', '')[:250]!r}"
        )

    print("\n" + "=" * 70)
    print("STRUCTURAL COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()