from pathlib import Path
import csv
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_dialogue_v2.csv"
)

CLEAN_FILE = (
    ROOT
    / "data"
    / "cleaned"
    / "english"
    / "the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "english"
    / "the_valley_of_fear_v2_reconstruction_audit.csv"
)


def main():

    print("=" * 70)
    print("VOF — V2 RECONSTRUCTION AUDIT")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    if not CLEAN_FILE.exists():
        raise FileNotFoundError(CLEAN_FILE)

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    text = CLEAN_FILE.read_text(
        encoding="utf-8"
    )

    print(f"\nV2 rows: {len(rows):,}")
    print(f"Clean source characters: {len(text):,}")

    # --------------------------------------------------------
    # Length statistics
    # --------------------------------------------------------

    lengths = [
        len(row["dialogue_text"])
        for row in rows
    ]

    print("\nDialogue length statistics:")

    print(
        f"  >100 chars   : "
        f"{sum(x > 100 for x in lengths):,}"
    )

    print(
        f"  >300 chars   : "
        f"{sum(x > 300 for x in lengths):,}"
    )

    print(
        f"  >500 chars   : "
        f"{sum(x > 500 for x in lengths):,}"
    )

    print(
        f"  >1000 chars  : "
        f"{sum(x > 1000 for x in lengths):,}"
    )

    # --------------------------------------------------------
    # Speaker statistics
    # --------------------------------------------------------

    speakers = Counter(
        row["speaker"]
        for row in rows
    )

    print("\nTop speakers:")

    for speaker, count in speakers.most_common(20):
        print(
            f"  {speaker!r}: {count}"
        )

    # --------------------------------------------------------
    # Known / unknown
    # --------------------------------------------------------

    unknown = [
        row
        for row in rows
        if row["speaker"] == "Unknown"
    ]

    known = [
        row
        for row in rows
        if row["speaker"] != "Unknown"
    ]

    print("\nSpeaker totals:")
    print(f"  Known   : {len(known):,}")
    print(f"  Unknown : {len(unknown):,}")

    # --------------------------------------------------------
    # Suspicious speaker strings
    # --------------------------------------------------------

    suspicious_words = {
        "in",
        "with",
        "as",
        "who",
        "which",
        "that",
        "and",
        "when",
        "from",
        "of",
        "to",
        "for",
        "on",
        "at",
        "by",
    }

    suspicious = []

    for row in known:

        speaker = row["speaker"].strip()

        words = speaker.lower().split()

        if len(words) > 4:
            suspicious.append(row)
            continue

        if any(
            word in suspicious_words
            for word in words
        ):
            suspicious.append(row)

    print(
        f"\nSuspicious known-speaker rows: "
        f"{len(suspicious):,}"
    )

    print("\nFirst 30 suspicious rows:")

    for row in suspicious[:30]:

        print(
            "\n"
            f"{row['turn_id']} | "
            f"speaker={row['speaker']!r}\n"
            f"dialogue={row['dialogue_text'][:250]!r}"
        )

    # --------------------------------------------------------
    # Longest dialogue records
    # --------------------------------------------------------

    longest = sorted(
        rows,
        key=lambda r: len(r["dialogue_text"]),
        reverse=True
    )

    print("\nLongest 20 dialogue records:")

    for row in longest[:20]:

        print(
            "\n"
            f"{row['turn_id']} | "
            f"speaker={row['speaker']!r} | "
            f"chars={len(row['dialogue_text'])}\n"
            f"{row['dialogue_text'][:300]!r}"
        )

    # --------------------------------------------------------
    # Write audit
    # --------------------------------------------------------

    fields = [
        "turn_id",
        "speaker",
        "dialogue_text",
        "dialogue_length",
        "suspicious_speaker",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()

        for row in rows:

            speaker = row["speaker"].strip()
            words = speaker.lower().split()

            is_suspicious = (
                speaker != "Unknown"
                and (
                    len(words) > 4
                    or any(
                        word in suspicious_words
                        for word in words
                    )
                )
            )

            writer.writerow({
                "turn_id": row["turn_id"],
                "speaker": speaker,
                "dialogue_text": row["dialogue_text"],
                "dialogue_length": len(
                    row["dialogue_text"]
                ),
                "suspicious_speaker": is_suspicious,
            })

    print("\nAudit created:")
    print(OUTPUT_FILE)

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()