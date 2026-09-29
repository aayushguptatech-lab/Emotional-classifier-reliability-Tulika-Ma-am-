from pathlib import Path
import csv
import re
from collections import Counter, defaultdict


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


def load(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def norm(text):
    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def main():

    print("=" * 70)
    print("VOF — HISTORICAL MERGE PATTERN ANALYSIS")
    print("=" * 70)

    v1 = load(V1_FILE)
    v4 = load(V4_FILE)

    print(f"\nV1 rows: {len(v1):,}")
    print(f"V4 rows: {len(v4):,}")

    # ---------------------------------------------------------
    # Build a word-based sequential alignment.
    #
    # Historical V4 preserves V1 order. We therefore walk
    # through V1 and find the smallest consecutive V1 block
    # whose normalized text equals each V4 record.
    # ---------------------------------------------------------

    alignment = []

    v1_pos = 0

    for v4_index, v4row in enumerate(v4):

        target = norm(
            v4row["dialogue_text"]
        )

        combined = ""
        start = v1_pos
        found_end = None

        for end in range(
            v1_pos,
            min(
                v1_pos + 20,
                len(v1)
            )
        ):

            piece = norm(
                v1[end]["dialogue_text"]
            )

            if not piece:
                continue

            combined = (
                piece
                if not combined
                else combined + " " + piece
            )

            if combined == target:
                found_end = end
                break

            if len(combined) > len(target):
                break

        if found_end is None:

            alignment.append({
                "v4_index": v4_index,
                "v4_turn_id": v4row["turn_id"],
                "v4_speaker": v4row["speaker"],
                "v1_start": None,
                "v1_end": None,
                "v1_count": None,
                "status": "UNMATCHED",
            })

            # Do not advance blindly.
            continue

        count = found_end - start + 1

        alignment.append({
            "v4_index": v4_index,
            "v4_turn_id": v4row["turn_id"],
            "v4_speaker": v4row["speaker"],
            "v1_start": start,
            "v1_end": found_end,
            "v1_count": count,
            "status": (
                "single"
                if count == 1
                else "merge"
            ),
        })

        v1_pos = found_end + 1

    # ---------------------------------------------------------
    # Basic statistics
    # ---------------------------------------------------------

    counts = Counter(
        row["v1_count"]
        for row in alignment
        if row["status"] != "UNMATCHED"
    )

    print("\nAlignment status:")
    print(
        "  Matched:",
        sum(
            1
            for row in alignment
            if row["status"] != "UNMATCHED"
        )
    )
    print(
        "  Unmatched:",
        sum(
            1
            for row in alignment
            if row["status"] == "UNMATCHED"
        )
    )

    print("\nV1 records per historical V4 turn:")

    for count in sorted(counts):

        print(
            f"  {count:>2} V1 record(s): "
            f"{counts[count]:>4} V4 turns"
        )

    # ---------------------------------------------------------
    # Examine merge sizes > 2
    # ---------------------------------------------------------

    print("\nMerge sizes greater than 2:")

    large_merges = [
        row
        for row in alignment
        if (
            row["status"] == "merge"
            and row["v1_count"] > 2
        )
    ]

    print(
        f"  Total: {len(large_merges):,}"
    )

    # ---------------------------------------------------------
    # For each merge, inspect the relationship between
    # neighboring V1 speaker labels.
    # ---------------------------------------------------------

    merge_speaker_patterns = Counter()

    for row in alignment:

        if row["status"] != "merge":
            continue

        start = row["v1_start"]
        end = row["v1_end"]

        speakers = tuple(
            v1[i]["speaker"]
            for i in range(
                start,
                end + 1
            )
        )

        merge_speaker_patterns[speakers] += 1

    print(
        "\nMost common speaker-label patterns inside merges:"
    )

    for pattern, count in (
        merge_speaker_patterns
        .most_common(30)
    ):

        print(
            f"  {count:>4} : "
            f"{pattern}"
        )

    # ---------------------------------------------------------
    # Examine whether merges commonly happen when the first
    # V1 record has a suspicious speaker and the next is
    # Unknown.
    # ---------------------------------------------------------

    categories = Counter()

    for row in alignment:

        if row["status"] != "merge":
            continue

        start = row["v1_start"]
        end = row["v1_end"]

        first = v1[start]
        last = v1[end]

        first_speaker = first["speaker"]
        last_speaker = last["speaker"]

        if (
            first_speaker != "Unknown"
            and last_speaker == "Unknown"
        ):
            category = "known_then_unknown"

        elif (
            first_speaker == "Unknown"
            and last_speaker == "Unknown"
        ):
            category = "unknown_then_unknown"

        elif (
            first_speaker == "Unknown"
            and last_speaker != "Unknown"
        ):
            category = "unknown_then_known"

        else:
            category = "known_then_known"

        categories[category] += 1

    print(
        "\nMerge speaker transition categories:"
    )

    for category, count in categories.most_common():
        print(
            f"  {category}: {count}"
        )

    # ---------------------------------------------------------
    # Print examples of each category
    # ---------------------------------------------------------

    print(
        "\nRepresentative examples:"
    )

    printed = set()

    for row in alignment:

        if row["status"] != "merge":
            continue

        start = row["v1_start"]
        end = row["v1_end"]

        first_speaker = v1[start]["speaker"]
        last_speaker = v1[end]["speaker"]

        if (
            first_speaker != "Unknown"
            and last_speaker == "Unknown"
        ):
            category = "known_then_unknown"

        elif (
            first_speaker == "Unknown"
            and last_speaker == "Unknown"
        ):
            category = "unknown_then_unknown"

        elif (
            first_speaker == "Unknown"
            and last_speaker != "Unknown"
        ):
            category = "unknown_then_known"

        else:
            category = "known_then_known"

        if category in printed:
            continue

        printed.add(category)

        print(
            f"\n--- {category} ---"
        )

        print(
            f"V4: {row['v4_turn_id']}"
        )

        print(
            f"V1 range: "
            f"{start + 1}-{end + 1}"
        )

        for i in range(
            start,
            end + 1
        ):

            print(
                f"  V1 {i + 1}: "
                f"{v1[i]['speaker']} | "
                f"{v1[i]['dialogue_text'][:220]!r}"
            )

    # ---------------------------------------------------------
    # Look for punctuation/continuation clues.
    # ---------------------------------------------------------

    punctuation = Counter()

    for row in alignment:

        if row["status"] != "merge":
            continue

        start = row["v1_start"]
        end = row["v1_end"]

        for i in range(
            start,
            end
        ):

            text = norm(
                v1[i]["dialogue_text"]
            )

            if not text:
                continue

            last_char = text[-1]

            if last_char in ",;:—-":
                punctuation["continuation_punctuation"] += 1

            elif last_char in ".!?":
                punctuation["sentence_punctuation"] += 1

            else:
                punctuation["other"] += 1

    print(
        "\nPunctuation at internal V1 boundaries:"
    )

    for key, value in punctuation.items():
        print(
            f"  {key}: {value}"
        )

    # ---------------------------------------------------------
    # Save alignment
    # ---------------------------------------------------------

    output = (
        ROOT
        / "data"
        / "extracted"
        / "english"
        / "historical_v1_v4_alignment.csv"
    )

    fields = [
        "v4_index",
        "v4_turn_id",
        "v4_speaker",
        "v1_start",
        "v1_end",
        "v1_count",
        "status",
    ]

    with output.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(alignment)

    print(
        "\nCreated:"
    )

    print(output)

    print(
        "\n" + "=" * 70
    )
    print(
        "MERGE ANALYSIS COMPLETE"
    )
    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()