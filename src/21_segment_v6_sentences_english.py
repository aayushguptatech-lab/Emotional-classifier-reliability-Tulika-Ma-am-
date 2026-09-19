import csv
import re
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v6.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)

REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1_review.csv"
)


# ---------------------------------------------------------
# Sentence segmentation
#
# This is deliberately conservative.
#
# We are NOT using an external NLP model yet.
# We first create a transparent, reproducible baseline
# that can be audited.
# ---------------------------------------------------------

ABBREVIATIONS = {
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "st.",
    "no.",
    "messrs.",
    "etc.",
    "i.e.",
    "e.g.",
}


def normalize_spaces(text):
    """
    Collapse physical line breaks and repeated whitespace
    without changing the wording or punctuation.
    """
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def protect_abbreviations(text):
    """
    Temporarily replace periods in common abbreviations so
    they are not interpreted as sentence boundaries.
    """

    protected = text

    for abbreviation in sorted(
        ABBREVIATIONS,
        key=len,
        reverse=True
    ):
        replacement = abbreviation.replace(".", "<prd>")
        protected = re.sub(
            re.escape(abbreviation),
            replacement,
            protected,
            flags=re.IGNORECASE,
        )

    return protected


def restore_abbreviations(text):
    return text.replace("<prd>", ".")


def split_sentences(text):
    """
    Conservative sentence splitter.

    Primary boundaries:
        .
        !
        ?

    A boundary is accepted when followed by:
        whitespace + uppercase/lowercase/quote
        OR end of text.

    We keep punctuation with the sentence.

    This is a baseline segmentation, not a claim that every
    historical literary boundary is automatically correct.
    """

    text = normalize_spaces(text)

    if not text:
        return []

    protected = protect_abbreviations(text)

    # Split after sentence-ending punctuation when another
    # token follows.
    parts = re.split(
        r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ“”\"‘’—\-])",
        protected,
    )

    sentences = []

    for part in parts:
        part = restore_abbreviations(part).strip()

        if part:
            sentences.append(part)

    return sentences


def needs_review(sentences, original_text):
    """
    Flag cases that deserve manual inspection.

    We do not automatically alter them.
    """

    reasons = []

    if not sentences:
        reasons.append("no_sentence_generated")

    # Very long single sentence.
    if len(sentences) == 1 and len(sentences[0]) > 500:
        reasons.append("very_long_single_sentence")

    # Extremely short sentence fragments.
    for sentence in sentences:
        if len(sentence.strip()) <= 2:
            reasons.append("very_short_fragment")
            break

    # Multiple dashes can indicate dialogue structure that
    # deserves inspection.
    if "—" in original_text and len(sentences) > 1:
        reasons.append("contains_em_dash")

    # Ellipsis can make automatic segmentation uncertain.
    if "..." in original_text and len(sentences) > 1:
        reasons.append("contains_ellipsis")

    return "; ".join(sorted(set(reasons)))


print("Reading V6 dialogue turns...")

with INPUT_FILE.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


print(f"V6 turns read: {len(rows):,}")


required_columns = {
    "text_id",
    "turn_id",
    "speaker",
    "dialogue_text",
    "unit_type",
    "extraction_confidence",
    "source",
}


actual_columns = set(rows[0].keys())

missing_columns = required_columns - actual_columns

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )


sentence_rows = []
review_rows = []

sentence_counts = []

for row in rows:

    turn_id = row["turn_id"]
    text_id = row["text_id"]
    dialogue_text = row["dialogue_text"]

    sentences = split_sentences(dialogue_text)

    sentence_counts.append(len(sentences))

    review_reason = needs_review(
        sentences,
        dialogue_text
    )

    for index, sentence in enumerate(sentences, start=1):

        sentence_id = (
            f"{turn_id}_S{index:02d}"
        )

        sentence_row = {
            "text_id": text_id,
            "turn_id": turn_id,
            "sentence_id": sentence_id,
            "speaker": row["speaker"],
            "current_text": sentence,
            "unit_type": row["unit_type"],
            "extraction_confidence": row[
                "extraction_confidence"
            ],
            "source": row["source"],
        }

        sentence_rows.append(sentence_row)

    if review_reason:
        review_rows.append({
            "text_id": text_id,
            "turn_id": turn_id,
            "speaker": row["speaker"],
            "dialogue_text": dialogue_text,
            "sentence_count": len(sentences),
            "review_reason": review_reason,
        })


# ---------------------------------------------------------
# Write sentence-level output.
# ---------------------------------------------------------

sentence_fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "unit_type",
    "extraction_confidence",
    "source",
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=sentence_fieldnames
    )

    writer.writeheader()
    writer.writerows(sentence_rows)


# ---------------------------------------------------------
# Write review output.
# ---------------------------------------------------------

review_fieldnames = [
    "text_id",
    "turn_id",
    "speaker",
    "dialogue_text",
    "sentence_count",
    "review_reason",
]


with REVIEW_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=review_fieldnames
    )

    writer.writeheader()
    writer.writerows(review_rows)


# ---------------------------------------------------------
# Safety checks.
# ---------------------------------------------------------

if not sentence_rows:
    raise ValueError(
        "No sentence rows were generated."
    )

sentence_ids = [
    row["sentence_id"]
    for row in sentence_rows
]

if len(sentence_ids) != len(set(sentence_ids)):
    raise ValueError(
        "Duplicate sentence IDs detected."
    )


# Every sentence must belong to a V6 turn.
v6_turn_ids = {
    row["turn_id"]
    for row in rows
}

unknown_parent_turns = {
    row["turn_id"]
    for row in sentence_rows
    if row["turn_id"] not in v6_turn_ids
}

if unknown_parent_turns:
    raise ValueError(
        "Sentence rows contain unknown turn IDs: "
        f"{sorted(unknown_parent_turns)}"
    )


print()
print("SENTENCE SEGMENTATION COMPLETE")
print("--------------------------------")
print(f"V6 dialogue turns:       {len(rows):,}")
print(f"Sentence rows generated: {len(sentence_rows):,}")
print(f"Turns requiring review:  {len(review_rows):,}")
print(
    "Average sentences/turn: "
    f"{sum(sentence_counts) / len(sentence_counts):.2f}"
)
print(
    "Maximum sentences/turn: "
    f"{max(sentence_counts)}"
)
print()
print(f"Sentence output: {OUTPUT_FILE}")
print(f"Review output:   {REVIEW_FILE}")
print()
print("Previous/next context was NOT generated yet.")
print("V6 was NOT modified.")