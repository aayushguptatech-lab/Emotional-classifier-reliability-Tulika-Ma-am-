import csv
import re
from pathlib import Path

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

V5_REVIEW_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5_review.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_v5_review_context.csv"
)


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def normalize_for_search(text):
    """
    Normalize physical line wrapping and whitespace
    without changing the actual words.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_context(text, dialogue, window=800):

    normalized_text = normalize_for_search(text)
    normalized_dialogue = normalize_for_search(dialogue)

    if not normalized_dialogue:
        return "", "", ""

    position = normalized_text.find(normalized_dialogue)

    # If the complete dialogue cannot be found,
    # progressively search using its beginning.
    if position == -1:

        words = normalized_dialogue.split()

        for keep_words in [50, 40, 30, 20, 15, 10]:

            if len(words) < keep_words:
                continue

            candidate = " ".join(words[:keep_words])

            position = normalized_text.find(candidate)

            if position != -1:
                normalized_dialogue = candidate
                break

    if position == -1:
        return "", "", ""

    start = max(
        0,
        position - window
    )

    end = min(
        len(normalized_text),
        position + len(normalized_dialogue) + window
    )

    before = normalized_text[start:position]

    matched = normalized_text[
        position:
        position + len(normalized_dialogue)
    ]

    after = normalized_text[
        position + len(normalized_dialogue):
        end
    ]

    return before, matched, after


print("Reading V5 review file...")

review_rows = read_csv(V5_REVIEW_FILE)

print(f"V5 review rows: {len(review_rows):,}")

print()
print("Reading cleaned novel...")

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

print(
    f"Clean novel characters: "
    f"{len(clean_text):,}"
)

audit_rows = []

for row in review_rows:

    turn_id = row.get(
        "turn_id",
        ""
    )

    dialogue = row.get(
        "dialogue_text",
        ""
    )

    before, matched, after = find_context(
        clean_text,
        dialogue
    )

    audit_rows.append(
        {
            "text_id": row.get(
                "text_id",
                ""
            ),

            "turn_id": turn_id,

            "speaker": row.get(
                "speaker",
                ""
            ),

            "dialogue_text": dialogue,

            "unit_type": row.get(
                "unit_type",
                ""
            ),

            "extraction_confidence": row.get(
                "extraction_confidence",
                ""
            ),

            "source": row.get(
                "source",
                ""
            ),

            "context_before": before,

            "matched_dialogue": matched,

            "context_after": after,
        }
    )


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
        "extraction_confidence",
        "source",
        "context_before",
        "matched_dialogue",
        "context_after",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(audit_rows)


print()
print("V5 REVIEW CONTEXT AUDIT COMPLETE")
print("---------------------------------")
print(
    f"Review turns audited: "
    f"{len(audit_rows):,}"
)

print(
    f"Output: {OUTPUT_FILE}"
)

print()
print("CONTEXT PREVIEW")
print("----------------")

for row in audit_rows:

    print()
    print("=" * 80)
    print(row["turn_id"])
    print("-" * 80)

    print("DIALOGUE:")
    print(
        row["dialogue_text"][:500]
    )

    print()
    print("BEFORE:")
    print(
        row["context_before"][-800:]
    )

    print()
    print("AFTER:")
    print(
        row["context_after"][:800]
    )

print()
print("No source files were modified.")