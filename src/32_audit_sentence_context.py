import csv
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v2.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_context_audit.csv"
)

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("SENTENCE CONTEXT AUDIT")
print("======================")
print()
print(f"Rows read: {len(rows):,}")

# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

required_columns = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "previous_text",
    "current_text",
    "next_text",
    "unit_type",
    "extraction_confidence",
    "source",
]

missing_columns = [
    column for column in required_columns
    if column not in rows[0]
]

# ---------------------------------------------------------
# Group by turn
# ---------------------------------------------------------

sentences_by_turn = defaultdict(list)

for row in rows:
    sentences_by_turn[row["turn_id"]].append(row)

# ---------------------------------------------------------
# Check context
# ---------------------------------------------------------

problems = []

for turn_id, turn_rows in sentences_by_turn.items():

    for index, row in enumerate(turn_rows):

        expected_previous = ""

        if index > 0:
            expected_previous = turn_rows[index - 1]["current_text"]

        expected_next = ""

        if index < len(turn_rows) - 1:
            expected_next = turn_rows[index + 1]["current_text"]

        # First sentence must have no previous context.
        if index == 0 and row["previous_text"] != "":
            problems.append({
                "sentence_id": row["sentence_id"],
                "turn_id": turn_id,
                "problem": "first_sentence_has_previous_context",
                "details": row["previous_text"],
            })

        # Last sentence must have no next context.
        if index == len(turn_rows) - 1 and row["next_text"] != "":
            problems.append({
                "sentence_id": row["sentence_id"],
                "turn_id": turn_id,
                "problem": "last_sentence_has_next_context",
                "details": row["next_text"],
            })

        # Check exact previous sentence.
        if row["previous_text"] != expected_previous:
            problems.append({
                "sentence_id": row["sentence_id"],
                "turn_id": turn_id,
                "problem": "previous_context_mismatch",
                "details": (
                    f"expected={expected_previous!r} | "
                    f"actual={row['previous_text']!r}"
                ),
            })

        # Check exact next sentence.
        if row["next_text"] != expected_next:
            problems.append({
                "sentence_id": row["sentence_id"],
                "turn_id": turn_id,
                "problem": "next_context_mismatch",
                "details": (
                    f"expected={expected_next!r} | "
                    f"actual={row['next_text']!r}"
                ),
            })

# ---------------------------------------------------------
# Check sentence IDs and row count
# ---------------------------------------------------------

sentence_ids = [row["sentence_id"] for row in rows]

duplicate_sentence_ids = sorted({
    sentence_id
    for sentence_id in sentence_ids
    if sentence_ids.count(sentence_id) > 1
})

if len(sentence_ids) != 2872:
    problems.append({
        "sentence_id": "",
        "turn_id": "",
        "problem": "unexpected_row_count",
        "details": f"Expected 2872, found {len(sentence_ids)}",
    })

if duplicate_sentence_ids:
    problems.append({
        "sentence_id": "",
        "turn_id": "",
        "problem": "duplicate_sentence_ids",
        "details": str(duplicate_sentence_ids),
    })

# ---------------------------------------------------------
# Check T01179 repair
# ---------------------------------------------------------

repair_rows = [
    row for row in rows
    if row["turn_id"] in {"VOF_T01179_A", "VOF_T01179_B"}
]

expected_repairs = {
    "VOF_T01179_A": "McGinty",
    "VOF_T01179_B": "McMurdo",
}

for row in repair_rows:
    expected_speaker = expected_repairs[row["turn_id"]]

    if row["speaker"] != expected_speaker:
        problems.append({
            "sentence_id": row["sentence_id"],
            "turn_id": row["turn_id"],
            "problem": "T01179_speaker_mismatch",
            "details": (
                f"expected={expected_speaker!r} | "
                f"actual={row['speaker']!r}"
            ),
        })

# ---------------------------------------------------------
# Check required columns
# ---------------------------------------------------------

if missing_columns:
    problems.append({
        "sentence_id": "",
        "turn_id": "",
        "problem": "missing_required_columns",
        "details": str(missing_columns),
    })

# ---------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------

first_sentence_count = sum(
    1
    for turn_rows in sentences_by_turn.values()
    if turn_rows
)

last_sentence_count = sum(
    1
    for turn_rows in sentences_by_turn.values()
    if turn_rows
)

middle_sentence_count = sum(
    max(0, len(turn_rows) - 2)
    for turn_rows in sentences_by_turn.values()
)

print()
print("Context-position counts:")
print(f"First sentence of turn: {first_sentence_count:,}")
print(f"Middle sentences:       {middle_sentence_count:,}")
print(f"Last sentence of turn:  {last_sentence_count:,}")

print()
print("T01179 repair rows:")

for row in repair_rows:
    print(
        f"  {row['sentence_id']} | "
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['current_text']}"
    )

# ---------------------------------------------------------
# Final verdict
# ---------------------------------------------------------

print()
print("FINAL CONTEXT VERDICT")
print("=====================")

if problems:
    print("REVIEW REQUIRED")
    print()
    print(f"Problems detected: {len(problems)}")

    for problem in problems[:25]:
        print(
            f"- {problem['problem']} | "
            f"{problem['turn_id']} | "
            f"{problem['sentence_id']} | "
            f"{problem['details']}"
        )

    if len(problems) > 25:
        print()
        print(
            f"... plus {len(problems) - 25} additional problems."
        )

else:
    print("CONTEXT AUDIT PASSED")
    print()
    print("All previous/current/next relationships are valid.")
    print("Context does not cross dialogue-turn boundaries.")

# ---------------------------------------------------------
# Save audit
# ---------------------------------------------------------

fieldnames = [
    "sentence_id",
    "turn_id",
    "problem",
    "details",
]

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(problems)

print()
print(f"Audit saved to: {OUTPUT_FILE}")
print()
print("IMPORTANT:")
print("- sentence_v2.csv was NOT modified.")
print("- No context values were changed.")
print("- No annotation was performed.")