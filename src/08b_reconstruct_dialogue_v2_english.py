"""
08b_reconstruct_dialogue_v2_english.py

Purpose:
    Experimental reconstruction of V2-style dialogue for The Valley of Fear.

Input:
    data/cleaned/english/the_valley_of_fear_clean.txt

Output (experimental; does not overwrite historical V2):
    data/extracted/english/the_valley_of_fear_dialogue_v2_experimental_08b.csv
    data/extracted/english/the_valley_of_fear_dialogue_v2_review_experimental_08b.csv

The historical frozen-stage V2 artifacts remain:
    data/extracted/english/the_valley_of_fear_dialogue_v2.csv
    data/extracted/english/the_valley_of_fear_dialogue_v2_review.csv

Method:
    - Extract quotation spans from the canonical cleaned text.
    - Preserve dialogue text from the source.
    - Merge only clearly continuous quotation fragments.
    - Use only immediately adjacent attribution for speaker detection.
    - Do not search hundreds of characters away for a speaker.
    - Keep Unknown when attribution is not directly supported.
"""

from pathlib import Path
import csv
import re


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "cleaned"
    / "english"
    / "the_valley_of_fear_clean.txt"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "extracted"
    / "english"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "the_valley_of_fear_dialogue_v2_experimental_08b.csv"
)

REVIEW_FILE = (
    OUTPUT_DIR
    / "the_valley_of_fear_dialogue_v2_review_experimental_08b.csv"
)


TEXT_ID = "VOF"
SOURCE = "Project Gutenberg #3289 - The Valley of Fear"


# ============================================================
# SPEECH VERBS
# ============================================================

SPEECH_VERBS = {
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
    "repeated",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()


def find_quote_spans(text):
    """
    Support both correctly decoded curly quotes and the
    mojibake representation present in some project files.
    """

    patterns = [
        r"“(.*?)”",
        r"â€œ(.*?)â€",
    ]

    spans = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.DOTALL
        ):
            spans.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(1),
            })

    # Remove duplicates.
    unique = {}

    for span in spans:
        key = (span["start"], span["end"])
        unique[key] = span

    spans = list(unique.values())
    spans.sort(key=lambda x: x["start"])

    return spans


def clean_dialogue(text):
    """
    Normalize line wrapping inside the dialogue field.

    The canonical novel file itself is never changed.
    """

    return normalize_space(text)


def extract_direct_speaker(text):
    """
    Extract a speaker only when a speech attribution is
    immediately adjacent to the quotation.

    This function intentionally avoids broad-context searching.
    """

    text = normalize_space(text)

    if not text:
        return None

    # --------------------------------------------------------
    # Name/pronoun + speech verb
    # --------------------------------------------------------

    pattern_before = re.compile(
        r"^(?:"
        r"(?P<name>[A-Z][A-Za-z'-]+"
        r"(?:\s+[A-Z][A-Za-z'-]+){0,3})"
        r"|(?P<pronoun>he|she|I|we|they|you)"
        r")\s+"
        r"(?:"
        + "|".join(sorted(SPEECH_VERBS))
        + r")\b",
        re.IGNORECASE,
    )

    match = pattern_before.search(text)

    if match:
        return (
            match.group("name")
            or match.group("pronoun")
        )

    # --------------------------------------------------------
    # Speech verb + name/pronoun
    # --------------------------------------------------------

    pattern_after = re.compile(
        r"^(?:"
        + "|".join(sorted(SPEECH_VERBS))
        + r")\s+"
        r"(?:"
        r"(?P<name>[A-Z][A-Za-z'-]+"
        r"(?:\s+[A-Z][A-Za-z'-]+){0,3})"
        r"|(?P<pronoun>he|she|I|we|they|you)"
        r")\b",
        re.IGNORECASE,
    )

    match = pattern_after.search(text)

    if match:
        return (
            match.group("name")
            or match.group("pronoun")
        )

    return None


def get_immediate_before(text, start):
    """
    Return only the immediately preceding attribution region.

    We deliberately stop at the previous sentence/paragraph
    boundary rather than searching arbitrarily far backwards.
    """

    before = text[max(0, start - 180):start]

    # Only the final sentence is relevant.
    pieces = re.split(r"(?<=[.!?])\s+|\n+", before)

    if pieces:
        return pieces[-1].strip()

    return before.strip()


