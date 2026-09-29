from pathlib import Path
import csv
import re


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


def align(v1, v4):

    results = []
    pos = 0

    for v4row in v4:

        target = norm(
            v4row["dialogue_text"]
        )

        combined = ""
        found = None

        for end in range(
            pos,
            min(
                pos + 20,
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

            if combined == target:
                found = end
                break

            if len(combined) > len(target):
                break

        if found is None:
            continue

        results.append(
            (
                v4row,
                pos,
                found
            )
        )

        pos = found + 1

    return results


def main():

    print("=" * 70)
    print("VOF — INSPECT HISTORICAL MERGE RULES")
    print("=" * 70)

    v1 = load(V1_FILE)
    v4 = load(V4_FILE)

    aligned = align(v1, v4)

    sentence_merges = []
    continuation_merges = []
    known_known = []

    for v4row, start, end in aligned:

        if end <= start:
            continue

        last_internal = norm(
            v1[end - 1]["dialogue_text"]
        )

        first_speaker = v1[start]["speaker"]
        second_speaker = v1[start + 1]["speaker"]

        last_char = (
            last_internal[-1]
            if last_internal
            else ""
        )

        item = (
            v4row,
            start,
            end,
            last_char,
            first_speaker,
            second_speaker
        )

        if last_char in ".!?":
            sentence_merges.append(item)

        elif last_char in ",;:—-":
            continuation_merges.append(item)

        else:
            continuation_merges.append(item)

        if (
            first_speaker != "Unknown"
            and second_speaker != "Unknown"
        ):
            known_known.append(item)

    print(
        f"\nSentence-punctuation merges: "
        f"{len(sentence_merges)}"
    )

    print(
        f"Continuation-punctuation merges: "
        f"{len(continuation_merges)}"
    )

    print(
        f"Known → known merges: "
        f"{len(known_known)}"
    )

    # ---------------------------------------------------------
    # Sentence punctuation examples
    # ---------------------------------------------------------

    print(
        "\n" + "=" * 70
    )
    print(
        "SENTENCE-PUNCTUATION MERGES — ALL EXAMPLES"
    )
    print(
        "=" * 70
    )

    for n, (
        v4row,
        start,
        end,
        last_char,
        first_speaker,
        second_speaker
    ) in enumerate(
        sentence_merges,
        1
    ):

        print(
            f"\n[{n}] {v4row['turn_id']}"
        )

        print(
            f"V1 range: "
            f"{start + 1}-{end + 1}"
        )

        print(
            f"Speakers: "
            f"{first_speaker!r} -> "
            f"{second_speaker!r}"
        )

        for i in range(
            start,
            end + 1
        ):

            print(
                f"  V1 {i + 1}: "
                f"{v1[i]['speaker']} | "
                f"{v1[i]['dialogue_text'][:500]!r}"
            )

        print(
            f"Historical V4: "
            f"{v4row['dialogue_text'][:900]!r}"
        )

    # ---------------------------------------------------------
    # Known-known examples
    # ---------------------------------------------------------

    print(
        "\n" + "=" * 70
    )
    print(
        "KNOWN → KNOWN MERGES"
    )
    print(
        "=" * 70
    )

    for n, (
        v4row,
        start,
        end,
        last_char,
        first_speaker,
        second_speaker
    ) in enumerate(
        known_known,
        1
    ):

        print(
            f"\n[{n}] {v4row['turn_id']}"
        )

        print(
            f"V1 range: "
            f"{start + 1}-{end + 1}"
        )

        print(
            f"Speakers: "
            f"{first_speaker!r} -> "
            f"{second_speaker!r}"
        )

        for i in range(
            start,
            end + 1
        ):

            print(
                f"  V1 {i + 1}: "
                f"{v1[i]['speaker']} | "
                f"{v1[i]['dialogue_text'][:450]!r}"
            )

        print(
            f"Historical V4: "
            f"{v4row['dialogue_text'][:700]!r}"
        )

    print(
        "\n" + "=" * 70
    )
    print(
        "INSPECTION COMPLETE"
    )
    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()