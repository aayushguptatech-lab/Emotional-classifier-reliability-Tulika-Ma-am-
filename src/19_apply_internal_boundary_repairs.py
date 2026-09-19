import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v6.csv"
)


# ---------------------------------------------------------
# Controlled repairs identified during the internal-boundary
# audit.
#
# T00431: speaker incorrectly recovered as "he"
# T00433: speaker was Unknown but source attribution identifies
#         White Mason
# T01179: one V5 turn actually contains TWO top-level speakers
# ---------------------------------------------------------

SPEAKER_REPAIRS = {
    "VOF_T00431": "the inspector",
    "VOF_T00433": "White Mason",
}


SPLIT_TURN_ID = "VOF_T01179"

SPLIT_FIRST_TEXT = "Now, McMurdo!"

SPLIT_SECOND_TEXT = (
    "I said just now that I knew Birdy Edwards,"
)


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)


print("Reading V5 dialogue turns...")

rows = read_csv(INPUT_FILE)

print(f"V5 turns read: {len(rows):,}")


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


# ---------------------------------------------------------
# Prepare output schema.
#
# parent_turn_id is added only to preserve lineage for the
# genuine split at T01179.
# repair_note records exactly why a controlled repair occurred.
# ---------------------------------------------------------

fieldnames = list(rows[0].keys())

if "parent_turn_id" not in fieldnames:
    fieldnames.append("parent_turn_id")

if "repair_note" not in fieldnames:
    fieldnames.append("repair_note")


output_rows = []

speaker_repairs_applied = 0
split_repairs_applied = 0


for row in rows:

    turn_id = row["turn_id"]

    # -----------------------------------------------------
    # Repair 1 and 2:
    # Correct speaker recovery while preserving the turn.
    # -----------------------------------------------------

    if turn_id in SPEAKER_REPAIRS:

        old_speaker = row["speaker"]
        new_speaker = SPEAKER_REPAIRS[turn_id]

        row["speaker"] = new_speaker
        row["extraction_confidence"] = "high"

        row["parent_turn_id"] = ""
        row["repair_note"] = (
            f"Controlled speaker repair: "
            f"{old_speaker} -> {new_speaker}; "
            f"supported by internal-boundary/source-context audit."
        )

        speaker_repairs_applied += 1

        output_rows.append(row)

        continue


    # -----------------------------------------------------
    # Repair 3:
    # T01179 contains a genuine top-level speaker boundary.
    #
    # V5 incorrectly represented:
    #
    #   McGinty: "Now, McMurdo!"
    #   McMurdo: "I said just now that I knew Birdy Edwards,"
    #
    # as one Unknown turn.
    #
    # We therefore create TWO new child turn IDs.
    # The original V5 turn ID is preserved as parent_turn_id.
    # -----------------------------------------------------

    if turn_id == SPLIT_TURN_ID:

        original_text = row["dialogue_text"].strip()

        expected_text = (
            SPLIT_FIRST_TEXT + " " + SPLIT_SECOND_TEXT
        )

        if original_text != expected_text:
            raise ValueError(
                "\nUnexpected T01179 dialogue text.\n"
                f"Expected:\n{expected_text!r}\n"
                f"Found:\n{original_text!r}\n"
                "\nNo V6 file has been written."
            )

        # First child turn: McGinty
        first_row = row.copy()

        first_row["turn_id"] = "VOF_T01179_A"
        first_row["speaker"] = "McGinty"
        first_row["dialogue_text"] = SPLIT_FIRST_TEXT
        first_row["extraction_confidence"] = "high"
        first_row["parent_turn_id"] = SPLIT_TURN_ID
        first_row["repair_note"] = (
            "Controlled split of V5 T01179: "
            "first top-level speaker segment identified as McGinty."
        )

        # Second child turn: McMurdo
        second_row = row.copy()

        second_row["turn_id"] = "VOF_T01179_B"
        second_row["speaker"] = "McMurdo"
        second_row["dialogue_text"] = SPLIT_SECOND_TEXT
        second_row["extraction_confidence"] = "high"
        second_row["parent_turn_id"] = SPLIT_TURN_ID
        second_row["repair_note"] = (
            "Controlled split of V5 T01179: "
            "second top-level speaker segment identified as McMurdo."
        )

        output_rows.append(first_row)
        output_rows.append(second_row)

        split_repairs_applied += 1

        continue


    # -----------------------------------------------------
    # All other V5 rows are copied unchanged.
    # -----------------------------------------------------

    row["parent_turn_id"] = ""
    row["repair_note"] = ""

    output_rows.append(row)


# ---------------------------------------------------------
# Final safety checks
# ---------------------------------------------------------

expected_output_count = len(rows) + 1

if len(output_rows) != expected_output_count:
    raise ValueError(
        f"Unexpected V6 row count: {len(output_rows)}. "
        f"Expected {expected_output_count}."
    )


# Ensure repaired IDs exist exactly once.
output_ids = [row["turn_id"] for row in output_rows]

if output_ids.count("VOF_T01179_A") != 1:
    raise ValueError("VOF_T01179_A was not created exactly once.")

if output_ids.count("VOF_T01179_B") != 1:
    raise ValueError("VOF_T01179_B was not created exactly once.")

# The original split turn must not remain as an active V6 turn.
if "VOF_T01179" in output_ids:
    raise ValueError(
        "Original V5 split turn ID VOF_T01179 "
        "incorrectly remains as a V6 turn."
    )


write_csv(
    OUTPUT_FILE,
    output_rows,
    fieldnames
)


print()
print("V6 INTERNAL-BOUNDARY REPAIR COMPLETE")
print("-------------------------------------")
print(f"V5 input turns:       {len(rows):,}")
print(f"V6 output turns:      {len(output_rows):,}")
print(f"Speaker repairs:      {speaker_repairs_applied}")
print(f"Turn splits:          {split_repairs_applied}")
print()
print("Repairs applied:")
print("  VOF_T00431 -> the inspector")
print("  VOF_T00433 -> White Mason")
print("  VOF_T01179 -> split into:")
print("      VOF_T01179_A -> McGinty")
print("      VOF_T01179_B -> McMurdo")
print()
print(f"Output: {OUTPUT_FILE}")
print()
print("V5 was NOT modified.")
print("Sentence segmentation was NOT performed.")