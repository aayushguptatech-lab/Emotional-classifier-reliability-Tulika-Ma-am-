import csv
from pathlib import Path
from collections import Counter


MASTER_FILE = Path(
    "data/final/english/the_valley_of_fear_master_v2.csv"
)

UNRESOLVED_FILE = Path(
    "data/final/english/the_valley_of_fear_master_unresolved.csv"
)

OUTPUT_FILE = Path(
    "data/final/english/the_valley_of_fear_master_v2_audit.csv"
)


with MASTER_FILE.open("r", encoding="utf-8", newline="") as f:
    master_reader = csv.DictReader(f)
    master_rows = list(master_reader)

with UNRESOLVED_FILE.open("r", encoding="utf-8", newline="") as f:
    unresolved_reader = csv.DictReader(f)
    unresolved_rows = list(unresolved_reader)


print("VOF MASTER V2 AUDIT")
print("===================")
print()

print(f"Master rows:       {len(master_rows):,}")
print(f"Unresolved rows:   {len(unresolved_rows):,}")


# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

required_columns = [
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

missing_columns = [
    column
    for column in required_columns
    if column not in master_reader.fieldnames
]

print()
print("Required-column check:")

if missing_columns:
    print("FAIL")
    print("Missing:", missing_columns)
else:
    print("PASS")


# ---------------------------------------------------------
# Row-count preservation
# ---------------------------------------------------------

print()
print("Row-count check:")

if len(master_rows) == 2872:
    print("PASS — 2,872 rows preserved")
else:
    print("FAIL")


# ---------------------------------------------------------
# Sentence ID uniqueness
# ---------------------------------------------------------

sentence_ids = [
    row["sentence_id"]
    for row in master_rows
]

duplicate_ids = [
    sid
    for sid, count in Counter(sentence_ids).items()
    if count > 1
]

print()
print("Sentence-ID uniqueness:")

if not duplicate_ids:
    print("PASS")
else:
    print(f"FAIL — duplicate IDs: {len(duplicate_ids)}")


# ---------------------------------------------------------
# Empty critical fields
# ---------------------------------------------------------

critical_fields = [
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
    "unit_type",
    "extraction_confidence",
    "source",
]

print()
print("Critical-field empty-value audit:")

empty_total = 0

for field in critical_fields:

    count = sum(
        1
        for row in master_rows
        if not row.get(field, "").strip()
    )

    if count:
        print(f"  {field}: {count}")
        empty_total += count

if empty_total == 0:
    print("PASS — no empty critical fields")
else:
    print(f"FAIL — {empty_total} empty values")


# ---------------------------------------------------------
# Chapter distribution
# ---------------------------------------------------------

chapter_counts = Counter(
    row["chapter"]
    for row in master_rows
)

print()
print("Chapter distribution:")
print("---------------------")

for chapter, count in chapter_counts.most_common():
    print(f"{chapter}: {count:,}")


# ---------------------------------------------------------
# Unresolved cases
# ---------------------------------------------------------

print()
print("UNRESOLVED CASES")
print("----------------")

print(f"Count: {len(unresolved_rows):,}")

for row in unresolved_rows:

    text = row["current_text"]

    if len(text) > 220:
        text = text[:220] + "..."

    print()
    print(
        f"{row['sentence_id']} | "
        f"{row['speaker']}"
    )
    print(f"  {text}")


# ---------------------------------------------------------
# Context integrity
# ---------------------------------------------------------

print()
print("Context integrity:")

context_errors = 0

rows_by_turn = {}

for row in master_rows:
    rows_by_turn.setdefault(
        row["turn_id"],
        []
    ).append(row)


for turn_id, turn_rows in rows_by_turn.items():

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
            context_errors += 1

        if row["next_text"] != expected_next:
            context_errors += 1


if context_errors == 0:
    print("PASS")
else:
    print(
        f"FAIL — {context_errors} context mismatches"
    )


# ---------------------------------------------------------
# Confidence distribution
# ---------------------------------------------------------

confidence_counts = Counter(
    row["extraction_confidence"]
    for row in master_rows
)

print()
print("Extraction-confidence distribution:")

for value, count in confidence_counts.items():
    print(f"  {value}: {count:,}")


# ---------------------------------------------------------
# Source consistency
# ---------------------------------------------------------

print()
print("Source consistency:")

sources = Counter(
    row["source"]
    for row in master_rows
)

for source, count in sources.items():
    print(f"  {source}: {count:,}")


# ---------------------------------------------------------
# Write audit summary
# ---------------------------------------------------------

audit_rows = [
    {
        "metric": "master_rows",
        "value": len(master_rows),
    },
    {
        "metric": "unresolved_rows",
        "value": len(unresolved_rows),
    },
    {
        "metric": "duplicate_sentence_ids",
        "value": len(duplicate_ids),
    },
    {
        "metric": "empty_critical_values",
        "value": empty_total,
    },
    {
        "metric": "context_errors",
        "value": context_errors,
    },
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=["metric", "value"],
    )

    writer.writeheader()
    writer.writerows(audit_rows)


print()
print("FINAL AUDIT FILE")
print("----------------")
print(OUTPUT_FILE)

print()
print("IMPORTANT:")
print("- No corpus file was modified.")
print("- master_v2.csv was NOT changed.")
print("- This step only audits the generated master.")