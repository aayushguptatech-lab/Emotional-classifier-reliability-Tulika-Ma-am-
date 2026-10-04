from pathlib import Path
import csv
import re


ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"

AUDIT_CSV = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)


def load_source():
    text = SOURCE_PATH.read_text(encoding="utf-8")

    header_re = re.compile(
        r"^===== TITLI SECTION "
        r"(?P<section>\d+\.\d+)"
        r" \| SOURCE "
        r"(?P<source_file>[^=]+?)"
        r" =====$"
    )

    paragraphs = []
    current_section = None
    global_index = 0

    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            continue

        match = header_re.fullmatch(line)

        if match:
            current_section = {
                "section": match.group("section"),
                "source_file": match.group("source_file"),
            }
            continue

        global_index += 1

        paragraphs.append(
            {
                "section": current_section["section"],
                "source_file": current_section["source_file"],
                "index": global_index,
                "text": line,
            }
        )

    return paragraphs


def main():
    paragraphs = load_source()

    lookup = {
        (p["section"], p["index"]): p
        for p in paragraphs
    }

    with AUDIT_CSV.open(
        encoding="utf-8",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    flagged_ids = {
        "TITLI-CAND-000014",
        "TITLI-CAND-000049",
        "TITLI-CAND-000069",
        "TITLI-CAND-000078",
        "TITLI-CAND-000092",
        "TITLI-CAND-000099",
        "TITLI-CAND-000100",
        "TITLI-CAND-000179",
        "TITLI-CAND-000191",
        "TITLI-CAND-000198",
        "TITLI-CAND-000202",
        "TITLI-CAND-000266",
        "TITLI-CAND-000267",
        "TITLI-CAND-000450",
        "TITLI-CAND-000504",
        "TITLI-CAND-000513",
        "TITLI-CAND-000589",
    }

    selected = [
        row
        for row in rows
        if row["candidate_id"] in flagged_ids
    ]

    selected.sort(
        key=lambda r: int(r["source_paragraph_index"])
    )

    print("=" * 100)
    print("TITLI FLAGGED-ROW SOURCE INSPECTION")
    print("=" * 100)

    for row in selected:
        key = (
            row["section"],
            int(row["source_paragraph_index"]),
        )

        source = lookup[key]

        print()
        print("=" * 100)
        print(f"Candidate: {row['candidate_id']}")
        print(f"Section: {row['section']}")
        print(f"Paragraph: {row['source_paragraph_index']}")
        print(f"Source file: {row['source_file']}")
        print(f"Speaker: {row['speaker']}")
        print(f"Status: {row['speaker_status']}")
        print(f"Dialogue length: {len(row['dialogue_text'])}")
        print("-" * 100)

        print("CANONICAL SOURCE PARAGRAPH:")
        print(source["text"])

        print("-" * 100)

        print("EXTRACTED DIALOGUE:")
        print(row["dialogue_text"])

        print("-" * 100)

        print("ATTRIBUTION TEXT:")
        print(row.get("attribution_text", ""))

        print("-" * 100)


if __name__ == "__main__":
    main()