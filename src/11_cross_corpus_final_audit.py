from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

CORPORA = {
    "VOF": BASE / "data/final/english/the_valley_of_fear_final_corpus.csv",
    "MWT": BASE / "data/final/english/the_man_who_was_thursday_final_corpus.csv",
    "OWT": BASE / "data/final/english/the_old_wives_tale_final_corpus.csv",
}

OUT_DIR = BASE / "data/final/english"
REPORT = OUT_DIR / "english_three_novel_final_audit.txt"


def audit(name, path):
    df = pd.read_csv(path)

    required = ["text_id", "turn_id", "speaker"]
    missing = [c for c in required if c not in df.columns]

    dialogue_col = None
    for col in ["dialogue_text", "quoted_text"]:
        if col in df.columns:
            dialogue_col = col
            break

    if dialogue_col is None:
        missing.append("dialogue_text/quoted_text")
        empty_dialogue = -1
    else:
        empty_dialogue = (
            df[dialogue_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

    known = (
        ~df["speaker"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["", "unknown", "nan"])
    ).sum()

    unknown = len(df) - known
    duplicate_ids = df["turn_id"].duplicated().sum()

    return {
        "name": name,
        "file": str(path.relative_to(BASE)),
        "rows": len(df),
        "known": int(known),
        "unknown": int(unknown),
        "unknown_pct": round(unknown / len(df) * 100, 2),
        "duplicate_ids": int(duplicate_ids),
        "empty_dialogue": int(empty_dialogue),
        "dialogue_column": dialogue_col or "NONE",
        "missing_fields": missing,
    }


results = []

for name, path in CORPORA.items():
    if not path.exists():
        print(f"MISSING: {path}")
        continue

    results.append(audit(name, path))

total_turns = sum(x["rows"] for x in results)
total_known = sum(x["known"] for x in results)
total_unknown = sum(x["unknown"] for x in results)

all_files_present = len(results) == 3

expected = {"VOF": 1267, "MWT": 870, "OWT": 679}
actual = {r["name"]: r["rows"] for r in results}
counts_correct = actual == expected

structural_pass = all(
    r["duplicate_ids"] == 0
    and r["empty_dialogue"] == 0
    and not r["missing_fields"]
    for r in results
)

lines = [
    "=" * 70,
    "THREE-NOVEL ENGLISH CORPUS — FINAL CROSS-CORPUS AUDIT",
    "=" * 70,
    "",
]

for r in results:
    lines.extend([
        r["name"],
        "-" * 70,
        f"File:                  {r['file']}",
        f"Turns:                 {r['rows']}",
        f"Known speakers:        {r['known']}",
        f"Unknown speakers:      {r['unknown']}",
        f"Unknown percentage:    {r['unknown_pct']}%",
        f"Dialogue column:       {r['dialogue_column']}",
        f"Duplicate turn IDs:    {r['duplicate_ids']}",
        f"Empty dialogue rows:   {r['empty_dialogue']}",
        f"Missing required:      {', '.join(r['missing_fields']) if r['missing_fields'] else 'None'}",
        "",
    ])

lines.extend([
    "=" * 70,
    "COMBINED ENGLISH CORPUS",
    "=" * 70,
    f"Novels audited:         {len(results)}",
    f"Total dialogue turns:   {total_turns}",
    f"Known speakers:         {total_known}",
    f"Unknown speakers:       {total_unknown}",
    f"Unknown percentage:     {round(total_unknown / total_turns * 100, 2)}%",
    "",
    "EXPECTED CURRENT COUNTS",
    "The Valley of Fear:     1267",
    "The Man Who Was Thursday: 870",
    "The Old Wives' Tale:    679",
    f"Expected total:         {sum(expected.values())}",
    "",
    "STATUS",
    f"All three final files present: {all_files_present}",
    f"Turn counts match frozen versions: {counts_correct}",
    f"Structural checks pass: {structural_pass}",
    "",
    "INTERPRETATION",
    "The three English novels are represented by their current",
    "reproducible final corpus versions.",
    "VOF uses dialogue_text; MWT and OWT use quoted_text.",
    "Unknown speaker values are retained rather than guessed.",
    "Novel-specific audit findings remain documented separately.",
    "",
])

REPORT.write_text("\n".join(lines), encoding="utf-8")

print("\n".join(lines))
print(f"REPORT: {REPORT.relative_to(BASE)}")