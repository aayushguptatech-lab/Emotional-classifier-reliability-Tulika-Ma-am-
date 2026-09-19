import csv
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_valley_of_fear_internal_boundary_audit.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_valley_of_fear_internal_boundary_review.csv"
)


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


rows = read_csv(INPUT_FILE)

review_rows = []

for row in rows:

    dialogue = row.get(
        "dialogue_text",
        ""
    )

    internal = row.get(
        "internal_attributions",
        ""
    )

    review_rows.append(
        {
            "text_id": row.get(
                "text_id",
                ""
            ),
            "turn_id": row.get(
                "turn_id",
                ""
            ),
            "speaker": row.get(
                "speaker",
                ""
            ),
            "dialogue_text": dialogue,
            "internal_attributions": internal,
            "source_context": row.get(
                "source_context",
                ""
            ),
            "boundary_decision": "",
            "corrected_speaker": "",
            "review_notes": "",
        }
    )


fields = [
    "text_id",
    "turn_id",
    "speaker",
    "dialogue_text",
    "internal_attributions",
    "source_context",
    "boundary_decision",
    "corrected_speaker",
    "review_notes",
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fields
    )

    writer.writeheader()
    writer.writerows(review_rows)


print()
print("INTERNAL BOUNDARY REVIEW FILE CREATED")
print("---------------------------------------")
print(
    f"Cases prepared for review: {len(review_rows):,}"
)
print(
    f"Output: {OUTPUT_FILE}"
)

print()
print("Review columns added:")
print("- boundary_decision")
print("- corrected_speaker")
print("- review_notes")

print()
print("No existing corpus files were modified.")