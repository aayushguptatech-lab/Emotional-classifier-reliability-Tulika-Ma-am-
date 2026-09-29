from pathlib import Path
import re

CLEAN_FILE = Path(
    "data/cleaned/english/the_man_who_was_thursday_clean.txt"
)

print("Analyzing speaker-attribution patterns in The Man Who Was Thursday...")

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )

text = CLEAN_FILE.read_text(encoding="utf-8")
lines = text.splitlines()

# Common speech-attribution verbs found during inspection.
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
    "inquired",
    "demanded",
    "protested",
    "returned",
    "urged",
    "suggested",
    "interrupted",
    "explained",
]

verb_pattern = "|".join(speech_verbs)

# ---------------------------------------------------------
# Pattern 1:
# “...,” said NAME
# ---------------------------------------------------------

pattern_after = re.compile(
    rf"[“”].*?[”]\s*,?\s*"
    rf"(?:{verb_pattern})\s+"
    rf"([^.!?\n]+)",
    re.IGNORECASE,
)

# ---------------------------------------------------------
# Pattern 2:
# said NAME, “...”
# ---------------------------------------------------------

pattern_before = re.compile(
    rf"(?:{verb_pattern})\s+"
    rf"([^,:\n]+)"
    rf",\s*[“]",
    re.IGNORECASE,
)

# ---------------------------------------------------------
# Pattern 3:
# “...” he/she said
# ---------------------------------------------------------

pattern_pronoun_after = re.compile(
    rf"[“”].*?[”]\s*,?\s*"
    rf"(?:{verb_pattern})\s+"
    rf"(he|she|they|i|we|you)\b",
    re.IGNORECASE,
)

print()
print("SPEAKER-ATTRIBUTION PATTERN ANALYSIS")
print("-------------------------------------")

# ---------------------------------------------------------
# Count pattern matches
# ---------------------------------------------------------

matches_after = pattern_after.findall(text)
matches_before = pattern_before.findall(text)
matches_pronoun_after = pattern_pronoun_after.findall(text)

print()
print("Pattern counts:")
print("----------------")
print(f'“...,” VERB NAME-like pattern: {len(matches_after):,}')
print(f'VERB NAME, “...” pattern: {len(matches_before):,}')
print(f'“...” VERB PRONOUN pattern: {len(matches_pronoun_after):,}')

# ---------------------------------------------------------
# Print concrete examples from lines
# ---------------------------------------------------------

print()
print('EXAMPLES: “...,” SPEECH-VERB ...')
print("--------------------------------")

count = 0

for i, line in enumerate(lines, start=1):
    if not any(
        re.search(
            rf"\b{verb}\b",
            line,
            re.IGNORECASE
        )
        for verb in speech_verbs
    ):
        continue

    if "”" in line and re.search(
        rf"\b({verb_pattern})\b",
        line,
        re.IGNORECASE
    ):
        print(f"{i:05d}: {line}")
        count += 1

        if count >= 40:
            break

print()
print('EXAMPLES: SPEECH-VERB ... “...”')
print("--------------------------------")

count = 0

for i, line in enumerate(lines, start=1):
    if re.search(
        rf"\b({verb_pattern})\b",
        line,
        re.IGNORECASE
    ) and "“" in line:
        print(f"{i:05d}: {line}")
        count += 1

        if count >= 40:
            break

print()
print("SPEAKER-ATTRIBUTION ANALYSIS COMPLETE.")