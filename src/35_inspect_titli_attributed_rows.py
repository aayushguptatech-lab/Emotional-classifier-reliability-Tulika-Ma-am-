import csv
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "extracted" / "hindi" / "titli" / "titli_dialogue_turns_attributed.csv"
OUTPUT = ROOT / "data" / "extracted" / "hindi" / "titli" / "titli_attributed_rows_inspection.txt"


def main():
    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    attributed = [
        r for r in rows
        if r.get("speaker_status") == "ATTRIBUTED"
    ]

    speakers = Counter(r.get("speaker", "").strip() for r in attributed)

    lines = []

    lines.append("=" * 100)
    lines.append("TITLI ATTRIBUTED-ROW INSPECTION")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Total reconstructed rows: {len(rows)}")
    lines.append(f"Attributed rows: {len(attributed)}")
    lines.append(f"Unknown rows: {len(rows) - len(attributed)}")
    lines.append(f"Unique attributed speakers: {len(speakers)}")
    lines.append("")
    lines.append("Speaker distribution:")
    lines.append("-" * 100)

    for speaker, count in speakers.most_common():
        lines.append(f"{speaker}: {count}")

    lines.append("")
    lines.append("=" * 100)
    lines.append("ALL ATTRIBUTED ROWS")
    lines.append("=" * 100)

    for i, row in enumerate(attributed, start=1):
        lines.append("")
        lines.append("-" * 100)
        lines.append(f"Attributed row #{i}")
        lines.append(f"Candidate ID: {row.get('candidate_id', '')}")
        lines.append(f"Section: {row.get('section', '')}")
        lines.append(f"Paragraph: {row.get('paragraph_index', '')}")
        lines.append(f"Source file: {row.get('source_file', '')}")
        lines.append(f"Speaker: {row.get('speaker', '')}")
        lines.append(f"Status: {row.get('speaker_status', '')}")
        lines.append(f"Dialogue length: {len(row.get('dialogue_text', ''))}")
        lines.append(f"Detection method: {row.get('detection_method', '')}")
        lines.append(f"Attribution text: {row.get('attribution_text', '')}")
        lines.append("")
        lines.append("DIALOGUE:")
        lines.append(row.get("dialogue_text", ""))

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print("Titli attributed-row inspection complete.")
    print(f"Total rows: {len(rows)}")
    print(f"Attributed rows: {len(attributed)}")
    print(f"Unknown rows: {len(rows) - len(attributed)}")
    print(f"Unique speakers: {len(speakers)}")
    print(f"Inspection report: {OUTPUT}")


if __name__ == "__main__":
    main()