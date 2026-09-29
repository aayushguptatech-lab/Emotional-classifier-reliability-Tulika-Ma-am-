"""
08c_audit_v2_experimental.py

Purpose
-------
Audit the experimental V2 reconstruction before it is allowed
to enter the downstream pipeline.

This script does NOT modify the corpus.
"""

from pathlib import Path
import csv
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue_v2_experimental_743.csv"
)


def main():

    print("=" * 70)
    print("VOF — EXPERIMENTAL V2 AUDIT")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"File not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        rows = list(csv.DictReader(f))

    print(f"\nRows: {len(rows):,}")

    # --------------------------------------------------------
    # Basic statistics
    # --------------------------------------------------------

    speakers = Counter(
        row["speaker"]
        for row in rows
    )

    unit_types = Counter(
        row["unit_type"]
        for row in rows
    )

    confidence = Counter(
        row["extraction_confidence"]
        for row in rows
    )

    print("\nUnit types:")
    for key, value in unit_types.items():
        print(f"  {key}: {value:,}")

    print("\nConfidence:")
    for key, value in confidence.items():
        print(f"  {key}: {value:,}")

    print("\nTop speakers:")
    for speaker, count in speakers.most_common(25):
        print(f"  {speaker!r}: {count:,}")

    # --------------------------------------------------------
    # Suspicious speaker strings
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SUSPICIOUS SPEAKER VALUES")
    print("=" * 70)

    suspicious_words = [
        "with",
        "in",
        "as",
        "who",
        "which",
        "that",
        "when",
        "while",
        "from",
        "at",
        "on",
        "for",
        "of",
        ".",
        ",",
    ]

    suspicious = []

    for row in rows:

        speaker = row["speaker"].strip()

        if speaker == "Unknown":
            continue

        lower = speaker.lower()

        if (
            len(speaker) > 40
            or any(
                word in lower
                for word in suspicious_words
            )
        ):
            suspicious.append(row)

    print(
        f"\nSuspicious known-speaker rows: "
        f"{len(suspicious):,}"
    )

    for row in suspicious[:30]:

        print("\n----------------------------------------")
        print("Turn:", row["turn_id"])
        print("Speaker:", row["speaker"])
        print("Confidence:", row["extraction_confidence"])
        print("Dialogue:")
        print(row["dialogue_text"][:500])

    # --------------------------------------------------------
    # Very long turns
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("LONGEST DIALOGUE TURNS")
    print("=" * 70)

    longest = sorted(
        rows,
        key=lambda r: len(r["dialogue_text"]),
        reverse=True
    )

    for row in longest[:20]:

        print("\n----------------------------------------")
        print("Turn:", row["turn_id"])
        print("Speaker:", row["speaker"])
        print(
            "Characters:",
            len(row["dialogue_text"])
        )
        print(
            row["dialogue_text"][:700]
        )

    # --------------------------------------------------------
    # Extremely long turns
    # --------------------------------------------------------

    extreme = [
        row
        for row in rows
        if len(row["dialogue_text"]) > 1000
    ]

    print("\n" + "=" * 70)
    print("EXTREME TURNS")
    print("=" * 70)

    print(
        f"Turns > 1000 characters: "
        f"{len(extreme):,}"
    )

    for row in extreme[:20]:

        print("\n----------------------------------------")
        print("Turn:", row["turn_id"])
        print("Speaker:", row["speaker"])
        print(
            "Characters:",
            len(row["dialogue_text"])
        )
        print(
            row["dialogue_text"][:1000]
        )


if __name__ == "__main__":
    main()