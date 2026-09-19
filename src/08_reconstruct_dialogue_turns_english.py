import csv
import re
from pathlib import Path


INPUT_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v3.csv"
)

REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v3_review.csv"
)


# ---------------------------------------------------------
# Basic speaker validation
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


# Common narrative/attribution modifiers.
# These are removed from an otherwise valid speaker expression.
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


def clean_attribution_candidate(candidate):
    """
    Clean a possible speaker expression without turning
    narrative text into a speaker.

    Examples:

        the inspector with satisfaction
            -> the inspector

        McMurdo carelessly
            -> McMurdo

        the doctor
            -> the doctor

    But:

        McMurdo. It was all
            -> None

        the letter which he
            -> None
    """

    candidate = candidate.strip()
    candidate = candidate.strip(",;: ")

    if not candidate:
        return None

    # A speaker attribution should not contain a sentence boundary.
    if "." in candidate:
        return None

    # Reject obvious narrative continuation.
    lowered = candidate.lower()

    narrative_fragments = (
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
        " made ",
    )

    padded = f" {lowered} "

    for fragment in narrative_fragments:
        if fragment in padded:
            return None

    # Remove known manner modifiers from the end.
    changed = True

    while changed:
        changed = False

        for modifier in ATTRIBUTION_MODIFIERS:
            pattern = re.compile(
                r"\s+" + re.escape(modifier) + r"\s*$",
                re.IGNORECASE,
            )

            new_candidate = pattern.sub("", candidate).strip()

            if new_candidate != candidate:
                candidate = new_candidate
                changed = True

    candidate = candidate.strip(",;: ")

    if not candidate:
        return None

    # Do not allow extremely long expressions.
    if len(candidate) > 40:
        return None

    # Speaker expressions should normally be short.
    words = candidate.split()

    if len(words) > 6:
        return None

    # Reject expressions containing obvious prose connectors.
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

    if any(word.lower().strip(",;:") in bad_words for word in words):
        return None

    return candidate


