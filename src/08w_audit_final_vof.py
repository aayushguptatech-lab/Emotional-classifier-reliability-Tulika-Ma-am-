from pathlib import Path
import csv
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FINAL = DATA / "final" / "english" / "the_valley_of_fear_final_corpus.csv"
CLEAN = DATA / "cleaned" / "english" / "the_valley_of_fear_clean.txt"

REPORT = DATA / "final" / "english" / "the_valley_of_fear_final_audit.txt"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    rows = read_csv(FINAL)
    source = CLEAN.read_text(encoding="utf-8")

    ids = [r["turn_id"] for r in rows]
    dialogues = [r["dialogue_text"] for r in rows]
    speakers = [r["speaker"] for r in rows]

    duplicate_ids = [
        x for x, n in Counter(ids).items() if n > 1
    ]

    empty = [
        r["turn_id"] for r in rows
        if not r["dialogue_text"].strip()
    ]

    unknown = sum(s == "Unknown" for s in speakers)
    known = len(rows) - unknown

    lowercase_titles = len(
        re.findall(r"\b(?:mr|mrs|dr|st)\.", source)
    )

    missing_fields = []
    required = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
        "extraction_confidence",
        "source",
    ]

    for i, row in enumerate(rows, 1):
        for field in required:
            if field not in row:
                missing_fields.append((i, field))

    suspicious = []

    for row in rows:
        text = row["dialogue_text"].strip()

        if len(text) > 1000:
            suspicious.append(
                (row["turn_id"], "very_long", len(text))
            )

        if re.search(r"\b(?:mr|mrs|dr|st)\.", text):
            suspicious.append(
                (row["turn_id"], "lowercase_title", text)
            )

    report = [
        "=" * 72,
        "THE VALLEY OF FEAR — FINAL AUDIT",
        "=" * 72,
        "",
        "1. CORPUS SIZE",
        "-" * 72,
        f"Rows:                    {len(rows)}",
        f"Unique turn IDs:         {len(set(ids))}",
        f"Duplicate turn IDs:     {len(duplicate_ids)}",
        f"Empty dialogue rows:     {len(empty)}",
        "",
        "2. SPEAKER ATTRIBUTION",
        "-" * 72,
        f"Known speakers:          {known}",
        f"Unknown speakers:        {unknown}",
        f"Unknown percentage:      {unknown / len(rows) * 100:.2f}%",
        "",
        "3. CANONICAL TEXT",
        "-" * 72,
        f"Source characters:        {len(source)}",
        f"Mr. occurrences:         {len(re.findall(r"Mr\.", source))}",
        f"Mrs. occurrences:        {len(re.findall(r"Mrs\.", source))}",
        f"Dr. occurrences:         {len(re.findall(r"Dr\.", source))}",
        f"St. occurrences:         {len(re.findall(r"St\.", source))}",
        f"Lowercase title forms:   {lowercase_titles}",
        "",
        "4. SCHEMA",
        "-" * 72,
        f"Missing required fields: {len(missing_fields)}",
        "",
        "5. LONG / SUSPICIOUS RECORDS",
        "-" * 72,
        f"Records flagged:         {len(suspicious)}",
        f"Records >1000 chars:     {sum(x[1] == 'very_long' for x in suspicious)}",
        f"Lowercase-title flags:   {sum(x[1] == 'lowercase_title' for x in suspicious)}",
        "",
        "6. REPRODUCIBILITY",
        "-" * 72,
        "Final corpus producer:",
        "src/08v_build_final_vof_corpus.py",
        "",
        "Canonical source:",
        "data/cleaned/english/the_valley_of_fear_clean.txt",
        "",
        "Final corpus:",
        "data/final/english/the_valley_of_fear_final_corpus.csv",
        "",
        "7. 172-TURN DISCREPANCY",
        "-" * 72,
        "README.md reports 172 dialogue turns.",
        "No reproducible selection rule or intermediate dataset producing",
        "172 was found in the available project artifacts.",
        f"Current reproducible corpus: {len(rows)} turns.",
        "",
        "8. AUDIT STATUS",
        "-" * 72,
        f"PASS unique IDs:         {len(duplicate_ids) == 0}",
        f"PASS non-empty dialogue:  {len(empty) == 0}",
        f"PASS canonical titles:    {lowercase_titles == 0}",
        f"PASS schema:              {len(missing_fields) == 0}",
        "",
        "NOTE:",
        "Speaker Unknown values are retained rather than being guessed.",
        "Long records are flagged for review and are not silently changed.",
        "",
        "=" * 72,
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    print()
    print(f"AUDIT REPORT: {REPORT}")


if __name__ == "__main__":
    main()