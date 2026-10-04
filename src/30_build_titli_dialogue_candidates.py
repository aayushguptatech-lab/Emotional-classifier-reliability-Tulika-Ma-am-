from pathlib import Path
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"
OUT_DIR = ROOT / "data" / "extracted" / "hindi" / "titli"
REPORT = OUT_DIR / "titli_dialogue_source_profile.txt"

OUT_DIR.mkdir(parents=True, exist_ok=True)

text = SOURCE.read_text(encoding="utf-8")
lines = text.splitlines()

# ============================================================
# EXACT TITLI SECTION HEADER
# ============================================================

section_header = re.compile(
    r"^===== TITLI SECTION ([0-9]+\.[0-9]+) \| SOURCE (.+?) =====$"
)

sections = []
current_section = None
current_source = None
current_paragraphs = []

for raw_line in lines:
    line = raw_line.strip()

    if not line:
        continue

    match = section_header.match(line)

    if match:
        if current_section is not None:
            sections.append(
                {
                    "section": current_section,
                    "source": current_source,
                    "paragraphs": current_paragraphs,
                }
            )

        current_section = match.group(1)
        current_source = match.group(2)
        current_paragraphs = []
        continue

    if current_section is not None:
        current_paragraphs.append(line)

if current_section is not None:
    sections.append(
        {
            "section": current_section,
            "source": current_source,
            "paragraphs": current_paragraphs,
        }
    )

# ============================================================
# FLATTEN PARAGRAPHS WITH PROVENANCE
# ============================================================

paragraphs = []

for section in sections:
    for paragraph_no, paragraph in enumerate(
        section["paragraphs"], start=1
    ):
        paragraphs.append(
            {
                "section": section["section"],
                "source": section["source"],
                "paragraph_no": paragraph_no,
                "text": paragraph,
            }
        )

# ============================================================
# PATTERNS
# ============================================================

patterns = {
    "double_quote": re.compile(r'[“”"„]'),
    "single_quote": re.compile(r"[‘’']"),
    "em_dash": re.compile(r"—"),
    "en_dash": re.compile(r"–"),
    "hyphen": re.compile(r"-"),
    "question": re.compile(r"[?？]"),
    "exclamation": re.compile(r"[!！]"),
    "speech_attribution": re.compile(
        r"(?:"
        r"कहा|कही|कहे|कहता|कहती|कहते|"
        r"बोला|बोली|बोले|बोलता|बोलती|बोलते|"
        r"पूछा|पूछी|पूछे|पूछता|पूछती|पूछते|"
        r"बताया|बतायी|बताये|"
        r"उत्तर दिया|उत्तर देती|उत्तर देते|"
        r"कहने लगा|कहने लगी|कहने लगे|"
        r"पुकारा|पुकारते|चिल्लाया|चिल्लाई|"
        r"फुसफुसाया|फुसफुसाई"
        r")"
    ),
    "speech_verb": re.compile(
        r"(?:"
        r"बोल|कह|पूछ|उत्तर|बत|"
        r"चिल्ल|फुसफुस|गरज|पुकार|"
        r"समझा|समझी|"
        r"हँस|रो"
        r")"
    ),
}

pattern_counts = Counter()
examples = {name: [] for name in patterns}

length_buckets = Counter()

# ============================================================
# PROFILE
# ============================================================

for item in paragraphs:

    p = item["text"]

    # Length
    n = len(p)

    if n <= 20:
        length_buckets["0-20"] += 1
    elif n <= 50:
        length_buckets["21-50"] += 1
    elif n <= 100:
        length_buckets["51-100"] += 1
    elif n <= 200:
        length_buckets["101-200"] += 1
    elif n <= 500:
        length_buckets["201-500"] += 1
    elif n <= 1000:
        length_buckets["501-1000"] += 1
    else:
        length_buckets[">1000"] += 1

    for name, pattern in patterns.items():

        if pattern.search(p):
            pattern_counts[name] += 1

            if len(examples[name]) < 15:
                examples[name].append(item)

# ============================================================
# COMBINATION ANALYSIS
# ============================================================

combination_counts = Counter()

combination_examples = {
    "quote_plus_attribution": [],
    "dash_plus_attribution": [],
    "quote_plus_question": [],
    "quote_plus_exclamation": [],
    "long_speech_verb_without_quote_or_dash": [],
    "multiple_dash_markers": [],
}

