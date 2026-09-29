from pathlib import Path
import csv

ANALYSIS_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_speaker_analysis.csv"
)

print("Inspecting unattributed MWT candidates...")

if not ANALYSIS_FILE.exists():
    raise FileNotFoundError(
        f"Analysis file not found: {ANALYSIS_FILE}"
    )

with ANALYSIS_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    rows = list(csv.DictReader(f))

unattributed = [
    row
    for row in rows
    if row["evidence_type"] == "none"
]

print()
print("UNATTRIBUTED CANDIDATES")
print("-----------------------")
print(f"Total: {len(unattributed):,}")

print()
print("First 60 examples:")
print("------------------")

for row in unattributed[:60]:

    preview = row["quoted_text"].replace(
        "\n",
        " "
    )

    if len(preview) > 300:
        preview = preview[:300] + "..."

    print(
        f'{row["candidate_id"]} | '
        f'lines {row["start_line"]}-{row["end_line"]} | '
        f'{preview}'
    )

print()
print("Unattributed-candidate inspection complete.")