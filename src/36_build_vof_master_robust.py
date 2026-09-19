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
    "data/final/english/the_valley_of_fear_master_v2.csv"
)

UNRESOLVED_FILE = Path(
    "data/final/english/the_valley_of_fear_master_unresolved.csv"
)


TEXT_ID = "VOF"
TITLE = "The Valley of Fear"
AUTHOR = "Arthur Conan Doyle"
PUBLICATION_YEAR = "1915"
LANGUAGE = "English"
SOURCE = "Project Gutenberg #3289"


# ---------------------------------------------------------
# Normalization used ONLY for source matching.
# Original corpus text is never changed.
# ---------------------------------------------------------

def normalize(text):
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


def compact(text):
    return re.sub(r"\s+", "", normalize(text)).lower()


# ---------------------------------------------------------
# Read inputs
# ---------------------------------------------------------

with SENTENCE_FILE.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

clean_text = CLEAN_FILE.read_text(encoding="utf-8")

normalized_clean = normalize(clean_text)
compact_clean = compact(clean_text)

print("BUILDING ROBUST VOF MASTER CORPUS")
print("=================================")
print()
print(f"Sentence/context rows: {len(rows):,}")
print(f"Clean source characters: {len(clean_text):,}")


# ---------------------------------------------------------
# Detect PART / CHAPTER headings
#
# We intentionally distinguish repeated Chapter I, etc.
# by tracking the current Part.
# ---------------------------------------------------------

heading_pattern = re.compile(
    r"(?m)^\s*("
    r"PART\s+[IVXLCDM0-9]+(?:\s*[-—:]\s*.*)?"
    r"|"
    r"CHAPTER\s+[IVXLCDM0-9]+(?:\s*[-—:]\s*.*)?"
    r")\s*$",
    re.IGNORECASE,
)

heading_matches = list(heading_pattern.finditer(clean_text))

chapter_intervals = []

current_part = None
chapter_number = None

for index, match in enumerate(heading_matches):

    raw_heading = " ".join(match.group(0).split())
    upper_heading = raw_heading.upper()

    start = match.start()

    if index + 1 < len(heading_matches):
        end = heading_matches[index + 1].start()
    else:
        end = len(clean_text)

    if upper_heading.startswith("PART "):
        current_part = raw_heading
        chapter_number = None
        continue

    if upper_heading.startswith("CHAPTER "):

        chapter_number = raw_heading

        if current_part:
            label = f"{current_part} — {chapter_number}"
        else:
            label = chapter_number

        chapter_intervals.append({
            "start": start,
            "end": end,
            "label": label,
        })


print()
print(f"Chapter intervals detected: {len(chapter_intervals):,}")


# ---------------------------------------------------------
# Convert chapter interval positions into normalized-source
# positions.
#
# Because normalization changes character count, we build a
# normalized source with mapping back to the original source.
# ---------------------------------------------------------

def normalize_with_positions(text):
    """
    Create a normalized representation while retaining
    approximate original character positions.

    Each normalized character receives the original source
    position from which it originated.
    """

    chars = []
    positions = []

    previous_was_space = False

    for index, char in enumerate(text):

        if char in "\r\n\t ":
            if previous_was_space:
                continue

            chars.append(" ")
            positions.append(index)
            previous_was_space = True
            continue

        previous_was_space = False

        replacements = {
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
            "—": "-",
            "–": "-",
        }

        char = replacements.get(char, char)

        chars.append(char)
        positions.append(index)

    normalized = "".join(chars).strip()

    return normalized, positions


normalized_source, normalized_positions = normalize_with_positions(
    clean_text
)


# ---------------------------------------------------------
# Search helpers
# ---------------------------------------------------------

def locate_fragment(fragment, start_position=0):

    fragment_normalized = normalize(fragment)

    if not fragment_normalized:
        return -1

    position = normalized_source.find(
        fragment_normalized,
        start_position,
    )

    if position != -1:
        return position

    # Compact fallback.
    compact_fragment = compact(fragment)

    if not compact_fragment:
        return -1

    compact_source = re.sub(
        r"\s+",
        "",
        normalized_source,
    ).lower()

    compact_position = compact_source.find(
        compact_fragment,
    )

    return compact_position


def get_source_position(normalized_position):

    if normalized_position < 0:
        return -1

    if normalized_position >= len(normalized_positions):
        return -1

    return normalized_positions[normalized_position]


# ---------------------------------------------------------
# Chapter lookup
# ---------------------------------------------------------

