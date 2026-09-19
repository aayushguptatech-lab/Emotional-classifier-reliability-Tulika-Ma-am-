import csv
import re
from pathlib import Path

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

V5_FILE = Path(
    "data/extracted/english/the_valley_of_fear_dialogue_v5.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_internal_boundary_audit.csv"
)


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def normalize(text):
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    return re.sub(r"\s+", " ", text).strip()


def find_dialogue_context(
    clean_text,
    dialogue,
    window=700
):
    text = normalize(clean_text)
    target = normalize(dialogue)

    if not target:
        return ""

    pos = text.find(target)

    if pos == -1:
        words = target.split()

        for n in [50, 40, 30, 20, 15]:
            if len(words) >= n:
                partial = " ".join(words[:n])
                pos = text.find(partial)

                if pos != -1:
                    break

    if pos == -1:
        return ""

    start = max(0, pos - window)
    end = min(
        len(text),
        pos + len(target) + window
    )

    return text[start:end]


def find_internal_attributions(text):
    """
    Look for attribution phrases occurring inside a
    reconstructed dialogue unit.

    This is diagnostic only.
    """

    patterns = [
        r"\bsaid\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\basked\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\breplied\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\banswered\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\bcried\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\bremarked\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\bcontinued\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\bexclaimed\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
        r"\bwhispered\s+(?:I|he|she|they|we|you|[A-Z][A-Za-z.'’\-]*(?:\s+[A-Z][A-Za-z.'’\-]*){0,3})",
    ]

    matches = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            matches.append(
                match.group(0)
            )

    return matches


print("Reading V5...")

rows = read_csv(V5_FILE)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

audit = []

for row in rows:

    dialogue = row.get(
        "dialogue_text",
        ""
    )

    context = find_dialogue_context(
        clean_text,
        dialogue
    )

    attributions = find_internal_attributions(
        dialogue
    )

    if len(attributions) > 0:

        audit.append(
            {
                "text_id": row.get(
                    "text_id",
                    ""
                ),
                "turn_id": row.get(
                    "turn_id",
                    ""
                ),
                "speaker": row.get(
                    "speaker",
                    ""
                ),
                "dialogue_text": dialogue,
                "internal_attributions": " | ".join(
                    attributions
                ),
                "source_context": context,
            }
        )


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fields = [
        "text_id",
        "turn_id",
        "speaker",
        "dialogue_text",
        "internal_attributions",
        "source_context",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields
    )

    writer.writeheader()
    writer.writerows(audit)


print()
print("INTERNAL SPEAKER-BOUNDARY AUDIT COMPLETE")
print("------------------------------------------")
print(
    f"Total V5 turns: {len(rows):,}"
)
print(
    f"Potential internal attribution cases: "
    f"{len(audit):,}"
)
print(
    f"Output: {OUTPUT_FILE}"
)

print()
print("FIRST 30 CASES")
print("--------------")

for row in audit[:30]:

    print()
    print("=" * 80)
    print(row["turn_id"])
    print(
        "ASSIGNED SPEAKER:",
        row["speaker"]
    )

    print()
    print("DIALOGUE:")
    print(row["dialogue_text"][:700])

    print()
    print("INTERNAL ATTRIBUTION:")
    print(row["internal_attributions"])

    print()
    print("SOURCE CONTEXT:")
    print(row["source_context"][:1200])

print()
print("No source files were modified.")