from pathlib import Path
import re
import csv

CLEAN_FILE = Path(
    "data/cleaned/english/the_man_who_was_thursday_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

print("Extracting dialogue candidates from The Man Who Was Thursday...")

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )

text = CLEAN_FILE.read_text(encoding="utf-8")

# ---------------------------------------------------------
# We use curly double quotation marks because the actual
# MWT source uses them consistently for dialogue.
#
# IMPORTANT:
# This stage only identifies quoted spans.
# It does NOT claim that every span is dialogue.
# Speaker attribution comes later.
# ---------------------------------------------------------

pattern = re.compile(
    r"“(.*?)”",
    re.DOTALL
)

matches = list(pattern.finditer(text))

print()
print("QUOTED-SPAN EXTRACTION")
print("----------------------")
print(f"Quoted spans found: {len(matches):,}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

rows = []

for index, match in enumerate(matches, start=1):
    quoted_text = match.group(1).strip()

    if not quoted_text:
        continue

    start_char = match.start()
    end_char = match.end()

    # Determine source line numbers.
    start_line = text.count(
        "\n",
        0,
        start_char
    ) + 1

    end_line = text.count(
        "\n",
        0,
        end_char
    ) + 1

    # Capture a small amount of surrounding context.
    context_start = max(0, start_char - 250)
    context_end = min(
        len(text),
        end_char + 250
    )

    context = text[
        context_start:context_end
    ].replace("\n", " ")

    rows.append(
        {
            "candidate_id": (
                f"MWT_C{index:05d}"
            ),
            "start_char": start_char,
            "end_char": end_char,
            "start_line": start_line,
            "end_line": end_line,
            "quoted_text": quoted_text,
            "surrounding_context": context,
            "candidate_type": "quoted_span",
            "speaker": "Unknown",
            "speaker_confidence": "review",
        }
    )

fieldnames = [
    "candidate_id",
    "start_char",
    "end_char",
    "start_line",
    "end_line",
    "quoted_text",
    "surrounding_context",
    "candidate_type",
    "speaker",
    "speaker_confidence",
]

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)

print()
print("Extraction successful.")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Rows written: {len(rows):,}")

print()
print("First 20 extracted candidates:")
print("-------------------------------")

for row in rows[:20]:
    preview = row["quoted_text"].replace(
        "\n",
        " "
    )

    if len(preview) > 200:
        preview = preview[:200] + "..."

    print(
        f'{row["candidate_id"]} | '
        f'lines {row["start_line"]}-{row["end_line"]} | '
        f'{preview}'
    )

print()
print("Dialogue-candidate extraction complete.")