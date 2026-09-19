import csv
import re
from pathlib import Path


SENTENCE_FILE = Path(
    "data/extracted/english/the_valley_of_fear_sentence_v2.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)

DIAGNOSIS_FILE = Path(
    "data/extracted/english/the_valley_of_fear_unmatched_diagnosis.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/the_valley_of_fear_source_fragment_diagnosis.csv"
)


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


with DIAGNOSIS_FILE.open("r", encoding="utf-8", newline="") as f:
    diagnosis_reader = csv.DictReader(f)
    diagnosis_rows = list(diagnosis_reader)


clean_text = CLEAN_FILE.read_text(encoding="utf-8")

normalized_clean = normalize(clean_text)
compact_clean = compact(clean_text)


results = []

for row in diagnosis_rows:

    # We are interested specifically in the cases that remained
    # unmatched even after aggressive normalization.
    if row["diagnosis"] != "not_found_even_after_aggressive_normalization":
        continue

    sentence = normalize(row["current_text"])
    compact_sentence = compact(sentence)

    # -----------------------------------------------------
    # Build beginning and ending fragments.
    # -----------------------------------------------------

    words = sentence.split()

    if len(words) >= 8:
        beginning = " ".join(words[:8])
        ending = " ".join(words[-8:])
    else:
        beginning = sentence
        ending = sentence

    beginning_compact = compact(beginning)
    ending_compact = compact(ending)

    beginning_found = (
        compact_clean.find(beginning_compact) != -1
    )

    ending_found = (
        compact_clean.find(ending_compact) != -1
    )

    # -----------------------------------------------------
    # Shorter fragments.
    # -----------------------------------------------------

    short_beginning = " ".join(words[:4])
    short_ending = " ".join(words[-4:])

    short_beginning_found = (
        compact_clean.find(compact(short_beginning)) != -1
    )

    short_ending_found = (
        compact_clean.find(compact(short_ending)) != -1
    )

    if beginning_found and ending_found:
        classification = "both_fragments_found"

    elif beginning_found:
        classification = "beginning_only"

    elif ending_found:
        classification = "ending_only"

    elif short_beginning_found or short_ending_found:
        classification = "short_fragment_only"

    else:
        classification = "no_fragment_found"

    results.append({
        "text_id": row["text_id"],
        "turn_id": row["turn_id"],
        "sentence_id": row["sentence_id"],
        "speaker": row["speaker"],
        "current_text": row["current_text"],
        "classification": classification,
        "beginning_fragment": beginning,
        "beginning_found": beginning_found,
        "ending_fragment": ending,
        "ending_found": ending_found,
        "short_beginning_found": short_beginning_found,
        "short_ending_found": short_ending_found,
    })


fieldnames = [
    "text_id",
    "turn_id",
    "sentence_id",
    "speaker",
    "current_text",
    "classification",
    "beginning_fragment",
    "beginning_found",
    "ending_fragment",
    "ending_found",
    "short_beginning_found",
    "short_ending_found",
]


with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

from collections import Counter

counts = Counter(
    row["classification"]
    for row in results
)

print("VOF SOURCE-FRAGMENT DIAGNOSIS")
print("=============================")
print()
print(f"Still-unmatched cases analyzed: {len(results):,}")
print()

for classification, count in counts.most_common():
    print(f"{classification}: {count:,}")

print()
print("FIRST 25 CASES")
print("---------------")

for row in results[:25]:

    text = row["current_text"]

    if len(text) > 180:
        text = text[:180] + "..."

    print()
    print(
        f"{row['sentence_id']} | "
        f"{row['classification']}"
    )
    print(f"  {text}")

print()
print(f"Output: {OUTPUT_FILE}")

print()
print("IMPORTANT:")
print("- No corpus file was modified.")
print("- sentence_v2.csv was NOT modified.")
print("- This is diagnosis only.")