def extract_speaker_from_attribution(text):
    """
    Recover a speaker from attribution text.

    The attribution may contain a speech verb:

        said Holmes
        asked I
        remarked the inspector

    We deliberately keep this conservative.
    """

    text = text.strip()

    # Remove leading punctuation.
    text = re.sub(r"^[,\s]+", "", text)

    verb_pattern = (
        r"(?:"
        + "|".join(map(re.escape, ATTRIBUTION_VERBS))
        + r")"
    )

    pattern = re.compile(
        r"\b"
        + verb_pattern
        + r"\s+"
        r"(.+?)"
        r"(?:\s*$)",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if not match:
        return None

    candidate = match.group(1)

    return clean_attribution_candidate(candidate)


def looks_like_split_attribution(text):
    """
    Detect attribution text between two quotation spans.

    Example:

        “Really, Holmes,” said I severely,
        “you are a little trying at times.”

    The quotation marks themselves are not part of the
    text passed to this function.
    """

    text = text.strip()

    if not text:
        return False

    verb_pattern = (
        r"(?:"
        + "|".join(map(re.escape, ATTRIBUTION_VERBS))
        + r")"
    )

    pattern = re.compile(
        r"^\s*,?\s*"
        + verb_pattern
        + r"\s+"
        r".+?$",
        re.IGNORECASE,
    )

    return bool(pattern.search(text))


# ---------------------------------------------------------
# Find quotation spans
# ---------------------------------------------------------

def find_quotation_spans(text):
    """
    Find curly-quoted spans.

    The novel uses curly quotation marks.
    """

    spans = []

    opening = "“"
    closing = "”"

    position = 0

    while True:
        start = text.find(opening, position)

        if start == -1:
            break

        end = text.find(closing, start + 1)

        if end == -1:
            break

        dialogue = text[start + 1:end].strip()

        spans.append(
            {
                "start": start,
                "end": end,
                "text": dialogue,
            }
        )

        position = end + 1

    return spans


# ---------------------------------------------------------
# Reconstruct dialogue turns
# ---------------------------------------------------------

def reconstruct_turns(text, spans):
    """
    Reconstruct multiple quotation spans belonging to the
    same speaker turn.

    Important:
    - Sentence segmentation is NOT performed here.
    - Long speeches remain one turn.
    - Multi-paragraph speeches remain one turn.
    """

    turns = []

    current_text_parts = []
    current_start = None
    current_speaker = None
    current_confidence = "review"

    for index, span in enumerate(spans):

        quote_text = span["text"]

        if current_start is None:
            current_start = span["start"]

        # Text between this quotation and the next quotation.
        gap = ""

        if index < len(spans) - 1:
            next_span = spans[index + 1]

            gap = text[
                span["end"] + 1:
                next_span["start"]
            ]

        # Look for attribution after the current quotation.
        speaker_after = None

        after_pattern = re.compile(
            r"^\s*,?\s*(.+?)(?:\n|$)",
            re.DOTALL,
        )

        after_match = after_pattern.match(gap)

        if after_match:
            attribution_text = after_match.group(1).strip()

            speaker_after = extract_speaker_from_attribution(
                attribution_text
            )

        # Look for a split attribution between quotations.
        split_attribution = looks_like_split_attribution(gap)

        if split_attribution:

            extracted_speaker = extract_speaker_from_attribution(
                gap
            )

            if extracted_speaker:
                current_speaker = extracted_speaker
                current_confidence = "high"

            if current_text_parts:
                current_text_parts.append(quote_text)
            else:
                current_text_parts = [quote_text]

            continue

        # If the current quotation has an explicit speaker
        # immediately after it, store it.
        if speaker_after:

            if current_text_parts:
                current_text_parts.append(quote_text)
            else:
                current_text_parts = [quote_text]

            current_speaker = speaker_after
            current_confidence = "high"

            # Finish this turn unless the next quotation is
            # clearly part of the same split speech.
            if index < len(spans) - 1:
                next_gap = text[
                    spans[index + 1]["end"] + 1:
                    spans[index + 1]["start"]
                ]

                if not looks_like_split_attribution(next_gap):
                    turns.append(
                        {
                            "start": current_start,
                            "speaker": current_speaker,
                            "dialogue_text": " ".join(
                                current_text_parts
                            ).strip(),
                            "unit_type": "speaker_turn",
                            "extraction_confidence": (
                                current_confidence
                            ),
                        }
                    )

                    current_text_parts = []
                    current_start = None
                    current_speaker = None
                    current_confidence = "review"

            continue

        # No clear speaker found.
        current_text_parts.append(quote_text)

        # If there is no explicit continuation, finish the turn.
        if index == len(spans) - 1:

            turns.append(
                {
                    "start": current_start,
                    "speaker": (
                        current_speaker
                        if current_speaker
                        else "Unknown"
                    ),
                    "dialogue_text": " ".join(
                        current_text_parts
                    ).strip(),
                    "unit_type": "speaker_turn",
                    "extraction_confidence": (
                        current_confidence
                        if current_speaker
                        else "review"
                    ),
                }
            )

            current_text_parts = []
            current_start = None
            current_speaker = None
            current_confidence = "review"

    return turns


# ---------------------------------------------------------
# Write output
# ---------------------------------------------------------

def write_outputs(turns):

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

        for number, turn in enumerate(
            turns,
            start=1,
        ):

            writer.writerow(
                {
                    "text_id": "VOF",
                    "turn_id": f"VOF_T{number:05d}",
                    "speaker": turn["speaker"],
                    "dialogue_text": turn["dialogue_text"],
                    "unit_type": turn["unit_type"],
                    "extraction_confidence": (
                        turn["extraction_confidence"]
                    ),
                    "source": (
                        "Project Gutenberg #3289"
                    ),
                }
            )

    # Review file
    review_rows = [
        turn
        for turn in turns
        if turn["extraction_confidence"] == "review"
        or turn["speaker"] == "Unknown"
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

        for number, turn in enumerate(
            review_rows,
            start=1,
        ):

            writer.writerow(
                {
                    "text_id": "VOF",
                    "turn_id": f"VOF_REVIEW_{number:05d}",
                    "speaker": turn["speaker"],
                    "dialogue_text": turn["dialogue_text"],
                    "unit_type": turn["unit_type"],
                    "extraction_confidence": (
                        turn["extraction_confidence"]
                    ),
                    "source": (
                        "Project Gutenberg #3289"
                    ),
                }
            )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("Reading cleaned novel...")

    text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    print(
        f"Characters read: {len(text):,}"
    )

    print("Finding quotation spans...")

    spans = find_quotation_spans(text)

    print(
        f"Quotation spans found: {len(spans):,}"
    )

    print("Reconstructing dialogue turns...")

    turns = reconstruct_turns(
        text,
        spans,
    )

    known = sum(
        1
        for turn in turns
        if turn["speaker"] != "Unknown"
    )

    unknown = len(turns) - known

    high = sum(
        1
        for turn in turns
        if turn["extraction_confidence"] == "high"
    )

    review = sum(
        1
        for turn in turns
        if turn["extraction_confidence"] == "review"
    )

    write_outputs(turns)

    print()
    print("RECONSTRUCTION COMPLETE")
    print("------------------------")
    print(
        f"Quotation spans: {len(spans):,}"
    )
    print(
        f"Dialogue turns: {len(turns):,}"
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
        "Sentence segmentation was NOT performed."
    )


if __name__ == "__main__":
    main()