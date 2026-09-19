import csv
from pathlib import Path
from collections import Counter

INPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_extraction_artifact_audit_v2.csv"
)

counter = Counter()

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        pattern = row.get("pattern", "")
        counter[pattern] += 1

print("ARTIFACT PATTERN COUNTS")
print("=======================")
print()

total = 0

for pattern, count in counter.most_common():
    print(f"{repr(pattern)} : {count}")
    total += count

print()
print(f"Total audit rows: {total}")