import csv
from pathlib import Path
from collections import Counter


MASTER_FILE = Path(
    "data/final/english/the_valley_of_fear_master_final.csv"
)

AUDIT_FILE = Path(
    "data/final/english/the_valley_of_fear_master_v2_audit.csv"
)

OUTPUT_FILE = Path(
    "data/final/english/the_valley_of_fear_freeze_report_final.csv"
)


with MASTER_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames


print("VOF FINAL FREEZE AUDIT")
print("======================")
print()

print(f"Rows: {len(rows):,}")


# ---------------------------------------------------------
# Frozen schema
# ---------------------------------------------------------

expected_fields = [
    "language",
    "text_id",
    "title",
    "author",
    "publication_year",
    "chapter",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "previous_text",
    "next_text",
    "unit_type",
    "extraction_confidence",
    "source",
]

schema_ok = fieldnames == expected_fields

print()
print("Schema:")
print("PASS" if schema_ok else "FAIL")


# ---------------------------------------------------------
# Stable sentence IDs
# ---------------------------------------------------------

sentence_ids = [
    row["sentence_id"]
    for row in rows
]

duplicate_ids = [
    sid
    for sid, count in Counter(sentence_ids).items()
    if count > 1
]

print()
print("Sentence IDs:")
print(
    "PASS — all unique"
    if not duplicate_ids
    else f"FAIL — {len(duplicate_ids)} duplicates"
)


# ---------------------------------------------------------
# Turn → sentence numbering
# ---------------------------------------------------------

turn_groups = {}

for row in rows:
    turn_groups.setdefault(
        row["turn_id"],
        []
    ).append(row)


numbering_errors = []

for turn_id, turn_rows in turn_groups.items():

    expected = 1

    for row in turn_rows:

        suffix = row["sentence_id"].split("_S")[-1]

        try:
            actual = int(suffix)
        except ValueError:
            numbering_errors.append(
                (turn_id, row["sentence_id"])
            )
            continue

        if actual != expected:
            numbering_errors.append(
                (turn_id, row["sentence_id"])
            )

        expected += 1


print()
print("Sentence numbering:")

if not numbering_errors:
    print("PASS")
else:
    print(
        f"FAIL — {len(numbering_errors)} numbering errors"
    )


# ---------------------------------------------------------
# Context integrity
# ---------------------------------------------------------

context_errors = []

for turn_id, turn_rows in turn_groups.items():

    for index, row in enumerate(turn_rows):

        expected_previous = ""

        if index > 0:
            expected_previous = turn_rows[index - 1][
                "current_text"
            ]

        expected_next = ""

        if index < len(turn_rows) - 1:
            expected_next = turn_rows[index + 1][
                "current_text"
            ]

        if row["previous_text"] != expected_previous:
            context_errors.append(
                (row["sentence_id"], "previous")
            )

        if row["next_text"] != expected_next:
            context_errors.append(
                (row["sentence_id"], "next")
            )


print()
print("Previous/next context:")

if not context_errors:
    print("PASS")
else:
    print(
        f"FAIL — {len(context_errors)} errors"
    )


# ---------------------------------------------------------
# T01179 repair
# ---------------------------------------------------------

repair_ids = {
    "VOF_T01179_A_S01",
    "VOF_T01179_B_S01",
}

repair_rows = {
    row["sentence_id"]: row
    for row in rows
    if row["sentence_id"] in repair_ids
}

original_repair_id_present = any(
    row["turn_id"] == "VOF_T01179"
    for row in rows
)

repair_ok = (
    len(repair_rows) == 2
    and not original_repair_id_present
    and repair_rows["VOF_T01179_A_S01"]["speaker"]
        == "McGinty"
    and repair_rows["VOF_T01179_B_S01"]["speaker"]
        == "McMurdo"
)

print()
print("T01179 repair:")

print(
    "PASS"
    if repair_ok
    else "FAIL"
)


# ---------------------------------------------------------
# Extraction confidence
# ---------------------------------------------------------

