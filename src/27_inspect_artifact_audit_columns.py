import csv
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_extraction_artifact_audit_v2.csv"
)

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    print("ARTIFACT AUDIT CSV STRUCTURE")
    print("============================")
    print("Columns found:")
    print()

    for column in reader.fieldnames:
        print(f"  {repr(column)}")

    print()
    first_row = next(reader, None)

    if first_row:
        print("First row:")
        print()
        for key, value in first_row.items():
            print(f"{repr(key)} = {repr(value)}")