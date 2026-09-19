import csv
from pathlib import Path
from collections import Counter, defaultdict

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_structure_audit.csv"
)


with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)


print("SENTENCE STRUCTURAL AUDIT")
print("=========================")
print()

# ---------------------------------------------------------
# 1. Basic counts
# ---------------------------------------------------------

print(f"Sentence rows: {len(rows):,}")

turn_ids = [row["turn_id"] for row in rows]
sentence_ids = [row["sentence_id"] for row in rows]

print(f"Unique turn IDs: {len(set(turn_ids)):,}")
print(f"Unique sentence IDs: {len(set(sentence_ids)):,}")


# ---------------------------------------------------------
# 2. Required columns
# ---------------------------------------------------------

required_columns = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "unit_type",
    "extraction_confidence",
    "source",
]

missing_columns = [
    column for column in required_columns
    if column not in rows[0]
]

print()
print("Required-column check:")

if missing_columns:
    print("FAIL")
    print("Missing columns:", missing_columns)
else:
    print("PASS")


# ---------------------------------------------------------
# 3. Empty values
# ---------------------------------------------------------

empty_current_text = []
empty_turn_id = []
empty_sentence_id = []
empty_speaker = []

for row in rows:
    if not row["current_text"].strip():
        empty_current_text.append(row["sentence_id"])

    if not row["turn_id"].strip():
        empty_turn_id.append(row["sentence_id"])

    if not row["sentence_id"].strip():
        empty_sentence_id.append(row["sentence_id"])

    if not row["speaker"].strip():
        empty_speaker.append(row["sentence_id"])


print()
print("Empty-value checks:")
print(f"Empty current_text: {len(empty_current_text)}")
print(f"Empty turn_id:      {len(empty_turn_id)}")
print(f"Empty sentence_id:  {len(empty_sentence_id)}")
print(f"Empty speaker:      {len(empty_speaker)}")


# ---------------------------------------------------------
# 4. Duplicate sentence IDs
# ---------------------------------------------------------

sentence_counter = Counter(sentence_ids)

duplicate_sentence_ids = [
    sentence_id
    for sentence_id, count in sentence_counter.items()
    if count > 1
]

print()
print("Duplicate sentence-ID check:")
print(f"Duplicate sentence IDs: {len(duplicate_sentence_ids)}")


# ---------------------------------------------------------
# 5. Sentences per turn
# ---------------------------------------------------------

turn_sentence_counts = Counter(turn_ids)

zero_sentence_turns = []

# All turns represented in the sentence file naturally have
# at least one sentence. This check is retained for clarity.
for turn_id, count in turn_sentence_counts.items():
    if count == 0:
        zero_sentence_turns.append(turn_id)

print()
print("Turn-to-sentence check:")
print(f"Turns represented: {len(turn_sentence_counts):,}")
print(f"Turns with zero sentences: {len(zero_sentence_turns)}")


# ---------------------------------------------------------
# 6. Sentence numbering
# ---------------------------------------------------------

bad_sentence_numbering = []

sentences_by_turn = defaultdict(list)

for row in rows:
    sentences_by_turn[row["turn_id"]].append(row["sentence_id"])


for turn_id, ids in sentences_by_turn.items():

    expected_numbers = list(range(1, len(ids) + 1))

    actual_numbers = []

    for sentence_id in ids:
        suffix = sentence_id.rsplit("_S", 1)[-1]

        try:
            actual_numbers.append(int(suffix))
        except ValueError:
            bad_sentence_numbering.append(
                (turn_id, sentence_id, "invalid_suffix")
            )

    if actual_numbers != expected_numbers:
        bad_sentence_numbering.append(
            (
                turn_id,
                ",".join(ids),
                f"expected={expected_numbers}, actual={actual_numbers}",
            )
        )


print()
print("Sentence-numbering check:")
print(f"Turns with numbering problems: {len(bad_sentence_numbering)}")


# ---------------------------------------------------------
# 7. Parent-turn repair check
# ---------------------------------------------------------

repair_ids = {
    "VOF_T01179_A",
    "VOF_T01179_B",
}

repair_rows = [
    row for row in rows
    if row["turn_id"] in repair_ids
]

