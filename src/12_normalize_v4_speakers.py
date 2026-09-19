import csv
import re
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5.csv"
)

REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5_review.csv"
)


ATTRIBUTION_MODIFIERS = (
    "with comic resignation",
    "with some gruffness",
    "with satisfaction",
    "with a laugh",
    "with an oath",
    "with vehemence",
    "in cold fury",
    "in a fury",
    "in no very",
    "in his most",
    "as we",
    "cordially",
    "gleefully",
    "sympathetically",
    "earnestly",
    "meekly",
    "grimly",
    "abruptly",
    "bitterly",
    "defiantly",
    "approvingly",
    "at last",
)


def normalize_candidate(speaker):

    speaker = speaker.strip()

    if not speaker:
        return None

    # -----------------------------------------------------
    # Remove known attribution modifiers from the end.
    # -----------------------------------------------------

    changed = True

    while changed:

        changed = False

        for modifier in ATTRIBUTION_MODIFIERS:

            pattern = re.compile(
                r"\s+"
                + re.escape(modifier)
                + r"\s*$",
                re.IGNORECASE,
            )

            cleaned = pattern.sub(
                "",
                speaker,
            ).strip()

            if cleaned != speaker:

                speaker = cleaned
                changed = True

    # -----------------------------------------------------
    # Reject obvious narrative fragments.
    # -----------------------------------------------------

    lowered = speaker.lower()

    rejected_fragments = (
        "which",
        "whom",
        "what they",
        "who had",
        "who they",
        "there was",
        "there is",
        "it was",
        "it is",
        "was all",
        "to one",
        "as he",
        "as she",
        "as we",
        "from the",
        "in a",
        "in no",
        "the letter",
        "the epistle",
        "present at",
        "of making",
    )

    for fragment in rejected_fragments:

        if fragment in lowered:

            return None

    # -----------------------------------------------------
    # Reject incomplete prepositional phrases.
    # -----------------------------------------------------

    if re.search(
        r"\b(?:in|with|from|of|to|at|as|by|for|on|under)"
        r"\s+(?:a|an|the|his|her|their|one|what|which|who)"
        r"\s*$",
        lowered,
    ):

        return None

    # -----------------------------------------------------
    # Reject clearly unfinished expressions.
    # -----------------------------------------------------

    if speaker.endswith(
        (
            " in",
            " with",
            " from",
            " of",
            " to",
            " as",
            " at",
            " by",
        )
    ):

        return None

    # -----------------------------------------------------
    # Basic length safety.
    # -----------------------------------------------------

    if len(speaker) > 35:
        return None

    if len(speaker.split()) > 6:
        return None

    return speaker


def process_rows(rows):

    output = []

    for row in rows:

        new_row = dict(row)

        original = row["speaker"].strip()

        if original == "Unknown":

            new_row["speaker"] = "Unknown"
            new_row["extraction_confidence"] = "review"

        else:

            cleaned = normalize_candidate(
                original
            )

            if cleaned is None:

                new_row["speaker"] = "Unknown"
                new_row[
                    "extraction_confidence"
                ] = "review"

            else:

                new_row["speaker"] = cleaned
                new_row[
                    "extraction_confidence"
                ] = "high"

        output.append(new_row)

    return output


def write_csv(path, rows):

    fieldnames = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
        "extraction_confidence",
        "source",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:

            writer.writerow(
                {
                    field: row.get(
                        field,
                        "",
                    )
                    for field in fieldnames
                }
            )


def main():

    print(
        "Reading V4 speaker assignments..."
    )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        rows = list(
            csv.DictReader(f)
        )

    print(
        f"Input turns: {len(rows):,}"
    )

    processed = process_rows(
        rows
    )

    known = [
        row
        for row in processed
        if row["speaker"] != "Unknown"
    ]

    review = [
        row
        for row in processed
        if row["speaker"] == "Unknown"
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        OUTPUT_FILE,
        processed,
    )

    write_csv(
        REVIEW_FILE,
        review,
    )

    print()
    print(
        "SPEAKER NORMALIZATION COMPLETE"
    )
    print(
        "-------------------------------"
    )
    print(
        f"Total turns: {len(processed):,}"
    )
    print(
        f"Known speakers: {len(known):,}"
    )
    print(
        f"Unknown/review: {len(review):,}"
    )
    print()
    print(
        f"Main output: {OUTPUT_FILE}"
    )
    print(
        f"Review output: {REVIEW_FILE}"
    )
    print()
    print(
        "V2 was not modified."
    )
    print(
        "V4 was not modified."
    )
    print(
        "Sentence segmentation was not performed."
    )


if __name__ == "__main__":
    main()