import csv
import re
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_contextual_speaker_audit.csv"
)


SUSPICIOUS_PATTERNS = (
    " in ",
    " with ",
    " as ",
    " who ",
    " whom ",
    " which ",
    " that ",
    " what ",
    " there ",
    " was ",
    " were ",
    " had ",
    " have ",
    " to ",
    " from ",
    " at ",
    " of ",
    " by ",
)


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def find_context(clean_text, dialogue_text):
    """
    Find the dialogue in the cleaned novel and return
    a short window surrounding it.

    This is diagnostic only. It does not modify the corpus.
    """

    dialogue = normalize(dialogue_text)

    if not dialogue:
        return "", ""

    # Try the first 100 characters first because long
    # dialogue may contain line-wrapping differences.
    search_piece = dialogue[:100]

    position = clean_text.find(search_piece)

    if position == -1:
        # Try a shorter piece.
        search_piece = dialogue[:60]
        position = clean_text.find(search_piece)

    if position == -1:
        return "", ""

    before_start = max(
        0,
        position - 250
    )

    after_end = min(
        len(clean_text),
        position + len(search_piece) + 250
    )

    before = clean_text[
        before_start:position
    ]

    after = clean_text[
        position + len(search_piece):after_end
    ]

    return (
        normalize(before),
        normalize(after)
    )


def looks_suspicious(speaker):

    speaker = speaker.strip()

    if not speaker:
        return False

    lowered = (
        " "
        + speaker.lower()
        + " "
    )

    # Long speaker expressions are worth inspection.
    if len(speaker) > 20:
        return True

    # Multi-word expressions are not automatically wrong,
    # but these connectors frequently indicate that the
    # regex captured narrative material after the speaker.
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in lowered:
            return True

    return False


def main():

    print(
        "Reading V4 speaker assignments..."
    )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        rows = list(
            csv.DictReader(f)
        )

    print(
        f"Total V4 turns: {len(rows):,}"
    )

    suspicious = [
        row
        for row in rows
        if row["speaker"] != "Unknown"
        and looks_suspicious(
            row["speaker"]
        )
    ]

    print(
        f"Suspicious known-speaker assignments: "
        f"{len(suspicious):,}"
    )

    print(
        "Reading cleaned novel..."
    )

    clean_text = CLEAN_FILE.read_text(
        encoding="utf-8"
    )

    audit_rows = []

    print()
    print(
        "CONTEXTUAL SPEAKER AUDIT"
    )
    print(
        "========================"
    )

    for row in suspicious:

        before, after = find_context(
            clean_text,
            row["dialogue_text"]
        )

        audit_rows.append(
            {
                "turn_id": row["turn_id"],
                "speaker": row["speaker"],
                "dialogue_text": row[
                    "dialogue_text"
                ],
                "context_before": before,
                "context_after": after,
                "extraction_confidence": row[
                    "extraction_confidence"
                ],
            }
        )

        print()
        print(
            f"{row['turn_id']} | "
            f"{row['speaker']}"
        )

        print(
            "DIALOGUE:"
        )

        print(
            row["dialogue_text"][:300]
        )

        print(
            "CONTEXT BEFORE:"
        )

        print(
            before[-300:]
        )

        print(
            "CONTEXT AFTER:"
        )

        print(
            after[:300]
        )

        print(
            "-" * 70
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "turn_id",
        "speaker",
        "dialogue_text",
        "context_before",
        "context_after",
        "extraction_confidence",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            audit_rows
        )

    print()
    print(
        "AUDIT COMPLETE"
    )
    print(
        f"Rows written: {len(audit_rows):,}"
    )
    print(
        f"Audit file: {OUTPUT_FILE}"
    )
    print()
    print(
        "V4 was NOT modified."
    )
    print(
        "V2 was NOT modified."
    )
    print(
        "No sentence segmentation was performed."
    )


if __name__ == "__main__":
    main()