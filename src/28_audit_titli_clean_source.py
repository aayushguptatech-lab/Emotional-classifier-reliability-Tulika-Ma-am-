from pathlib import Path
import re
import hashlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]

CLEAN_SOURCE = (
    ROOT
    / "data"
    / "cleaned"
    / "hindi"
    / "titli_clean.txt"
)

REPORT = (
    ROOT
    / "data"
    / "cleaned"
    / "hindi"
    / "titli_clean_source_audit.txt"
)


EXPECTED_SECTIONS = [
    "1.1",
    "1.2",
    "1.3",
    "1.4",
    "1.5",
    "1.6",
    "1.7",
    "1.8",
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.9",
    "2.10",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "3.7",
    "3.8",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
]

MISSING_SECTIONS = [
    "2.6",
    "2.7",
    "2.8",
]


SECTION_PATTERN = re.compile(
    r"^===== TITLI SECTION "
    r"([0-9]+\.[0-9]+)"
    r" \| SOURCE (.+?) =====$"
)


INTERFACE_TERMS = [
    "विकिस्रोत",
    "सामग्री पर जाएँ",
    "मुख्य मेन्यू",
    "साइडबार",
    "लॉग-इन",
    "खाता बनाएँ",
    "दान करें",
    "हाल के परिवर्तन",
    "चौपाल",
    "मुखपृष्ठ",
    "Main menu",
    "Sidebar",
    "Log in",
    "Create account",
    "Donate",
]


# ============================================================
# FILE CHECK
# ============================================================

if not CLEAN_SOURCE.exists():
    raise FileNotFoundError(
        f"Clean source not found: {CLEAN_SOURCE}"
    )


text = CLEAN_SOURCE.read_text(
    encoding="utf-8"
)

raw_bytes = text.encode("utf-8")

sha256 = hashlib.sha256(
    raw_bytes
).hexdigest()

byte_size = len(raw_bytes)

physical_lines = text.splitlines()


# ============================================================
# PARSE CANONICAL SOURCE
#
# Format produced by src/27_build_titli_clean_source.py:
#
# ===== SECTION HEADER =====
# paragraph
# paragraph
# paragraph
#
# ===== NEXT SECTION HEADER =====
#
# Therefore every non-empty non-header line is one
# canonical extracted paragraph.
# ============================================================

sections = []

current = None

for line_number, line in enumerate(
    physical_lines,
    start=1,
):

    stripped = line.strip()

    match = SECTION_PATTERN.match(
        stripped
    )

    if match:

        if current is not None:
            sections.append(current)

        current = {
            "section": match.group(1),
            "source": match.group(2).strip(),
            "header_line": line_number,
            "paragraphs": [],
        }

        continue

    if current is None:
        # Ignore leading content before the first section
        # only if it is blank.
        if stripped:
            raise RuntimeError(
                "Non-empty content found before first "
                f"section header at line {line_number}: "
                f"{stripped[:200]!r}"
            )

        continue

    # Blank lines separate sections.
    # Non-empty lines are canonical paragraphs.
    if stripped:
        current["paragraphs"].append(
            {
                "line": line_number,
                "text": stripped,
            }
        )


if current is not None:
    sections.append(current)


# ============================================================
# GLOBAL STRUCTURE
# ============================================================

detected_sections = [
    section["section"]
    for section in sections
]

missing_from_clean = [
    section
    for section in EXPECTED_SECTIONS
    if section not in detected_sections
]

unexpected_sections = [
    section
    for section in detected_sections
    if section not in EXPECTED_SECTIONS
]

duplicate_sections = sorted(
    {
        section
        for section in detected_sections
        if detected_sections.count(section) > 1
    }
)


section_order_pass = (
    detected_sections == EXPECTED_SECTIONS
)

coverage_pass = (
    section_order_pass
    and not unexpected_sections
    and not duplicate_sections
)


