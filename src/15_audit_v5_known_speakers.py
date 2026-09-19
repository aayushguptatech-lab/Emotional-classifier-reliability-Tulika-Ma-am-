import csv
import re
from pathlib import Path

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

V5_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_v5_known_speaker_audit.csv"
)


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def normalize_for_search(text):
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_context(text, dialogue, window=500):

    normalized_text = normalize_for_search(text)
    normalized_dialogue = normalize_for_search(dialogue)

    if not normalized_dialogue:
        return "", "", ""

    position = normalized_text.find(
        normalized_dialogue
    )

    if position == -1:

        words = normalized_dialogue.split()

        for keep_words in [50, 40, 30, 20, 15, 10]:

            if len(words) < keep_words:
                continue

            candidate = " ".join(
                words[:keep_words]
            )

            position = normalized_text.find(
                candidate
            )

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

    before = normalized_text[
        start:position
    ]

    matched = normalized_text[
        position:
        position + len(normalized_dialogue)
    ]

    after = normalized_text[
        position + len(normalized_dialogue):
        end
    ]

    return before, matched, after


print("Reading V5...")

rows = read_csv(V5_FILE)

print(
    f"Total V5 turns: {len(rows):,}"
)

known_rows = [
    row
    for row in rows
    if row.get("speaker", "").strip()
    and row.get("speaker", "").strip() != "Unknown"
]

print(
    f"Known-speaker turns: {len(known_rows):,}"
)

print()
print("Reading cleaned novel...")

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

audit_rows = []

for row in known_rows:

    before, matched, after = find_context(
        clean_text,
        row.get("dialogue_text", "")
    )

    audit_rows.append(
        {
            "text_id": row.get("text_id", ""),
            "turn_id": row.get("turn_id", ""),
            "speaker": row.get("speaker", ""),
            "dialogue_text": row.get("dialogue_text", ""),
            "context_before": before,
            "matched_dialogue": matched,
            "context_after": after,
        }
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
print("KNOWN SPEAKER AUDIT COMPLETE")
print("-----------------------------")
print(
    f"Known-speaker turns audited: "
    f"{len(audit_rows):,}"
)

print(
    f"Output: {OUTPUT_FILE}"
)

print()
print("FIRST 40 KNOWN-SPEAKER CASES")
print("-----------------------------")

for row in audit_rows[:40]:

    print()
    print("=" * 80)
    print(row["turn_id"])
    print("ASSIGNED SPEAKER:", row["speaker"])
    print("-" * 80)

    print("DIALOGUE:")
    print(
        row["dialogue_text"][:500]
    )

    print()
    print("BEFORE:")
    print(
        row["context_before"][-500:]
    )

    print()
    print("AFTER:")
    print(
        row["context_after"][:500]
    )

print()
print("No source files were modified.")