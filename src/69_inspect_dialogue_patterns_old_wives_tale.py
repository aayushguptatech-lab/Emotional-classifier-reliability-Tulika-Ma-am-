from pathlib import Path
import re

FILE = Path(
    "data/cleaned/english/the_old_wives_tale_clean.txt"
)

print("Inspecting dialogue patterns in The Old Wives' Tale")
print("===================================================")
print()

if not FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {FILE}"
    )

text = FILE.read_text(
    encoding="utf-8"
)

print("BASIC FILE INFORMATION")
print("-----------------------")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")
print()

# --------------------------------------------------
# QUOTATION MARK COUNTS
# --------------------------------------------------

print("QUOTATION MARK COUNTS")
print("----------------------")

quote_patterns = {
    'Straight double quote (")': '"',
    "Left curly double quote (“)": "“",
    "Right curly double quote (”)": "”",
    "Straight single quote (')": "'",
    "Left curly single quote (‘)": "‘",
    "Right curly single quote (’)": "’",
}

for label, char in quote_patterns.items():
    print(
        f"{label}: {text.count(char):,}"
    )

print()

# --------------------------------------------------
# DIALOGUE-LIKE QUOTED SPANS
# --------------------------------------------------

print("DOUBLE-QUOTED SPAN ANALYSIS")
print("---------------------------")

curly_open = text.count("“")
curly_close = text.count("”")

print(
    f"Curly opening quotes: {curly_open:,}"
)
print(
    f"Curly closing quotes: {curly_close:,}"
)

if curly_open == curly_close:
    print("Curly quote balance: BALANCED")
else:
    print("Curly quote balance: REVIEW NEEDED")

print()

straight_matches = re.findall(
    r'"([^"\n]{1,500})"',
    text
)

curly_matches = re.findall(
    r'“([^”\n]{1,500})”',
    text
)

print(
    f"Straight-double-quoted candidate spans: "
    f"{len(straight_matches):,}"
)

print(
    f"Curly-double-quoted candidate spans: "
    f"{len(curly_matches):,}"
)

print()

# --------------------------------------------------
# SPEECH VERB PATTERNS
# --------------------------------------------------

print("COMMON SPEECH-VERB PATTERNS")
print("---------------------------")

speech_verbs = [
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "shouted",
    "whispered",
    "murmured",
    "remarked",
    "observed",
    "continued",
    "added",
    "declared",
    "suggested",
    "began",
    "interrupted",
    "called",
    "demanded",
    "urged",
    "begged",
    "protested",
]

lower_text = text.lower()

for verb in speech_verbs:
    count = len(
        re.findall(
            rf"\b{re.escape(verb)}\b",
            lower_text
        )
    )

    print(
        f"{verb:12s}: {count:,}"
    )

print()

# --------------------------------------------------
# DIALOGUE ATTRIBUTION PATTERNS
# --------------------------------------------------

print("DIALOGUE-ATTRIBUTION PATTERNS")
print("------------------------------")

attribution_patterns = [
    r'“[^”]{1,300},”?\s+\w+\s+(?:said|asked|replied|answered|cried|remarked)',
    r'\w+\s+(?:said|asked|replied|answered|cried|remarked)[,:]?\s+“[^”]{1,300}”',
    r'“[^”]{1,300}”\s+(?:said|asked|replied|answered|cried|remarked)',
]

for pattern in attribution_patterns:
    matches = re.findall(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    print(
        f"Pattern: {pattern}"
    )
    print(
        f"Matches: {len(matches):,}"
    )
    print()

# --------------------------------------------------
# SAMPLE QUOTED PASSAGES
# --------------------------------------------------

print("SAMPLE QUOTED PASSAGES")
print("----------------------")

samples = curly_matches[:20]

if not samples:
    samples = straight_matches[:20]

for i, sample in enumerate(samples, start=1):
    sample_clean = " ".join(
        sample.split()
    )

    if len(sample_clean) > 300:
        sample_clean = (
            sample_clean[:300]
            + "..."
        )

    print(
        f"{i:02d}: {sample_clean}"
    )

print()

# --------------------------------------------------
# LINES CONTAINING QUOTATION MARKS
# --------------------------------------------------

print("SAMPLE LINES CONTAINING DIALOGUE MARKERS")
print("-----------------------------------------")

dialogue_lines = []

for line_no, line in enumerate(
    text.splitlines(),
    start=1
):
    if (
        "“" in line
        or "”" in line
        or '"' in line
    ):
        dialogue_lines.append(
            (line_no, line.strip())
        )

for line_no, line in dialogue_lines[:40]:
    if len(line) > 300:
        line = line[:300] + "..."

    print(
        f"{line_no:06d}: {line}"
    )

print()

print("DIALOGUE PATTERN INSPECTION COMPLETE.")