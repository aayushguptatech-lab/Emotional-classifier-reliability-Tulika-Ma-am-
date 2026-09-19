import csv
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v2.csv"
)


# ---------------------------------------------------------
# Read sentence layer
# ---------------------------------------------------------

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("ADDING SENTENCE CONTEXT")
print("=======================")
print()
print(f"Input sentence rows: {len(rows):,}")


# ---------------------------------------------------------
# Group sentences by turn
#
# IMPORTANT:
# Previous/next context is generated ONLY inside the
# same speaker turn.
# ---------------------------------------------------------

sentences_by_turn = defaultdict(list)

for row in rows:
    sentences_by_turn[row["turn_id"]].append(row)


# ---------------------------------------------------------
# Add previous/current/next
# ---------------------------------------------------------

output_rows = []

for turn_id, turn_rows in sentences_by_turn.items():

    # Preserve the original sentence order from sentence_v1.
    for index, row in enumerate(turn_rows):

        previous_text = ""

        if index > 0:
            previous_text = turn_rows[index - 1]["current_text"]

        next_text = ""

        if index < len(turn_rows) - 1:
            next_text = turn_rows[index + 1]["current_text"]

        output_row = {
            "text_id": row["text_id"],
            "turn_id": row["turn_id"],
            "sentence_id": row["sentence_id"],
            "speaker": row["speaker"],
            "previous_text": previous_text,
            "current_text": row["current_text"],
            "next_text": next_text,
            "unit_type": row["unit_type"],
            "extraction_confidence": row["extraction_confidence"],
            "source": row["source"],
        }

        output_rows.append(output_row)


# ---------------------------------------------------------
# Safety checks
# ---------------------------------------------------------

input_sentence_ids = [row["sentence_id"] for row in rows]
output_sentence_ids = [row["sentence_id"] for row in output_rows]

if input_sentence_ids != output_sentence_ids:
    raise ValueError(
        "Sentence order or sentence IDs changed during context generation."
    )

if len(output_rows) != len(rows):
    raise ValueError(
        "Number of rows changed during context generation."
    )

if len(set(output_sentence_ids)) != len(output_sentence_ids):
    raise ValueError(
        "Duplicate sentence IDs detected in context output."
    )

# Verify that context never crosses a turn boundary.
for index, row in enumerate(output_rows):

    turn_rows = sentences_by_turn[row["turn_id"]]

    # Find this sentence inside its turn.
    local_index = next(
        i
        for i, turn_row in enumerate(turn_rows)
        if turn_row["sentence_id"] == row["sentence_id"]
    )

    expected_previous = ""

    if local_index > 0:
        expected_previous = turn_rows[local_index - 1]["current_text"]

    expected_next = ""

    if local_index < len(turn_rows) - 1:
        expected_next = turn_rows[local_index + 1]["current_text"]

    if row["previous_text"] != expected_previous:
        raise ValueError(
            f"Previous-context mismatch for {row['sentence_id']}"
        )

    if row["next_text"] != expected_next:
        raise ValueError(
            f"Next-context mismatch for {row['sentence_id']}"
        )


# ---------------------------------------------------------
# Write output
# ---------------------------------------------------------

fieldnames = [
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

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

first_sentence_count = sum(
    1
    for row in output_rows
    if row["previous_text"] == ""
)

last_sentence_count = sum(
    1
    for row in output_rows
    if row["next_text"] == ""
)

middle_sentence_count = len(output_rows) - (
    first_sentence_count + last_sentence_count
)

print()
print("CONTEXT GENERATION COMPLETE")
print("----------------------------")
print(f"Input sentence rows:       {len(rows):,}")
print(f"Output sentence rows:      {len(output_rows):,}")
print(f"Dialogue turns:            {len(sentences_by_turn):,}")
print(f"First sentence of turn:    {first_sentence_count:,}")
print(f"Middle sentence:           {middle_sentence_count:,}")
print(f"Last sentence of turn:     {last_sentence_count:,}")
print()
print(f"Output: {OUTPUT_FILE}")
print()
print("IMPORTANT:")
print("- sentence_v1.csv was NOT modified.")
print("- Context never crosses a speaker-turn boundary.")
print("- No annotation was performed.")