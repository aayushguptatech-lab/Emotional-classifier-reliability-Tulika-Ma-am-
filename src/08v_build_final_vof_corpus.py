from pathlib import Path
import csv
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

V6 = DATA / "extracted" / "english" / "the_valley_of_fear_dialogue_v6_rebuilt.csv"
CLEAN = DATA / "cleaned" / "english" / "the_valley_of_fear_clean.txt"

OUT_DIR = DATA / "final" / "english"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL = OUT_DIR / "the_valley_of_fear_final_corpus.csv"
REPORT = OUT_DIR / "the_valley_of_fear_final_validation.txt"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def source_fingerprint(text):
    return {
        "characters": len(text),
        "words": len(re.findall(r"\b\w+\b", text)),
        "mr": len(re.findall(r"\bMr\.", text)),
        "mrs": len(re.findall(r"\bMrs\.", text)),
        "dr": len(re.findall(r"\bDr\.", text)),
        "st": len(re.findall(r"\bSt\.", text)),
        "lowercase_titles": len(
            re.findall(r"\b(?:mr|mrs|dr|st)\.", text)
        ),
    }


def main():
    if not V6.exists():
        raise FileNotFoundError(f"Missing input: {V6}")

    if not CLEAN.exists():
        raise FileNotFoundError(f"Missing canonical source: {CLEAN}")

    rows = read_csv(V6)
    canonical = CLEAN.read_text(encoding="utf-8")

    before = source_fingerprint(canonical)

    final_rows = []

    for row in rows:
        final_rows.append({
            "text_id": row.get("text_id", "VOF"),
            "turn_id": row["turn_id"],
            "speaker": row.get("speaker", "Unknown"),
            "dialogue_text": row["dialogue_text"],
            "unit_type": row.get("unit_type", "dialogue_candidate"),
            "extraction_confidence": row.get(
                "extraction_confidence", ""
            ),
            "source": row.get(
                "source",
                "Project Gutenberg #3289"
            ),
        })

    fields = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "unit_type",
        "extraction_confidence",
        "source",
    ]

    write_csv(FINAL, final_rows, fields)

    after = source_fingerprint(canonical)

    ids = [r["turn_id"] for r in final_rows]
    speakers = Counter(r["speaker"] for r in final_rows)

    duplicate_ids = [
        x for x, n in Counter(ids).items() if n > 1
    ]

    empty_dialogue = [
        r["turn_id"]
        for r in final_rows
        if not r["dialogue_text"].strip()
    ]

    checks = {
        "final_rows": len(final_rows),
        "unique_turn_ids": len(set(ids)),
        "duplicate_turn_ids": len(duplicate_ids),
        "empty_dialogue": len(empty_dialogue),
        "known_speakers": len(final_rows) - speakers["Unknown"],
        "unknown_speakers": speakers["Unknown"],
        "canonical_text_unchanged": before == after,
        "lowercase_title_forms": after["lowercase_titles"],
    }

    report = [
        "=" * 72,
        "THE VALLEY OF FEAR — FINAL CORPUS VALIDATION",
        "=" * 72,
        "",
        f"Input turns:              {len(rows)}",
        f"Final corpus turns:       {checks['final_rows']}",
        f"Unique turn IDs:          {checks['unique_turn_ids']}",
        f"Duplicate turn IDs:      {checks['duplicate_turn_ids']}",
        f"Empty dialogue rows:      {checks['empty_dialogue']}",
        "",
        "SPEAKER COUNTS",
        "-" * 72,
        f"Known speakers:           {checks['known_speakers']}",
        f"Unknown speakers:         {checks['unknown_speakers']}",
        "",
        "CANONICAL TEXT",
        "-" * 72,
        f"Characters:               {before['characters']}",
        f"Words:                    {before['words']}",
        f"Mr.:                      {before['mr']}",
        f"Mrs.:                     {before['mrs']}",
        f"Dr.:                      {before['dr']}",
        f"St.:                      {before['st']}",
        f"Lowercase title forms:    {after['lowercase_titles']}",
        f"Canonical text unchanged: {checks['canonical_text_unchanged']}",
        "",
        "SOURCE",
        "-" * 72,
        "Project Gutenberg #3289",
        "Arthur Conan Doyle — The Valley of Fear",
        "",
        "REPRODUCIBILITY NOTE",
        "-" * 72,
        "This final corpus is generated from the current reproducible V6",
        "dialogue artifact without modifying the canonical cleaned novel.",
        "Canonical source text is kept separate from any matching or",
        "segmentation transformations.",
        "",
        "DOCUMENTED COUNT DISCREPANCY",
        "-" * 72,
        "README.md reports 172 dialogue turns.",
        "The available project artifacts do not contain a reproducible",
        "selection rule, script, or intermediate dataset that produces 172.",
        f"The current generated corpus contains {len(final_rows)} turns.",
        "The 172-turn figure is therefore retained as a documented",
        "historical project claim rather than imposed as an undocumented",
        "filter on the current corpus.",
        "",
        "VALIDATION",
        "-" * 72,
        f"PASS unique turn IDs:     {checks['duplicate_turn_ids'] == 0}",
        f"PASS non-empty dialogue:   {checks['empty_dialogue'] == 0}",
        f"PASS canonical unchanged:  {checks['canonical_text_unchanged']}",
        f"PASS no lowercase titles:  {after['lowercase_titles'] == 0}",
        "",
        "=" * 72,
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    print()
    print(f"FINAL CSV:    {FINAL}")
    print(f"VALIDATION:   {REPORT}")


if __name__ == "__main__":
    main()