# ============================================================
# PARAGRAPH STATISTICS
# ============================================================

all_paragraphs = []

long_paragraphs = []

short_paragraphs = []

empty_lines_inside_sections = []

interface_hits = []

duplicate_consecutive_paragraphs = []


for section_data in sections:

    section = section_data["section"]
    source = section_data["source"]

    paragraphs = section_data["paragraphs"]

    lengths = [
        len(item["text"])
        for item in paragraphs
    ]

    if lengths:

        minimum = min(lengths)
        maximum = max(lengths)
        average = sum(lengths) / len(lengths)

    else:

        minimum = 0
        maximum = 0
        average = 0

    section_data["min_length"] = minimum
    section_data["max_length"] = maximum
    section_data["avg_length"] = average

    previous_text = None

    for number, item in enumerate(
        paragraphs,
        start=1,
    ):

        paragraph = item["text"]
        line_number = item["line"]

        all_paragraphs.append(
            (
                section,
                number,
                line_number,
                paragraph,
            )
        )

        length = len(paragraph)

        if length > 1000:

            long_paragraphs.append(
                (
                    section,
                    number,
                    line_number,
                    length,
                    paragraph,
                )
            )

        if 1 <= length <= 20:

            short_paragraphs.append(
                (
                    section,
                    number,
                    line_number,
                    length,
                    paragraph,
                )
            )

        hits = [
            term
            for term in INTERFACE_TERMS
            if term in paragraph
        ]

        if hits:

            interface_hits.append(
                (
                    section,
                    number,
                    line_number,
                    hits,
                    paragraph,
                )
            )

        if (
            previous_text is not None
            and paragraph == previous_text
        ):

            duplicate_consecutive_paragraphs.append(
                (
                    section,
                    number,
                    line_number,
                    paragraph,
                )
            )

        previous_text = paragraph


# ============================================================
# EXPECTED PARAGRAPH COUNT
#
# The builder reported 1,406 paragraphs.
# We independently count the actual non-empty content lines.
# ============================================================

EXPECTED_PARAGRAPHS = 1406

paragraph_count_pass = (
    len(all_paragraphs)
    == EXPECTED_PARAGRAPHS
)


# ============================================================
# BUILD REPORT
# ============================================================

report = []

report.append(
    "TITLI (तितली) — CLEAN SOURCE INDEPENDENT AUDIT"
)

report.append("")

report.append(
    "Author: जयशंकर प्रसाद"
)

report.append(
    "Source basis: canonical cleaned Wikisource pages"
)

report.append("")


# ============================================================
# 1. FILE INTEGRITY
# ============================================================

report.append(
    "1. FILE INTEGRITY"
)

report.append(
    f"Clean source: {CLEAN_SOURCE}"
)

report.append(
    f"Bytes: {byte_size}"
)

report.append(
    f"SHA256: {sha256}"
)

report.append(
    f"Total physical lines: {len(physical_lines)}"
)

report.append("")


# ============================================================
# 2. SECTION STRUCTURE
# ============================================================

report.append(
    "2. SECTION STRUCTURE"
)

report.append(
    f"Expected sections: {len(EXPECTED_SECTIONS)}"
)

report.append(
    f"Detected sections: {len(sections)}"
)

report.append(
    "Expected-section order: "
    + (
        "PASS"
        if section_order_pass
        else "FAIL"
    )
)

report.append(
    "Expected-section coverage: "
    + (
        "PASS"
        if coverage_pass
        else "REVIEW"
    )
)

report.append(
    f"Missing from clean source: "
    f"{missing_from_clean if missing_from_clean else 'NONE'}"
)

report.append(
    f"Unexpected sections: "
    f"{unexpected_sections if unexpected_sections else 'NONE'}"
)

report.append(
    f"Duplicate sections: "
    f"{duplicate_sections if duplicate_sections else 'NONE'}"
)

report.append("")


# ============================================================
# 3. SECTION-BY-SECTION CONTENT AUDIT
# ============================================================