for item in paragraphs:

    p = item["text"]

    has_quote = (
        patterns["double_quote"].search(p)
        or patterns["single_quote"].search(p)
    )

    has_dash = (
        patterns["em_dash"].search(p)
        or patterns["en_dash"].search(p)
        or patterns["hyphen"].search(p)
    )

    has_attribution = patterns["speech_attribution"].search(p)
    has_question = patterns["question"].search(p)
    has_exclamation = patterns["exclamation"].search(p)

    dash_count = len(re.findall(r"[—–-]", p))

    if has_quote and has_attribution:

        combination_counts["quote_plus_attribution"] += 1

        if len(combination_examples["quote_plus_attribution"]) < 20:
            combination_examples[
                "quote_plus_attribution"
            ].append(item)

    if has_dash and has_attribution:

        combination_counts["dash_plus_attribution"] += 1

        if len(combination_examples["dash_plus_attribution"]) < 20:
            combination_examples[
                "dash_plus_attribution"
            ].append(item)

    if has_quote and has_question:

        combination_counts["quote_plus_question"] += 1

        if len(combination_examples["quote_plus_question"]) < 20:
            combination_examples[
                "quote_plus_question"
            ].append(item)

    if has_quote and has_exclamation:

        combination_counts["quote_plus_exclamation"] += 1

        if len(combination_examples["quote_plus_exclamation"]) < 20:
            combination_examples[
                "quote_plus_exclamation"
            ].append(item)

    if (
        len(p) > 500
        and patterns["speech_verb"].search(p)
        and not has_quote
        and not has_dash
    ):

        combination_counts[
            "long_speech_verb_without_quote_or_dash"
        ] += 1

        if len(
            combination_examples[
                "long_speech_verb_without_quote_or_dash"
            ]
        ) < 20:

            combination_examples[
                "long_speech_verb_without_quote_or_dash"
            ].append(item)

    if dash_count >= 2:

        combination_counts["multiple_dash_markers"] += 1

        if len(combination_examples["multiple_dash_markers"]) < 20:
            combination_examples[
                "multiple_dash_markers"
            ].append(item)

# ============================================================
# REPORT
# ============================================================

with REPORT.open("w", encoding="utf-8") as f:

    f.write("TITLI DIALOGUE SOURCE PROFILE\n")
    f.write("=" * 80 + "\n\n")

    f.write("Purpose\n")
    f.write("-" * 80 + "\n")
    f.write(
        "Profiles the canonical Titli clean source before dialogue "
        "candidate extraction. No dialogue candidates are created "
        "by this script.\n\n"
    )

    f.write("Source\n")
    f.write("-" * 80 + "\n")
    f.write(f"{SOURCE}\n")
    f.write(f"Source bytes: {SOURCE.stat().st_size}\n\n")

    f.write("Overall structure\n")
    f.write("-" * 80 + "\n")
    f.write(f"Sections detected: {len(sections)}\n")
    f.write(f"Canonical paragraphs: {len(paragraphs)}\n\n")

    f.write("Section inventory\n")
    f.write("-" * 80 + "\n")

    for section in sections:

        f.write(
            f"SECTION {section['section']} | "
            f"SOURCE {section['source']} | "
            f"PARAGRAPHS {len(section['paragraphs'])}\n"
        )

    f.write("\n")

    f.write("Paragraph length distribution\n")
    f.write("-" * 80 + "\n")

    for bucket in (
        "0-20",
        "21-50",
        "51-100",
        "101-200",
        "201-500",
        "501-1000",
        ">1000",
    ):

        f.write(
            f"{bucket}: {length_buckets[bucket]}\n"
        )

    f.write("\n")

    f.write("Pattern counts\n")
    f.write("-" * 80 + "\n")

    for name, count in pattern_counts.items():

        f.write(
            f"{name}: {count}\n"
        )

    f.write("\n")

    f.write("Combination counts\n")
    f.write("-" * 80 + "\n")

    for name, count in combination_counts.items():

        f.write(
            f"{name}: {count}\n"
        )

    # --------------------------------------------------------
    # Individual examples
    # --------------------------------------------------------

    for name in patterns:

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(f"EXAMPLES: {name}\n")
        f.write("=" * 80 + "\n")

        for item in examples[name]:

            f.write(
                f"\n[{item['section']} | "
                f"{item['source']} | "
                f"paragraph {item['paragraph_no']}]\n"
            )

            f.write(item["text"])
            f.write("\n")

    # --------------------------------------------------------
    # Combination examples
    # --------------------------------------------------------

    for name, items in combination_examples.items():

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(
            f"COMBINATION EXAMPLES: {name}\n"
        )
        f.write("=" * 80 + "\n")

        for item in items:

            f.write(
                f"\n[{item['section']} | "
                f"{item['source']} | "
                f"paragraph {item['paragraph_no']}]\n"
            )

            f.write(item["text"])
            f.write("\n")

print(f"Profile report: {REPORT}")
print(f"Sections: {len(sections)}")
print(f"Paragraphs: {len(paragraphs)}")
print(f"Report bytes: {REPORT.stat().st_size}")