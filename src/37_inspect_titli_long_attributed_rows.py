
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)

OUTPUT = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_long_attributed_rows_inspection.txt"
)


def main():
    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    attributed = [
        r for r in rows
        if r.get("speaker_status") == "ATTRIBUTED"
    ]

    attributed.sort(
        key=lambda r: len(r.get("dialogue_text", "")),
        reverse=True,
    )

    selected = attributed[:24]

    lines = []

    lines.append("=" * 100)
    lines.append("TITLI LONG ATTRIBUTED ROWS INSPECTION")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Total reconstructed rows: {len(rows)}")
    lines.append(f"Attributed rows: {len(attributed)}")
    lines.append(f"Rows inspected: {len(selected)}")
    lines.append("")

    for i, row in enumerate(selected, start=1):
        dialogue = row.get("dialogue_text", "")

        lines.append("-" * 100)
        lines.append(f"ROW #{i}")
        lines.append(f"Candidate ID: {row.get('candidate_id', '')}")
        lines.append(f"Section: {row.get('section', '')}")
        lines.append(f"Source file: {row.get('source_file', '')}")
        lines.append(f"Speaker: {row.get('speaker', '')}")
        lines.append(f"Status: {row.get('speaker_status', '')}")
        lines.append(f"Dialogue length: {len(dialogue)}")
        lines.append("")
        lines.append("DIALOGUE:")
        lines.append(dialogue)
        lines.append("")

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("Titli long-row inspection complete.")
    print(f"Total reconstructed rows: {len(rows)}")
    print(f"Attributed rows: {len(attributed)}")
    print(f"Rows inspected: {len(selected)}")
    print(f"Inspection report: {OUTPUT}")


if __name__ == "__main__":
    main()