def get_immediate_after(text, end):
    """
    Return only the immediately following attribution region.
    """

    after = text[end:min(len(text), end + 180)]

    pieces = re.split(r"\n+|(?<=[.!?])\s+", after)

    if pieces:
        return pieces[0].strip()

    return after.strip()


def get_speaker(text, span):
    """
    Conservative speaker attribution.

    Priority:
        1. Immediately after quotation.
        2. Immediately before quotation.
        3. Unknown.
    """

    after = get_immediate_after(
        text,
        span["end"]
    )

    speaker = extract_direct_speaker(after)

    if speaker:
        return speaker, "high"

    before = get_immediate_before(
        text,
        span["start"]
    )

    speaker = extract_direct_speaker(before)

    if speaker:
        return speaker, "high"

    return "Unknown", "review"


def should_merge(text, current, nxt):
    """
    Merge only when the next quotation is clearly part of
    the same immediate dialogue passage.

    Conservative rule:
    - no paragraph break
    - short intervening material
    - no clear new speaker attribution
    """

    gap = text[
        current["end"]:
        nxt["start"]
    ]

    if not gap:
        return True

    # Paragraph boundary = separate dialogue unit.
    if "\n\n" in gap:
        return False

    normalized = normalize_space(gap)

    # Large narrative gap = separate unit.
    if len(normalized) > 100:
        return False

    # A speech verb in the gap may indicate a new attribution.
    lower = normalized.lower()

    for verb in SPEECH_VERBS:
        if re.search(
            rf"\b{re.escape(verb)}\b",
            lower
        ):
            return False

    # Typical continuation punctuation.
    if normalized in {
        "",
        ",",
        ";",
        ":",
        "—",
        "-",
    }:
        return True

    # If the gap begins with punctuation or a continuation
    # marker, conservative merge.
    if normalized.startswith(
        (",", ";", ":", "—", "-")
    ):
        return True

    return False


def reconstruct_groups(text, spans):

    if not spans:
        return []

    groups = []
    current = [spans[0]]

    for index in range(len(spans) - 1):

        current_span = spans[index]
        next_span = spans[index + 1]

        if should_merge(
            text,
            current_span,
            next_span
        ):
            current.append(next_span)
        else:
            groups.append(current)
            current = [next_span]

    groups.append(current)

    return groups


def build_record(text, group, number):

    first = group[0]

    dialogue_parts = [
        clean_dialogue(span["text"])
        for span in group
    ]

    dialogue = " ".join(
        part
        for part in dialogue_parts
        if part
    )

    speaker, confidence = get_speaker(
        text,
        first
    )

    if speaker == "Unknown":
        unit_type = "dialogue_candidate"
    else:
        unit_type = "speaker_attributed_dialogue"

    return {
        "text_id": TEXT_ID,
        "turn_id": f"VOF_T{number:05d}",
        "speaker": speaker,
        "dialogue_text": dialogue,
        "unit_type": unit_type,
        "extraction_confidence": confidence,
        "source": SOURCE,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VOF — CONSERVATIVE REPRODUCIBLE V2 EXTRACTION")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    text = INPUT_FILE.read_text(
        encoding="utf-8"
    )

    print(f"\nInput: {INPUT_FILE}")
    print(
        f"Source characters: {len(text):,}"
    )

    spans = find_quote_spans(text)

    print(
        f"Quotation spans found: {len(spans):,}"
    )

    groups = reconstruct_groups(
        text,
        spans
    )

    print(
        f"Reconstructed turns: {len(groups):,}"
    )

    records = []

    for number, group in enumerate(
        groups,
        start=1
    ):
        records.append(
            build_record(
                text,
                group,
                number
            )
        )

    fields = [
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
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(records)

    review_fields = fields + [
        "review_reason"
    ]

    with REVIEW_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=review_fields
        )

        writer.writeheader()

        for row in records:

            reason = (
                "Speaker attribution requires manual/source review."
                if row["speaker"] == "Unknown"
                else ""
            )

            writer.writerow({
                **row,
                "review_reason": reason,
            })

    unknown = sum(
        row["speaker"] == "Unknown"
        for row in records
    )

    known = len(records) - unknown

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    print(f"Total turns      : {len(records):,}")
    print(f"Known speakers   : {known:,}")
    print(f"Unknown speakers : {unknown:,}")

    print("\nCreated:")
    print(OUTPUT_FILE)
    print(REVIEW_FILE)

    print("\nCanonical cleaned source was not modified.")


if __name__ == "__main__":
    main()