def chapter_for_position(source_position):

    if source_position < 0:
        return "Unresolved"

    for interval in chapter_intervals:

        if interval["start"] <= source_position < interval["end"]:
            return interval["label"]

    return "Outside detected chapter"


# ---------------------------------------------------------
# Find source evidence for each sentence
#
# Strategy:
# 1. Full sentence.
# 2. First 12 words.
# 3. Last 12 words.
# 4. First 8 words.
# 5. Last 8 words.
# 6. First 5 words.
# 7. Last 5 words.
# ---------------------------------------------------------

def source_evidence(sentence, previous_position):

    words = sentence.split()

    candidates = []

    if len(words) >= 12:
        candidates.append(
            ("full", sentence)
        )
        candidates.append(
            ("beginning_12", " ".join(words[:12]))
        )
        candidates.append(
            ("ending_12", " ".join(words[-12:]))
        )

    if len(words) >= 8:
        candidates.append(
            ("beginning_8", " ".join(words[:8]))
        )
        candidates.append(
            ("ending_8", " ".join(words[-8:]))
        )

    if len(words) >= 5:
        candidates.append(
            ("beginning_5", " ".join(words[:5]))
        )
        candidates.append(
            ("ending_5", " ".join(words[-5:]))
        )

    candidates.append(
        ("full", sentence)
    )

    for method, fragment in candidates:

        normalized_fragment = normalize(fragment)

        position = normalized_source.find(
            normalized_fragment,
            previous_position,
        )

        if position != -1:

            source_position = get_source_position(position)

            return method, source_position

    return "unresolved", -1


# ---------------------------------------------------------
# Map sentences sequentially
# ---------------------------------------------------------

master_rows = []
unresolved_rows = []

search_position = 0

for row in rows:

    sentence = normalize(row["current_text"])

    method, source_position = source_evidence(
        sentence,
        search_position,
    )

    if source_position == -1:

        # Try from the beginning as a diagnostic fallback.
        method, source_position = source_evidence(
            sentence,
            0,
        )

    if source_position == -1:

        chapter = "Unresolved"

        unresolved_rows.append({
            "sentence_id": row["sentence_id"],
            "turn_id": row["turn_id"],
            "speaker": row["speaker"],
            "current_text": row["current_text"],
            "reason": "no_source_fragment_found",
        })

    else:

        chapter = chapter_for_position(
            source_position
        )

        search_position = max(
            search_position,
            source_position + len(sentence),
        )

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

if len(master_rows) != len(rows):
    raise ValueError(
        "Master row count changed."
    )

input_ids = [row["sentence_id"] for row in rows]
output_ids = [row["sentence_id"] for row in master_rows]

if input_ids != output_ids:
    raise ValueError(
        "Sentence IDs/order changed."
    )


# ---------------------------------------------------------
# Write master corpus
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

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

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(master_rows)


# ---------------------------------------------------------
# Write unresolved cases separately
# ---------------------------------------------------------

with UNRESOLVED_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    unresolved_fields = [
        "sentence_id",
        "turn_id",
        "speaker",
        "current_text",
        "reason",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=unresolved_fields,
    )

    writer.writeheader()
    writer.writerows(unresolved_rows)


# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------

from collections import Counter

chapter_counts = Counter(
    row["chapter"]
    for row in master_rows
)

method_counts = Counter()

# Re-run evidence classification only for reporting.
# This does not modify the corpus.

for row in rows:

    sentence = normalize(row["current_text"])

    method, position = source_evidence(
        sentence,
        0,
    )

    method_counts[method] += 1


print()
print("ROBUST MASTER CORPUS CREATED")
print("-----------------------------")
print(f"Input rows:                 {len(rows):,}")
print(f"Master rows:                {len(master_rows):,}")
print(f"Unresolved source rows:     {len(unresolved_rows):,}")

print()
print("Chapter distribution:")

for chapter, count in chapter_counts.items():
    print(f"  {chapter}: {count:,}")

print()
print("Source-evidence methods:")
for method, count in method_counts.most_common():
    print(f"  {method}: {count:,}")

print()
print(f"Master output:")
print(f"  {OUTPUT_FILE}")

print()
print(f"Unresolved output:")
print(f"  {UNRESOLVED_FILE}")

print()
print("IMPORTANT:")
print("- sentence_v2.csv was NOT modified.")
print("- No sentence text was changed.")
print("- No speaker was changed.")
print("- No annotation was performed.")