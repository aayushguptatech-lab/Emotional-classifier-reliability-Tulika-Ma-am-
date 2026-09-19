import csv
import re
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_extraction_artifact_audit_v2.csv"
)


# These patterns are intentionally conservative.
# They identify likely extraction/spacing artifacts.
# NOTHING is automatically repaired.


PATTERNS = [
    (
        "missing_space_after_comma",
        re.compile(r"[A-Za-z]{2,},[A-Za-z]{2,}")
    ),

    (
        "missing_space_after_semicolon",
        re.compile(r"[A-Za-z]{2,};[A-Za-z]{2,}")
    ),

    (
        "missing_space_after_colon",
        re.compile(r"[A-Za-z]{2,}:[A-Za-z]{2,}")
    ),

    (
        "missing_space_after_period",
        re.compile(r"[a-z]{2,}\.[A-Z][a-z]{1,}")
    ),

    (
        "joined_common_words",
        re.compile(
            r"\b(?:"
            r"beforeyou|"
            r"upall|"
            r"Icame|"
            r"Icould|"
            r"Iwould|"
            r"Ihad|"
            r"Iwas|"
            r"itis|"
            r"itwas|"
            r"ofit|"
            r"ofhim|"
            r"ofher|"
            r"ofme|"
            r"tothe|"
            r"thathe|"
            r"thatshe|"
            r"hewas|"
            r"shewas|"
            r"andhe|"
            r"andshe|"
            r"withthe|"
            r"forhim|"
            r"forher|"
            r"fromthe|"
            r"wifeand|"
            r"oweus|"
            r"tookit|"
            r"saidhe|"
            r"thatmight|"
            r"ahammer|"
            r"brillianceof|"
            r"downthe|"
            r"workmenwill|"
            r"ringand|"
            r"hisvalise|"
            r"yetI|"
            r"cangive|"
            r"youmy|"
            r"inthe|"
            r"itbutt|"
            r"tookit|"
            r"youmy"
            r")\b",
            re.IGNORECASE,
        ),
    ),

    (
        "missing_space_after_em_dash",
        re.compile(r"[A-Za-z]—[A-Za-z]")
    ),
]


def find_matches(text):
    matches = []

    for pattern_name, pattern in PATTERNS:
        for match in pattern.finditer(text):
            matches.append(
                {
                    "pattern": pattern_name,
                    "fragment": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    return matches


print("EXTRACTION ARTIFACT AUDIT V2")
print("============================")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


with INPUT_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    reader = csv.DictReader(f)
    rows = list(reader)


print(f"Sentence rows read: {len(rows):,}")


audit_rows = []


for row in rows:

    text = row.get("current_text", "")

    if not text:
        continue

    matches = find_matches(text)

    for match in matches:

        audit_rows.append(
            {
                "text_id": row.get("text_id", ""),
                "turn_id": row.get("turn_id", ""),
                "sentence_id": row.get("sentence_id", ""),
                "speaker": row.get("speaker", ""),
                "current_text": text,
                "pattern": match["pattern"],
                "fragment": match["fragment"],
                "start_position": match["start"],
                "end_position": match["end"],
                "suggested_spacing": "",
                "decision": "",
                "review_notes": "",
            }
        )


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "pattern",
    "fragment",
    "start_position",
    "end_position",
    "suggested_spacing",
    "decision",
    "review_notes",
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(audit_rows)


print()
print("ARTIFACT AUDIT V2 COMPLETE")
print("---------------------------")
print(f"Input sentence rows:  {len(rows):,}")
print(f"Potential artifacts:  {len(audit_rows):,}")
print(f"Output: {OUTPUT_FILE}")

print()
print("IMPORTANT:")
print("No source or corpus file was modified.")
print("All matches are REVIEW candidates only.")