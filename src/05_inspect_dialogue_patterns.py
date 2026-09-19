from pathlib import Path
import re


# ---------------------------------------------------------
# 1. File location
# ---------------------------------------------------------

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)


# ---------------------------------------------------------
# 2. Read the cleaned novel
# ---------------------------------------------------------

text = CLEAN_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------
# 3. Basic information
# ---------------------------------------------------------

print("=" * 70)
print("DIALOGUE PATTERN INSPECTION")
print("=" * 70)

print(f"File: {CLEAN_FILE}")
print(f"Characters: {len(text):,}")

print()


# ---------------------------------------------------------
# 4. Count quotation marks
# ---------------------------------------------------------

double_quotes = text.count('"')
left_double_quotes = text.count("“")
right_double_quotes = text.count("”")

print("Quotation mark counts")
print("-" * 70)

print(f'ASCII double quote ("): {double_quotes:,}')
print(f"Left curly quote (“):    {left_double_quotes:,}")
print(f"Right curly quote (”):   {right_double_quotes:,}")

print()


# ---------------------------------------------------------
# 5. Extract text inside curly quotation marks
# ---------------------------------------------------------

curly_dialogue = re.findall(
    r'“(.*?)”',
    text,
    flags=re.DOTALL
)

print("Curly-quoted spans")
print("-" * 70)

print(f"Number of spans found: {len(curly_dialogue):,}")

print()


# ---------------------------------------------------------
# 6. Show sample quotation spans
# ---------------------------------------------------------

print("=" * 70)
print("SAMPLE QUOTATION SPANS")
print("=" * 70)

sample_count = min(20, len(curly_dialogue))

for i in range(sample_count):

    dialogue = curly_dialogue[i].strip()

    print()
    print(f"[Sample {i + 1}]")
    print("-" * 70)
    print(dialogue)


# ---------------------------------------------------------
# 7. Look for common speaker-attribution patterns
# ---------------------------------------------------------

speaker_verbs = [
    "said",
    "asked",
    "replied",
    "answered",
    "remarked",
    "continued",
    "cried",
    "exclaimed",
    "shouted",
    "whispered",
    "observed",
    "returned",
    "added",
    "continued",
    "murmured",
    "declared",
    "demanded",
    "suggested",
    "explained",
    "repeated",
    "called",
    "protested",
]


print()
print("=" * 70)
print("QUOTATION + SPEAKER-VERB PATTERNS")
print("=" * 70)


for verb in speaker_verbs:

    pattern = re.compile(
        rf'”\s*(?:said|asked|replied|answered|remarked|continued|'
        rf'cried|exclaimed|shouted|whispered|observed|returned|'
        rf'added|murmured|declared|demanded|suggested|explained|'
        rf'repeated|called|protested)\b',
        flags=re.IGNORECASE
    )

    break


matches = pattern.findall(text)

print(
    "Quotation marks followed by a common speaker-attribution verb:",
    len(matches)
)


# ---------------------------------------------------------
# 8. Show context around quotation endings
# ---------------------------------------------------------

print()
print("=" * 70)
print("SAMPLE SPEAKER-ATTRIBUTION CONTEXT")
print("=" * 70)

pattern = re.compile(
    r'”\s*(.{0,100})',
    flags=re.DOTALL
)

matches = list(pattern.finditer(text))

shown = 0

for match in matches:

    following_text = match.group(1).strip()

    if not following_text:
        continue

    lower_text = following_text.lower()

    if any(
        re.search(
            rf'\b{re.escape(verb)}\b',
            lower_text
        )
        for verb in speaker_verbs
    ):

        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)

        context = text[start:end]

        print()
        print("-" * 70)
        print(context.replace("\n", " "))

        shown += 1

        if shown >= 20:
            break


# ---------------------------------------------------------
# 9. Multi-line quotation inspection
# ---------------------------------------------------------

print()
print("=" * 70)
print("MULTI-LINE QUOTATION INSPECTION")
print("=" * 70)

multiline_count = 0

for dialogue in curly_dialogue:

    if "\n" in dialogue:

        multiline_count += 1

        if multiline_count <= 10:

            print()
            print(f"[Multi-line quotation {multiline_count}]")
            print("-" * 70)
            print(dialogue)


print()
print(f"Total multi-line quotation spans: {multiline_count:,}")


# ---------------------------------------------------------
# 10. Final message
# ---------------------------------------------------------

print()
print("=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)