confidence_values = Counter(
    row["extraction_confidence"]
    for row in rows
)

allowed_confidence = {
    "high",
    "review",
}

invalid_confidence = [
    value
    for value in confidence_values
    if value not in allowed_confidence
]

print()
print("Extraction-confidence values:")

if not invalid_confidence:
    print("PASS")
else:
    print(
        f"FAIL — invalid values: {invalid_confidence}"
    )


# ---------------------------------------------------------
# Chapter labels
# ---------------------------------------------------------

chapters = Counter(
    row["chapter"]
    for row in rows
)

invalid_chapters = []

for chapter in chapters:

    if chapter == "Unresolved":
        continue

    if not chapter.startswith("PART I — Chapter ") and \
       not chapter.startswith("PART II — Chapter "):

        invalid_chapters.append(chapter)


print()
print("Chapter-label consistency:")

if not invalid_chapters:
    print("PASS")
else:
    print(
        f"FAIL — invalid labels: {invalid_chapters}"
    )


# ---------------------------------------------------------
# Unresolved source locations
# ---------------------------------------------------------

unresolved_count = sum(
    row["chapter"] == "Unresolved"
    for row in rows
)

print()
print("Unresolved source locations:")
print(f"{unresolved_count:,}")


# ---------------------------------------------------------
# Metadata consistency
# ---------------------------------------------------------

metadata_errors = []

for row in rows:

    if row["language"] != "English":
        metadata_errors.append(
            (row["sentence_id"], "language")
        )

    if row["text_id"] != "VOF":
        metadata_errors.append(
            (row["sentence_id"], "text_id")
        )

    if row["title"] != "The Valley of Fear":
        metadata_errors.append(
            (row["sentence_id"], "title")
        )

    if row["author"] != "Arthur Conan Doyle":
        metadata_errors.append(
            (row["sentence_id"], "author")
        )

    if row["publication_year"] != "1915":
        metadata_errors.append(
            (row["sentence_id"], "publication_year")
        )


print()
print("Metadata consistency:")

if not metadata_errors:
    print("PASS")
else:
    print(
        f"FAIL — {len(metadata_errors)} errors"
    )


# ---------------------------------------------------------
# Final verdict
# ---------------------------------------------------------

all_checks_pass = all([
    schema_ok,
    not duplicate_ids,
    not numbering_errors,
    not context_errors,
    repair_ok,
    not invalid_confidence,
    not invalid_chapters,
    not metadata_errors,
    len(rows) == 2872,
])


print()
print("FINAL FREEZE VERDICT")
print("====================")

if all_checks_pass:
    print("STRUCTURAL FREEZE AUDIT PASSED")
    print()
    print(
        "The VOF master is structurally ready "
        "for corpus freezing."
    )
else:
    print("FREEZE AUDIT FAILED")
    print()
    print(
        "Do NOT freeze the corpus until the "
        "failed checks are resolved."
    )


# ---------------------------------------------------------
# Write freeze report
# ---------------------------------------------------------

report_rows = [
    ("master_rows", len(rows)),
    ("unique_sentence_ids", len(sentence_ids) - len(duplicate_ids)),
    ("duplicate_sentence_ids", len(duplicate_ids)),
    ("turns", len(turn_groups)),
    ("numbering_errors", len(numbering_errors)),
    ("context_errors", len(context_errors)),
    ("t01179_repair_ok", repair_ok),
    ("invalid_confidence_values", len(invalid_confidence)),
    ("invalid_chapter_labels", len(invalid_chapters)),
    ("unresolved_source_locations", unresolved_count),
    ("metadata_errors", len(metadata_errors)),
    ("overall_freeze_audit", all_checks_pass),
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "metric",
        "value",
    ])

    writer.writerows(report_rows)


print()
print(f"Freeze report:")
print(OUTPUT_FILE)

print()
print("IMPORTANT:")
print("- Master corpus was NOT modified.")
print("- Sentence text was NOT modified.")
print("- Speaker assignments were NOT modified.")
print("- This is the final structural freeze audit only.")