report.append(
    "3. SECTION-BY-SECTION CONTENT AUDIT"
)

for section_data in sections:

    report.append(
        f"{section_data['section']} | "
        f"{section_data['source']} | "
        f"paragraphs={len(section_data['paragraphs'])} | "
        f"min={section_data['min_length']} | "
        f"max={section_data['max_length']} | "
        f"avg={section_data['avg_length']:.1f}"
    )

report.append("")


# ============================================================
# 4. PARAGRAPH COUNT VALIDATION
# ============================================================

report.append(
    "4. PARAGRAPH COUNT VALIDATION"
)

report.append(
    f"Expected paragraph count: "
    f"{EXPECTED_PARAGRAPHS}"
)

report.append(
    f"Independently counted paragraphs: "
    f"{len(all_paragraphs)}"
)

report.append(
    "Paragraph count: "
    + (
        "PASS"
        if paragraph_count_pass
        else "FAIL"
    )
)

report.append(
    "Counting method: "
    "one non-empty physical content line = one "
    "canonical extracted paragraph"
)

report.append("")


# ============================================================
# 5. LONG PARAGRAPH REVIEW
# ============================================================

report.append(
    "5. LONG-PARAGRAPH REVIEW (>1000 CHARACTERS)"
)

report.append(
    f"Total long paragraphs: "
    f"{len(long_paragraphs)}"
)

if long_paragraphs:

    for (
        section,
        number,
        line_number,
        length,
        paragraph,
    ) in long_paragraphs:

        preview = (
            paragraph[:500]
            .replace("\n", " ")
        )

        report.append(
            f"{section} paragraph {number} "
            f"(line {line_number}) | "
            f"length={length} | "
            f"preview={preview!r}"
        )

else:

    report.append(
        "None detected."
    )

report.append("")


# ============================================================
# 6. VERY-SHORT PARAGRAPH REVIEW
# ============================================================

report.append(
    "6. VERY-SHORT PARAGRAPH REVIEW "
    "(1–20 CHARACTERS)"
)

report.append(
    f"Total very-short paragraphs: "
    f"{len(short_paragraphs)}"
)

if short_paragraphs:

    for (
        section,
        number,
        line_number,
        length,
        paragraph,
    ) in short_paragraphs[:200]:

        report.append(
            f"{section} paragraph {number} "
            f"(line {line_number}) | "
            f"length={length} | "
            f"text={paragraph!r}"
        )

    if len(short_paragraphs) > 200:

        report.append(
            f"... "
            f"{len(short_paragraphs) - 200} "
            f"additional very-short paragraphs omitted."
        )

else:

    report.append(
        "None detected."
    )

report.append("")


# ============================================================
# 7. INTERFACE CONTAMINATION
# ============================================================

report.append(
    "7. INTERFACE / NAVIGATION CONTAMINATION"
)

report.append(
    f"Potential interface-contaminated paragraphs: "
    f"{len(interface_hits)}"
)

if interface_hits:

    for (
        section,
        number,
        line_number,
        hits,
        paragraph,
    ) in interface_hits:

        report.append(
            f"{section} paragraph {number} "
            f"(line {line_number}) | "
            f"hits={hits} | "
            f"text={paragraph[:500]!r}"
        )

else:

    report.append(
        "No obvious interface/navigation contamination detected."
    )

report.append("")


# ============================================================
# 8. CONSECUTIVE DUPLICATE PARAGRAPHS
# ============================================================

report.append(
    "8. CONSECUTIVE DUPLICATE PARAGRAPH CHECK"
)

report.append(
    f"Consecutive duplicate paragraphs: "
    f"{len(duplicate_consecutive_paragraphs)}"
)

if duplicate_consecutive_paragraphs:

    for (
        section,
        number,
        line_number,
        paragraph,
    ) in duplicate_consecutive_paragraphs[:100]:

        report.append(
            f"{section} paragraph {number} "
            f"(line {line_number}) | "
            f"text={paragraph[:500]!r}"
        )

