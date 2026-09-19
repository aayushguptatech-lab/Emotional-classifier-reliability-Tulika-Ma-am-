import csv
import re
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v2.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4.csv"
)

REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v4_review.csv"
)


# ---------------------------------------------------------
# Speaker attribution vocabulary
# ---------------------------------------------------------

ATTRIBUTION_VERBS = (
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "remarked",
    "observed",
    "added",
    "continued",
    "whispered",
    "shouted",
    "called",
    "murmured",
    "declared",
    "explained",
    "suggested",
    "demanded",
    "protested",
    "returned",
    "responded",
    "agreed",
    "admitted",
    "insisted",
    "warned",
    "announced",
    "ejaculated",
    "groaned",
    "laughed",
)


# ---------------------------------------------------------
# Attribution modifiers
# ---------------------------------------------------------

ATTRIBUTION_MODIFIERS = (
    "boldly",
    "carelessly",
    "coolly",
    "defiantly",
    "eagerly",
    "excitedly",
    "gravely",
    "heartily",
    "impatiently",
    "piteously",
    "quietly",
    "sadly",
    "severely",
    "sternly",
    "thoughtfully",
    "warmly",
    "with satisfaction",
    "with some gruffness",
    "with a laugh",
    "good-humouredly",
    "good humouredly",
)


# ---------------------------------------------------------
# Speaker candidate validation
# ---------------------------------------------------------

def clean_speaker_candidate(candidate):
    """
    Validate and clean a candidate speaker expression.

    Examples accepted:

        Holmes
        McGinty
        I
        he
        she
        the doctor
        the inspector
        the chairman
        one of the men

    Examples rejected:

        McMurdo. It was all
        the letter which he
        the chairman. Ted Baldwin
        this singular epistle. There
    """

    candidate = candidate.strip()

    candidate = candidate.strip(
        ",;: "
    )

    if not candidate:
        return None

    # A speaker name/expression should not contain
    # a sentence boundary.
    if "." in candidate:
        return None

    # Remove quotation marks if they survived extraction.
    candidate = candidate.strip(
        "“”‘’\"' "
    )

    # Remove common attribution modifiers from the end.
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
                candidate,
            ).strip()

            if cleaned != candidate:
                candidate = cleaned
                changed = True

    if not candidate:
        return None

    # Reject obvious narrative fragments.
    lowered = candidate.lower()

    bad_phrases = (
        " it was ",
        " it is ",
        " there was ",
        " there is ",
        " he was ",
        " he is ",
        " she was ",
        " she is ",
        " who had ",
        " whom they ",
        " which he ",
        " which she ",
        " which they ",
        " the giant was ",
        " this singular ",
        " made ",
    )

    padded = " " + lowered + " "

    for phrase in bad_phrases:
        if phrase in padded:
            return None

    # Narrative connector words are strong evidence
    # that this is not a speaker.
    bad_words = {
        "which",
        "that",
        "because",
        "although",
        "while",
        "when",
        "where",
        "after",
        "before",
        "there",
        "was",
        "were",
        "is",
        "are",
        "had",
        "have",
        "made",
        "came",
        "went",
    }

    words = candidate.split()

    if any(
        word.lower().strip(",;:")
        in bad_words
        for word in words
    ):
        return None

    # Keep speaker expressions reasonably short.
    if len(candidate) > 40:
        return None

    if len(words) > 6:
        return None

    return candidate


# ---------------------------------------------------------
# Extract speaker from attribution
# ---------------------------------------------------------

def extract_speaker(attribution):
    """
    Extract a speaker from an attribution such as:

        said Holmes
        asked I
        remarked the inspector
        cried McGinty loudly

    The function deliberately returns None when the
    attribution looks unsafe.
    """

    attribution = attribution.strip()

    attribution = re.sub(
        r"^[,\s]+",
        "",
        attribution,
    )

    verb_pattern = (
        r"(?:"
        + "|".join(
            re.escape(v)
            for v in ATTRIBUTION_VERBS
        )
        + r")"
    )

    pattern = re.compile(
        r"\b"
        + verb_pattern
        + r"\s+"
        r"(.+?)"
        r"\s*$",
        re.IGNORECASE,
    )

    match = pattern.search(
        attribution
    )

    if not match:
        return None

    candidate = match.group(1)

    return clean_speaker_candidate(
        candidate
    )


# ---------------------------------------------------------
# Detect whether a candidate speaker looks safe
# ---------------------------------------------------------

def speaker_is_safe(speaker):
    """
    Additional safety check after extraction.
    """

    if not speaker:
        return False

    cleaned = clean_speaker_candidate(
        speaker
    )

    if cleaned is None:
        return False

    # Pronouns are legitimate historical dialogue
    # attribution forms.
    allowed_pronouns = {
        "I",
        "he",
        "she",
        "they",
        "we",
        "you",
    }

    if cleaned in allowed_pronouns:
        return True

    # A single capitalized proper name.
    if re.fullmatch(
        r"[A-Z][A-Za-z'’\-]+",
        cleaned,
    ):
        return True

    # Multi-word role/name expressions.
    if re.fullmatch(
        r"(?:[A-Za-z'’\-]+)(?:\s+[A-Za-z'’\-]+){0,5}",
        cleaned,
    ):
        return True

    return False


# ---------------------------------------------------------
# Main recovery
# ---------------------------------------------------------

def recover_speakers(rows):

    recovered = []

    for row in rows:

        old_speaker = row["speaker"].strip()

        # V2's explicit speaker is retained only if it
        # passes our safety checks.
        if (
            old_speaker != "Unknown"
            and speaker_is_safe(old_speaker)
        ):

            speaker = clean_speaker_candidate(
                old_speaker
            )

            confidence = "high"

        else:

            speaker = "Unknown"
            confidence = "review"

        new_row = dict(row)

        new_row["speaker"] = speaker

        new_row[
            "extraction_confidence"
        ] = confidence

        recovered.append(
            new_row
        )

    return recovered


# ---------------------------------------------------------
# Write outputs
# ---------------------------------------------------------

def write_outputs(rows):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
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

    review_rows = [
        row
        for row in rows
        if row["speaker"] == "Unknown"
        or row["extraction_confidence"]
        == "review"
    ]

    with REVIEW_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in review_rows:

            writer.writerow(
                {
                    field: row.get(
                        field,
                        "",
                    )
                    for field in fieldnames
                }
            )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print(
        "Reading V2 dialogue turns..."
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
        f"V2 turns read: {len(rows):,}"
    )

    print(
        "Recovering and validating speakers..."
    )

    recovered = recover_speakers(
        rows
    )

    known = sum(
        1
        for row in recovered
        if row["speaker"]
        != "Unknown"
    )

    unknown = len(recovered) - known

    high = sum(
        1
        for row in recovered
        if row["extraction_confidence"]
        == "high"
    )

    review = sum(
        1
        for row in recovered
        if row["extraction_confidence"]
        == "review"
    )

    write_outputs(
        recovered
    )

    print()
    print(
        "SPEAKER RECOVERY COMPLETE"
    )
    print(
        "--------------------------"
    )
    print(
        f"Input turns: {len(rows):,}"
    )
    print(
        f"Known speakers: {known:,}"
    )
    print(
        f"Unknown speakers: {unknown:,}"
    )
    print(
        f"High confidence: {high:,}"
    )
    print(
        f"Review confidence: {review:,}"
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
        "Turn reconstruction was NOT changed."
    )
    print(
        "Sentence segmentation was NOT performed."
    )


if __name__ == "__main__":
    main()