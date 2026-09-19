import csv
import re
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_joined_word_direct_audit.csv"
)

# Specific patterns already observed during manual inspection.
TARGET_PATTERNS = [
    r"\bcheerycountry\b",
    r"\bIt’sas\b",
    r"\brattrap\b",
    r"\bworkmenwill\b",
    r"\bgood-nightto\b",
    r"\bGeorge,you\b",
    r"\bBirdyEdwards\b",
    r"\bthehouse\b",
    r"\bbeforeyou\b",
    r"\bhisvalise\b",
    r"\bsomeways\b",
    r"\bthenI’ll\b",
    r"\bthere isa\b",
    r"\baftera\b",
    r"\bthemall\b",
    r"\byourhands\b",
    r"\bseemedto\b",
    r"\basthe\b",
    r"\bconsciencecannot\b",
    r"\btobetter\b",
    r"\bwithoutanother\b",
    r"\bhiswife\b",
    r"\bgiveme\b",
    r"\btoyour\b",
]

combined_pattern = re.compile(
    "(" + "|".join(TARGET_PATTERNS) + ")"
)

rows = []

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        text = row.get("current_text", "")

        matches = combined_pattern.finditer(text)

        for match in matches:
            rows.append({
                "text_id": row["text_id"],
                "turn_id": row["turn_id"],
                "sentence_id": row["sentence_id"],
                "speaker": row["speaker"],
                "current_text": text,
                "matched_fragment": match.group(0),
                "start_position": match.start(),
                "end_position": match.end(),
                "decision": "",
                "review_notes": "",
            })

fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "matched_fragment",
    "start_position",
    "end_position",
    "decision",
    "review_notes",
]

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("DIRECT JOINED-WORD AUDIT")
print("========================")
print(f"Sentence rows scanned: {sum(1 for _ in open(INPUT_FILE, encoding='utf-8')) - 1:,}")
print(f"Potential matches:      {len(rows):,}")
print(f"Output: {OUTPUT_FILE}")
print()
print("No corpus file was modified.")