print()
print("T01179 repair check:")
print(f"Repair sentence rows found: {len(repair_rows)}")

for row in repair_rows:
    print(
        f"  {row['sentence_id']} | "
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['current_text']}"
    )


# ---------------------------------------------------------
# 8. Expected V6 turn coverage
# ---------------------------------------------------------

V6_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v6.csv"
)

with V6_FILE.open("r", encoding="utf-8", newline="") as f:
    v6_reader = csv.DictReader(f)
    v6_rows = list(v6_reader)

v6_turn_ids = set(row["turn_id"] for row in v6_rows)
sentence_turn_ids = set(turn_ids)

missing_turns = sorted(v6_turn_ids - sentence_turn_ids)
extra_turns = sorted(sentence_turn_ids - v6_turn_ids)

print()
print("V6-to-sentence coverage check:")
print(f"V6 turns:                    {len(v6_turn_ids):,}")
print(f"Sentence-file turn IDs:      {len(sentence_turn_ids):,}")
print(f"V6 turns missing sentences:  {len(missing_turns)}")
print(f"Unexpected extra turn IDs:   {len(extra_turns)}")


# ---------------------------------------------------------
# 9. Confidence values
# ---------------------------------------------------------

confidence_counts = Counter(
    row["extraction_confidence"]
    for row in rows
)

print()
print("Extraction-confidence values:")

for value, count in confidence_counts.items():
    print(f"  {repr(value)} : {count}")


# ---------------------------------------------------------
# 10. Final verdict
# ---------------------------------------------------------

problems = []

if missing_columns:
    problems.append("missing required columns")

if empty_current_text:
    problems.append("empty current_text")

if empty_turn_id:
    problems.append("empty turn_id")

if empty_sentence_id:
    problems.append("empty sentence_id")

if duplicate_sentence_ids:
    problems.append("duplicate sentence IDs")

if bad_sentence_numbering:
    problems.append("sentence numbering problems")

if missing_turns:
    problems.append("V6 turns missing from sentence file")

if extra_turns:
    problems.append("unexpected extra turn IDs")


print()
print("FINAL STRUCTURAL VERDICT")
print("========================")

if problems:
    print("REVIEW REQUIRED")
    print()
    for problem in problems:
        print(f"- {problem}")
else:
    print("STRUCTURAL AUDIT PASSED")
    print()
    print("No structural problems were detected.")


# ---------------------------------------------------------
# 11. Write machine-readable audit summary
# ---------------------------------------------------------

audit_rows = [
    {
        "check": "required_columns",
        "status": "PASS" if not missing_columns else "FAIL",
        "details": (
            "All required columns present"
            if not missing_columns
            else str(missing_columns)
        ),
    },
    {
        "check": "empty_current_text",
        "status": "PASS" if not empty_current_text else "FAIL",
        "details": str(len(empty_current_text)),
    },
    {
        "check": "empty_turn_id",
        "status": "PASS" if not empty_turn_id else "FAIL",
        "details": str(len(empty_turn_id)),
    },
    {
        "check": "empty_sentence_id",
        "status": "PASS" if not empty_sentence_id else "FAIL",
        "details": str(len(empty_sentence_id)),
    },
    {
        "check": "duplicate_sentence_ids",
        "status": "PASS" if not duplicate_sentence_ids else "FAIL",
        "details": str(len(duplicate_sentence_ids)),
    },
    {
        "check": "sentence_numbering",
        "status": "PASS" if not bad_sentence_numbering else "FAIL",
        "details": str(len(bad_sentence_numbering)),
    },
    {
        "check": "v6_turn_coverage",
        "status": "PASS" if not missing_turns and not extra_turns else "FAIL",
        "details": (
            f"missing={len(missing_turns)}, "
            f"extra={len(extra_turns)}"
        ),
    },
]

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["check", "status", "details"]
    )
    writer.writeheader()
    writer.writerows(audit_rows)


print()
print(f"Audit summary saved to: {OUTPUT_FILE}")
print()
print("IMPORTANT:")
print("- No corpus file was modified.")
print("- sentence_v1.csv was NOT changed.")
print("- Previous/next context was NOT generated.")