else:

    report.append(
        "None detected."
    )

report.append("")


# ============================================================
# 9. MISSING SOURCE SECTIONS
# ============================================================

report.append(
    "9. MISSING SOURCE SECTIONS"
)

report.append(
    "The following Wikisource novel sections were "
    "unavailable and are intentionally absent:"
)

report.append(
    ", ".join(MISSING_SECTIONS)
)

report.append(
    "No text was synthesized or inferred for these sections."
)

report.append("")


# ============================================================
# 10. SOURCE ORDER
# ============================================================

report.append(
    "10. SOURCE-ORDER CHECK"
)

if section_order_pass:

    report.append(
        "PASS — available sections occur in the expected "
        "canonical order."
    )

else:

    report.append(
        "FAIL — detected section order differs from "
        "expected canonical order."
    )

report.append("")


# ============================================================
# 11. CONTENT-SIZE SUMMARY
# ============================================================

report.append(
    "11. CONTENT-SIZE SUMMARY"
)

report.append(
    f"Total clean paragraphs: "
    f"{len(all_paragraphs)}"
)

report.append(
    f"Paragraphs >1000 chars: "
    f"{len(long_paragraphs)}"
)

report.append(
    f"Paragraphs 1–20 chars: "
    f"{len(short_paragraphs)}"
)

report.append(
    f"Interface-contaminated paragraphs: "
    f"{len(interface_hits)}"
)

report.append(
    f"Consecutive duplicate paragraphs: "
    f"{len(duplicate_consecutive_paragraphs)}"
)

report.append("")


# ============================================================
# 12. FINAL AUDIT CONCLUSION
# ============================================================

report.append(
    "12. AUDIT CONCLUSION"
)

final_pass = (
    coverage_pass
    and paragraph_count_pass
    and len(all_paragraphs) > 0
    and not interface_hits
    and not duplicate_sections
)

if final_pass:

    report.append(
        "STRUCTURAL STATUS: PASS"
    )

else:

    report.append(
        "STRUCTURAL STATUS: REVIEW REQUIRED"
    )

report.append(
    "The audit independently reads the canonical clean-source "
    "format produced by src/27_build_titli_clean_source.py."
)

report.append(
    "Each non-empty content line between section headers is "
    "treated as one extracted paragraph."
)

report.append(
    "Long paragraphs are reported for manual inspection and "
    "are not automatically considered errors."
)

report.append(
    "Missing sections 2.6, 2.7, and 2.8 remain explicitly "
    "unavailable and were not reconstructed."
)

report.append(
    "This audit evaluates the canonical clean source only. "
    "No dialogue extraction or speaker attribution is performed."
)


# ============================================================
# WRITE REPORT
# ============================================================

REPORT.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)


# ============================================================
# CONSOLE OUTPUT
# ============================================================

print(
    f"Audit report: {REPORT}"
)

print(
    f"Sections detected: {len(sections)}"
)

print(
    f"Clean paragraphs: {len(all_paragraphs)}"
)

print(
    f"Expected paragraphs: {EXPECTED_PARAGRAPHS}"
)

print(
    f"Paragraph count: "
    f"{'PASS' if paragraph_count_pass else 'FAIL'}"
)

print(
    f"Long paragraphs (>1000): "
    f"{len(long_paragraphs)}"
)

print(
    f"Very short paragraphs (<=20): "
    f"{len(short_paragraphs)}"
)

print(
    f"Interface contamination hits: "
    f"{len(interface_hits)}"
)

print(
    f"Duplicate sections: "
    f"{len(duplicate_sections)}"
)

print(
    f"SHA256: {sha256}"
)

print(
    f"STRUCTURAL STATUS: "
    f"{'PASS' if final_pass else 'REVIEW REQUIRED'}"
)