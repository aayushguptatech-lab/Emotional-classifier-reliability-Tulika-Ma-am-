import csv
from collections import Counter
from pathlib import Path

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
	
ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "extracted" / "hindi" / "kankal" / "kankal_dialogue_turns_attributed.csv"
OUTPUT_PATH = ROOT / "data" / "final" / "hindi" / "kankal_dialogue_final.csv"
EXPECTED_ROWS = 317
EXPECTED_SPEAKERS = 10


def read_csv(path):
	with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
		reader = csv.DictReader(csv_file)
		if reader.fieldnames is None:
			raise ValueError(f"CSV has no header: {path}")
		return reader.fieldnames, list(reader)


def main():
	fieldnames, source_rows = read_csv(INPUT_PATH)
	required_fields = {"turn_id", "speaker", "speaker_status", "dialogue_text"}
	missing_fields = required_fields.difference(fieldnames)
	if missing_fields:
		raise ValueError(f"Input is missing required fields: {sorted(missing_fields)}")

	final_rows = [row for row in source_rows if row["speaker_status"] == "ATTRIBUTED"]
	if len(final_rows) != EXPECTED_ROWS:
		raise ValueError(f"Expected {EXPECTED_ROWS} attributed rows, found {len(final_rows)}")
	if any(not row["speaker"].strip() or row["speaker"] == "Unknown" for row in final_rows):
		raise ValueError("Final rows contain an empty or Unknown speaker")
	if any(not row["dialogue_text"].strip() for row in final_rows):
		raise ValueError("Final rows contain empty dialogue text")

	turn_ids = [row["turn_id"] for row in final_rows]
	if len(turn_ids) != len(set(turn_ids)):
		raise ValueError("Final rows contain duplicate turn IDs")

	speakers = {row["speaker"] for row in final_rows}
	if len(speakers) != EXPECTED_SPEAKERS:
		raise ValueError(f"Expected {EXPECTED_SPEAKERS} speakers, found {len(speakers)}")

	dialogue_counts = Counter(row["dialogue_text"] for row in final_rows)
	duplicate_dialogue_groups = sum(count > 1 for count in dialogue_counts.values())
	duplicate_dialogue_rows = sum(count for count in dialogue_counts.values() if count > 1)

	with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
		writer.writeheader()
		writer.writerows(final_rows)

	output_fields, written_rows = read_csv(OUTPUT_PATH)
	if output_fields != fieldnames or written_rows != final_rows:
		raise ValueError("Written CSV does not exactly preserve selected source rows")
	if Counter(row["dialogue_text"] for row in written_rows) != dialogue_counts:
		raise ValueError("Repeated dialogue was not preserved")

	speaker_counts = Counter(row["speaker"] for row in written_rows)
	print(f"PASS: wrote {len(written_rows)} attributed rows to {OUTPUT_PATH.relative_to(ROOT)}")
	print(f"PASS: {len(speaker_counts)} unique speakers; no empty/Unknown speakers or empty dialogue")
	print(f"PASS: turn IDs unique; all {len(fieldnames)} source columns preserved in source order")
	print(
		"PASS: preserved repeated dialogue "
		f"({duplicate_dialogue_groups} groups, {duplicate_dialogue_rows} rows involved)"
	)
	for speaker, count in sorted(speaker_counts.items()):
		print(f"{speaker}={count}")


if __name__ == "__main__":
	main()
