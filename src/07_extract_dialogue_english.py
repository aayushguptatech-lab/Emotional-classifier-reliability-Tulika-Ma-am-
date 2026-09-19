import re
import csv
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue.csv"
)

REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_review.csv"
)

TEXT_ID = "VOF"

SOURCE = (
    "Project Gutenberg #3289 - "
    "The Valley of Fear"
)


# ============================================================
# SPEAKER ATTRIBUTION PATTERNS
# ============================================================

# Common verbs used when a character speaks.
SPEECH_VERBS = (
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
    "remarked",
    "ejaculated",
    "groaned",
    "laughed",
    "repeated",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_whitespace(text):
    """
    Convert repeated whitespace/newlines inside a dialogue
    span into normal spaces.

    IMPORTANT:
    This does NOT change spelling or punctuation.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_speaker_from_after(text):
    """
    Try to detect a speaker immediately after a quotation.

    Example:
        “I agree,” said Holmes.

    Returns:
        Holmes
    """

    pattern = re.compile(
        r"^\s*(?:"
        + "|".join(SPEECH_VERBS)
        + r")\s+"
        r"(?P<speaker>[A-Z][A-Za-z.'’-]*(?:\s+[A-Z][A-Za-z.'’-]*){0,4})",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if match:
        speaker = match.group("speaker").strip()

        # Remove trailing punctuation.
        speaker = speaker.rstrip(".,;:!?")

        return speaker

    return None


def extract_speaker_from_before(text):
    """
    Try to detect a speaker immediately before a quotation.

    Example:
        Holmes said, “I agree.”

    Returns:
        Holmes
    """

    pattern = re.compile(
        r"(?P<speaker>[A-Z][A-Za-z.'’-]*(?:\s+[A-Z][A-Za-z.'’-]*){0,4})"
        r"\s+"
        r"(?:"
        + "|".join(SPEECH_VERBS)
        + r")"
        r"\s*,?\s*$",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if match:
        speaker = match.group("speaker").strip()
        speaker = speaker.rstrip(".,;:!?")

        return speaker

    return None


def find_quote_spans(text):
    """
    Find curly-quoted dialogue spans.

    This handles:
        “text”

    and preserves multiline quotations.
    """

    pattern = re.compile(
        r"“(.*?)”",
        re.DOTALL,
    )

    return list(pattern.finditer(text))


def get_context_before(text, start_position, characters=180):
    """
    Return a short context window before a quotation.
    """

    start = max(0, start_position - characters)
    return text[start:start_position]


def get_context_after(text, end_position, characters=180):
    """
    Return a short context window after a quotation.
    """

    end = min(len(text), end_position + characters)
    return text[end_position:end]


def classify_unit_type(speaker, confidence):
    """
    Keep unit_type separate from extraction_confidence.

    This is intentionally conservative.
    """

    if speaker != "Unknown" and confidence == "high":
        return "speaker_attributed_dialogue"

    return "dialogue_candidate"


# ============================================================
# MAIN EXTRACTION
# ============================================================

def main():

    print("=" * 70)
    print("TASK 7.4 - ENGLISH DIALOGUE EXTRACTION PROTOTYPE")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    print(f"\nReading:\n{INPUT_FILE}")

    text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    if not text.strip():
        raise ValueError("Input file is empty.")

    print(f"Characters read: {len(text):,}")

    # --------------------------------------------------------
    # Find quotation spans
    # --------------------------------------------------------

    quote_spans = find_quote_spans(text)

    print(f"Quotation spans found: {len(quote_spans):,}")

    if not quote_spans:
        raise ValueError(
            "No curly-quoted dialogue spans were found."
        )

    # --------------------------------------------------------
    # Prepare output
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REVIEW_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    records = []
    review_records = []

    # --------------------------------------------------------
    # Process quotation spans
    # --------------------------------------------------------

    turn_number = 1

    for match in quote_spans:

        dialogue_text = match.group(1)

        if not dialogue_text.strip():
            continue

        start_position = match.start()
        end_position = match.end()

        before_context = get_context_before(
            text,
            start_position
        )

        after_context = get_context_after(
            text,
            end_position
        )

        speaker = None
        confidence = "review"
        detection_method = "none"

        # ----------------------------------------------------
        # Try attribution AFTER quotation
        # ----------------------------------------------------

        speaker_after = extract_speaker_from_after(
            after_context
        )

        if speaker_after:
            speaker = speaker_after
            confidence = "high"
            detection_method = "after_quote"

        # ----------------------------------------------------
        # Try attribution BEFORE quotation
        # ----------------------------------------------------

        if speaker is None:

            speaker_before = extract_speaker_from_before(
                before_context
            )

            if speaker_before:
                speaker = speaker_before
                confidence = "high"
                detection_method = "before_quote"

        # ----------------------------------------------------
        # If no speaker found
        # ----------------------------------------------------

        if speaker is None:
            speaker = "Unknown"

        # ----------------------------------------------------
        # Clean dialogue text
        # --------------------------------------------------------

        cleaned_dialogue = clean_whitespace(
            dialogue_text
        )

        # ----------------------------------------------------
        # Unit type
        # ----------------------------------------------------

        unit_type = classify_unit_type(
            speaker,
            confidence
        )

        # ----------------------------------------------------
        # Stable turn ID
        # ----------------------------------------------------

        turn_id = f"{TEXT_ID}_T{turn_number:05d}"

        # ----------------------------------------------------
        # Main record
        # ----------------------------------------------------

        record = {
            "text_id": TEXT_ID,
            "turn_id": turn_id,
            "speaker": speaker,
            "dialogue_text": cleaned_dialogue,
            "unit_type": unit_type,
            "extraction_confidence": confidence,
            "source": SOURCE,
        }

        records.append(record)

        # ----------------------------------------------------
        # Review record
        # ----------------------------------------------------

        if confidence == "review":

            review_record = {
                "text_id": TEXT_ID,
                "turn_id": turn_id,
                "speaker": speaker,
                "dialogue_text": cleaned_dialogue,
                "unit_type": unit_type,
                "extraction_confidence": confidence,
                "detection_method": detection_method,
                "context_before": clean_whitespace(
                    before_context
                ),
                "context_after": clean_whitespace(
                    after_context
                ),
                "source": SOURCE,
            }

            review_records.append(
                review_record
            )

        turn_number += 1

    # ========================================================
    # WRITE MAIN CSV
    # ========================================================

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
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)

    # ========================================================
    # WRITE REVIEW CSV
    # ========================================================

    review_fieldnames = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
        "extraction_confidence",
        "detection_method",
        "context_before",
        "context_after",
        "source",
    ]

    with REVIEW_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=review_fieldnames
        )

        writer.writeheader()
        writer.writerows(review_records)

    # ========================================================
    # SUMMARY
    # ========================================================

    high_confidence = sum(
        1
        for r in records
        if r["extraction_confidence"] == "high"
    )

    review_count = sum(
        1
        for r in records
        if r["extraction_confidence"] == "review"
    )

    known_speakers = sum(
        1
        for r in records
        if r["speaker"] != "Unknown"
    )

    unknown_speakers = sum(
        1
        for r in records
        if r["speaker"] == "Unknown"
    )

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)

    print(f"\nTotal dialogue candidates: {len(records):,}")
    print(f"Known speakers: {known_speakers:,}")
    print(f"Unknown speakers: {unknown_speakers:,}")
    print(f"High-confidence records: {high_confidence:,}")
    print(f"Review records: {review_count:,}")

    print("\nMain output:")
    print(OUTPUT_FILE)

    print("\nReview output:")
    print(REVIEW_FILE)

    print("\nImportant:")
    print("Sentence segmentation was NOT performed.")
    print("Dialogue turns were preserved as parent units.")
    print("Unknown speakers were retained for later review.")

    print("\nTASK 7.4 COMPLETE")


if __name__ == "__main__":
    main()