from pathlib import Path
import re

CLEAN_FILE = Path(
    "data/cleaned/english/the_man_who_was_thursday_clean.txt"
)

print("Inspecting dialogue patterns in The Man Who Was Thursday...")

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )

text = CLEAN_FILE.read_text(encoding="utf-8")

lines = text.splitlines()

print()
print("BASIC TEXT STATISTICS")
print("----------------------")
print(f"Characters: {len(text):,}")
print(f"Lines: {len(lines):,}")

# ---------------------------------------------------------
# 1. Quotation mark counts
# ---------------------------------------------------------

straight_double = text.count('"')
curly_open = text.count("“")
curly_close = text.count("”")
curly_single_open = text.count("‘")
curly_single_close = text.count("’")

print()
print("QUOTATION MARK COUNTS")
print("---------------------")
print(f'Straight double quote (\"): {straight_double:,}')
print(f"Curly opening double quote (“): {curly_open:,}")
print(f"Curly closing double quote (”): {curly_close:,}")
print(f"Curly opening single quote (‘): {curly_single_open:,}")
print(f"Curly closing single quote (’): {curly_single_close:,}")

# ---------------------------------------------------------
# 2. Lines containing dialogue quotation marks
# ---------------------------------------------------------

dialogue_lines = []

for i, line in enumerate(lines, start=1):
    if '"' in line or "“" in line or "”" in line:
        dialogue_lines.append((i, line))

print()
print("LINES CONTAINING DOUBLE QUOTATION MARKS")
print("----------------------------------------")
print(f"Total lines: {len(dialogue_lines):,}")

print()
print("First 30 examples:")
print("------------------")

for line_number, line in dialogue_lines[:30]:
    print(f"{line_number:05d}: {line}")

# ---------------------------------------------------------
# 3. Lines containing common speech attribution verbs
# ---------------------------------------------------------

speech_verbs = [
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "whispered",
    "shouted",
    "murmured",
    "remarked",
    "observed",
    "continued",
    "declared",
    "added",
    "began",
    "called",
]

speech_verb_pattern = re.compile(
    r"\b(" + "|".join(speech_verbs) + r")\b",
    re.IGNORECASE,
)

attribution_lines = []

for i, line in enumerate(lines, start=1):
    if speech_verb_pattern.search(line):
        attribution_lines.append((i, line))

print()
print("LINES WITH COMMON SPEECH-ATTRIBUTION VERBS")
print("-------------------------------------------")
print(f"Total lines: {len(attribution_lines):,}")

print()
print("First 40 examples:")
print("------------------")

for line_number, line in attribution_lines[:40]:
    print(f"{line_number:05d}: {line}")

# ---------------------------------------------------------
# 4. Examples where quotation and speech attribution
#    occur on the same line
# ---------------------------------------------------------

combined_examples = []

for i, line in enumerate(lines, start=1):
    has_quote = '"' in line or "“" in line or "”" in line
    has_verb = speech_verb_pattern.search(line)

    if has_quote and has_verb:
        combined_examples.append((i, line))

print()
print("QUOTE + SPEECH-ATTRIBUTION SAME-LINE EXAMPLES")
print("----------------------------------------------")
print(f"Total examples: {len(combined_examples):,}")

print()
print("First 40 examples:")
print("------------------")

for line_number, line in combined_examples[:40]:
    print(f"{line_number:05d}: {line}")

# ---------------------------------------------------------
# 5. Paragraphs containing dialogue
# ---------------------------------------------------------

paragraphs = re.split(r"\n\s*\n", text)

dialogue_paragraphs = []

for i, paragraph in enumerate(paragraphs, start=1):
    has_quote = '"' in paragraph or "“" in paragraph or "”" in paragraph

    if has_quote:
        dialogue_paragraphs.append((i, paragraph))

print()
print("PARAGRAPHS CONTAINING DOUBLE QUOTATION MARKS")
print("---------------------------------------------")
print(f"Total paragraphs: {len(dialogue_paragraphs):,}")

print()
print("First 15 paragraph examples:")
print("----------------------------")

for paragraph_number, paragraph in dialogue_paragraphs[:15]:
    preview = " ".join(paragraph.split())

    if len(preview) > 500:
        preview = preview[:500] + "..."

    print()
    print(f"Paragraph {paragraph_number}:")
    print(preview)

print()
print("Dialogue-pattern inspection complete.")