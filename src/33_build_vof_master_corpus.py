import csv
import re
from pathlib import Path


SENTENCE_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v2.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

OUTPUT_FILE = Path(
    "data/final/english/the_valley_of_fear_master.csv"
)


# ---------------------------------------------------------
# Fixed metadata
# ---------------------------------------------------------

TEXT_ID = "VOF"
TITLE = "The Valley of Fear"
AUTHOR = "Arthur Conan Doyle"
PUBLICATION_YEAR = "1915"
LANGUAGE = "English"
SOURCE = "Project Gutenberg #3289"


# ---------------------------------------------------------
# Read validated sentence/context layer
# ---------------------------------------------------------

with SENTENCE_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    sentence_rows = list(reader)

print("BUILDING VALLEY OF FEAR MASTER CORPUS")
print("======================================")
print()
print(f"Sentence/context rows read: {len(sentence_rows):,}")


# ---------------------------------------------------------
# Read clean novel
# ---------------------------------------------------------

clean_text = CLEAN_FILE.read_text(encoding="utf-8")

print(f"Clean novel characters:     {len(clean_text):,}")


# ---------------------------------------------------------
# Detect chapter headings
#
# We only use headings actually present in the clean text.
# No chapter numbering is invented.
# ---------------------------------------------------------

chapter_pattern = re.compile(
    r"(?m)^\s*(CHAPTER\s+[IVXLCDM0-9]+(?:\s*[-—:]\s*.*)?|"
    r"PART\s+[IVXLCDM0-9]+(?:\s*[-—:]\s*.*)?)\s*$",
    re.IGNORECASE,
)

chapter_matches = list(chapter_pattern.finditer(clean_text))

print()
print(f"Chapter/part headings detected: {len(chapter_matches):,}")


# ---------------------------------------------------------
# Print detected headings for verification
# ---------------------------------------------------------

print()
print("Detected headings:")
print("------------------")

for match in chapter_matches:
    heading = " ".join(match.group(0).split())
    print(f"{match.start():>8} | {heading}")


# ---------------------------------------------------------
# Build chapter intervals
# ---------------------------------------------------------

chapter_intervals = []

for index, match in enumerate(chapter_matches):

    heading = " ".join(match.group(0).split())

    start = match.start()

    if index + 1 < len(chapter_matches):
        end = chapter_matches[index + 1].start()
    else:
        end = len(clean_text)

    chapter_intervals.append({
        "heading": heading,
        "start": start,
        "end": end,
    })


# ---------------------------------------------------------
# Locate each sentence in clean novel
#
# We search using the sentence text after normalizing
# whitespace. Exact physical line wrapping in the clean
# novel is therefore not treated as meaningful.
# ---------------------------------------------------------

def normalize_for_search(text):
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


normalized_clean = normalize_for_search(clean_text)


def find_sentence_position(sentence):
    """
    Find the sentence in the normalized clean novel.

    We use the exact normalized sentence text.
    If it occurs multiple times, occurrence disambiguation
    is handled using a forward search position.
    """
    return normalized_clean.find(sentence)


# ---------------------------------------------------------
# Sequentially assign chapters
#
# Because repeated sentences can occur, maintain a forward
# search position through the source.
# ---------------------------------------------------------

search_position = 0

master_rows = []
unmatched = []

for row in sentence_rows:

    sentence = normalize_for_search(row["current_text"])

    if not sentence:
        unmatched.append({
            "sentence_id": row["sentence_id"],
            "reason": "empty_sentence",
        })
        continue

    position = normalized_clean.find(sentence, search_position)

    if position == -1:
        # Try the entire clean text as a fallback.
        position = normalized_clean.find(sentence)

    if position == -1:
        unmatched.append({
            "sentence_id": row["sentence_id"],
            "reason": "sentence_not_found_in_clean_text",
        })
        chapter = "Unknown"
    else:
        search_position = position + len(sentence)

        chapter = "Unknown"

        for interval in chapter_intervals:
            if interval["start"] <= position < interval["end"]:
                chapter = interval["heading"]
                break

    master_rows.append({
        "language": LANGUAGE,
        "text_id": TEXT_ID,
        "title": TITLE,
        "author": AUTHOR,
        "publication_year": PUBLICATION_YEAR,
        "chapter": chapter,
        "turn_id": row["turn_id"],
        "sentence_id": row["sentence_id"],
        "speaker": row["speaker"],
        "current_text": row["current_text"],
        "previous_text": row["previous_text"],
        "next_text": row["next_text"],
        "unit_type": row["unit_type"],
        "extraction_confidence": row["extraction_confidence"],
        "source": SOURCE,
    })


# ---------------------------------------------------------
# Safety checks
# ---------------------------------------------------------

if len(master_rows) != len(sentence_rows):
    raise ValueError(
        "Master row count does not match sentence/context row count."
    )

input_ids = [row["sentence_id"] for row in sentence_rows]
output_ids = [row["sentence_id"] for row in master_rows]

if input_ids != output_ids:
    raise ValueError(
        "Sentence IDs/order changed during master-corpus construction."
    )


# ---------------------------------------------------------
# Write master corpus
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "language",
    "text_id",
    "title",
    "author",
    "publication_year",
    "chapter",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "previous_text",
    "next_text",
    "unit_type",
    "extraction_confidence",
    "source",
]

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(master_rows)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

chapter_counts = {}

for row in master_rows:
    chapter = row["chapter"]
    chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1


print()
print("MASTER CORPUS CREATED")
print("---------------------")
print(f"Input rows:              {len(sentence_rows):,}")
print(f"Master rows:             {len(master_rows):,}")
print(f"Unmatched sentences:     {len(unmatched):,}")
print(f"Rows assigned a chapter: {sum(v for k, v in chapter_counts.items() if k != 'Unknown'):,}")
print(f"Rows with Unknown:       {chapter_counts.get('Unknown', 0):,}")

print()
print("Chapter distribution:")

for chapter, count in chapter_counts.items():
    print(f"  {chapter}: {count:,}")

print()
print(f"Output: {OUTPUT_FILE}")

if unmatched:
    print()
    print("UNMATCHED SENTENCES:")
    for item in unmatched[:20]:
        print(
            f"  {item['sentence_id']} | "
            f"{item['reason']}"
        )

    if len(unmatched) > 20:
        print(
            f"  ... plus {len(unmatched) - 20} additional unmatched."
        )

print()
print("IMPORTANT:")
print("- sentence_v2.csv was NOT modified.")
print("- No sentence text was changed.")
print("- No speaker was changed.")
print("- No annotation was performed.")