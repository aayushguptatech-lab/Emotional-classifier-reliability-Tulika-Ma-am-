from pathlib import Path
from bs4 import BeautifulSoup
import re
import hashlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw" / "hindi" / "titli"
CLEAN_DIR = ROOT / "data" / "cleaned" / "hindi"

OUT = CLEAN_DIR / "titli_clean.txt"
VALIDATION = CLEAN_DIR / "titli_clean_validation.txt"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CANONICAL WIKISOURCE SECTION ORDER
# ============================================================

SOURCE_FILES = [
    ("1.1", "titli_01.html"),
    ("1.2", "titli_02.html"),
    ("1.3", "titli_03.html"),
    ("1.4", "titli_04.html"),
    ("1.5", "titli_05.html"),
    ("1.6", "titli_06.html"),
    ("1.7", "titli_07.html"),
    ("1.8", "titli_08.html"),

    ("2.1", "titli_09.html"),
    ("2.2", "titli_10.html"),
    ("2.3", "titli_11.html"),
    ("2.4", "titli_12.html"),
    ("2.5", "titli_13.html"),

    ("2.9", "titli_17.html"),
    ("2.10", "titli_18.html"),

    ("3.1", "titli_19.html"),
    ("3.2", "titli_20.html"),
    ("3.3", "titli_21.html"),
    ("3.4", "titli_22.html"),
    ("3.5", "titli_23.html"),
    ("3.6", "titli_24.html"),
    ("3.7", "titli_25.html"),
    ("3.8", "titli_26.html"),

    ("4.1", "titli_27.html"),
    ("4.2", "titli_28.html"),
    ("4.3", "titli_29.html"),
    ("4.4", "titli_30.html"),
    ("4.5", "titli_31.html"),
]

MISSING_SECTIONS = ["2.6", "2.7", "2.8"]


INTERFACE_LINES = {
    "सामग्री पर जाएँ",
    "मुख्य मेन्यू",
    "साइडबार पर ले जाएँ",
    "छिपाएँ",
    "खोजें",
    "दिखावट",
    "दान करें",
    "खाता बनाएँ",
    "लॉग-इन करें",
    "लेखक",
    "विषय",
    "समाज",
    "हाल की घटनाएँ",
    "हाल में हुए परिवर्तन",
    "सहायता",
    "चौपाल",
    "मुखपृष्ठ",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize paragraph text while preserving the paragraph itself.

    Important:
    - Internal whitespace is normalized.
    - New paragraph boundaries are NOT created here.
    - Paragraphs are returned as independent strings.
    """

    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Zero-width characters observed in the Wikisource source.
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Collapse horizontal whitespace only.
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse accidental repeated internal newlines.
    text = re.sub(r"\n+", " ", text)

    return text.strip()


# ============================================================
# MAIN CONTENT EXTRACTION
# ============================================================

def extract_main_content(raw_html: str) -> list[str]:
    """
    Extract canonical paragraph-like blocks from a Wikisource page.

    We deliberately avoid recursively collecting every div because
    nested div/p structures can cause duplicate extraction.

    Priority:
      1. p
      2. poem
      3. blockquote
      4. direct block-level divs when no paragraph elements exist
    """

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove definite interface elements.
    for tag in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "form",
    ]):
        tag.decompose()

    # Locate MediaWiki/Wikisource article body.
    main = (
        soup.select_one("#mw-content-text")
        or soup.select_one(".mw-parser-output")
        or soup.select_one("#bodyContent")
    )

    if main is None:
        raise RuntimeError("Could not locate Wikisource main content")

    # Remove interface elements inside article body.
    for selector in [
        ".mw-editsection",
        ".mw-jump",
        ".noprint",
        ".metadata",
        ".catlinks",
        ".navbox",
        ".navigation-not-searchable",
        ".printfooter",
        ".thumb",
        ".gallery",
        ".portal",
        ".toc",
    ]:
        for tag in main.select(selector):
            tag.decompose()

    # --------------------------------------------------------
    # First choice: explicit paragraph-like elements
    # --------------------------------------------------------

    elements = main.find_all(
        ["p", "poem", "blockquote"],
        recursive=True,
    )

    paragraphs = []

    for element in elements:
        text = element.get_text(" ", strip=True)
        text = normalize_text(text)

        if not text:
            continue

        if text in INTERFACE_LINES:
            continue

        paragraphs.append(text)

    # --------------------------------------------------------
    # Fallback for pages without explicit p/poem/blockquote
    # --------------------------------------------------------

    if not paragraphs:
        for child in main.find_all("div", recursive=False):
            text = child.get_text(" ", strip=True)
            text = normalize_text(text)

            if not text:
                continue

            if text in INTERFACE_LINES:
                continue

            paragraphs.append(text)

    # --------------------------------------------------------
    # Remove only consecutive exact duplicates.
    # --------------------------------------------------------

    clean = []

    for paragraph in paragraphs:
        if not clean or paragraph != clean[-1]:
            clean.append(paragraph)

    return clean


# ============================================================
# HASH
# ============================================================

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ============================================================
# PROCESS SOURCE FILES
# ============================================================

validation = []

all_sections = []

total_source_bytes = 0
total_paragraphs = 0

validation.append("TITLI (तितली) — CANONICAL CLEAN SOURCE VALIDATION")
validation.append("")
validation.append("Author: जयशंकर प्रसाद")
validation.append("Source: Hindi Wikisource")
validation.append("")

validation.append("1. SOURCE SECTIONS USED")

for section, filename in SOURCE_FILES:

    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file missing: {path}"
        )

    raw_bytes = path.read_bytes()

    raw_html = raw_bytes.decode(
        "utf-8",
        errors="replace",
    )

    total_source_bytes += len(raw_bytes)

    soup = BeautifulSoup(
        raw_html,
        "html.parser",
    )

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else ""
    )

    paragraphs = extract_main_content(raw_html)

    total_paragraphs += len(paragraphs)

    all_sections.append(
        (
            section,
            filename,
            title,
            paragraphs,
        )
    )

    validation.append(
        f"{section} | {filename} | "
        f"bytes={len(raw_bytes)} | "
        f"paragraphs={len(paragraphs)} | "
        f"title={title!r}"
    )


# ============================================================
# MISSING SOURCE SECTIONS
# ============================================================

validation.append("")
validation.append("2. MISSING SOURCE SECTIONS")

validation.append(
    "Missing and not reconstructed: "
    + ", ".join(MISSING_SECTIONS)
)


# ============================================================
# EXCLUDED FILES
# ============================================================

validation.append("")
validation.append("3. EXCLUDED FILES")

validation.append(
    "titli_001.html — excluded from canonical source because "
    "it is byte-identical to titli_01.html."
)

validation.append(
    "titli_part_1.html — excluded because source inspection "
    "identified it as a Wikisource landing/navigation page "
    "rather than novel prose."
)


# ============================================================
# BUILD CANONICAL CLEAN SOURCE
# ============================================================

output_parts = []

for section, filename, title, paragraphs in all_sections:

    output_parts.append(
        f"===== TITLI SECTION {section} | SOURCE {filename} ====="
    )

    # IMPORTANT:
    # Each extracted paragraph is written as exactly one line.
    # Sections are separated by one blank line.
    output_parts.extend(paragraphs)

    output_parts.append("")


clean_text = "\n".join(output_parts).strip() + "\n"

clean_bytes = clean_text.encode("utf-8")

OUT.write_bytes(clean_bytes)


# ============================================================
# CLEAN SOURCE VALIDATION
# ============================================================

validation.append("")
validation.append("4. CLEAN SOURCE")

validation.append(f"Output: {OUT}")
validation.append(
    f"Source files used: {len(SOURCE_FILES)}"
)
validation.append(
    f"Source bytes read: {total_source_bytes}"
)
validation.append(
    f"Clean source bytes: {len(clean_bytes)}"
)
validation.append(
    f"Clean source paragraphs: {total_paragraphs}"
)
validation.append(
    f"Clean source SHA256: {sha256_bytes(clean_bytes)}"
)


# ============================================================
# INDEPENDENT LINE-LEVEL CHECK
# ============================================================

section_headers = [
    f"===== TITLI SECTION {section} | SOURCE {filename} ====="
    for section, filename in SOURCE_FILES
]

physical_lines = clean_text.splitlines()

found_headers = [
    line
    for line in physical_lines
    if line.startswith("===== TITLI SECTION ")
]

content_lines = [
    line
    for line in physical_lines
    if line.strip()
    and not line.startswith("===== TITLI SECTION ")
]

validation.append("")
validation.append("5. LINE-LEVEL STRUCTURE CHECKS")

validation.append(
    f"Physical lines: {len(physical_lines)}"
)

validation.append(
    f"Section headers expected: {len(section_headers)}"
)

validation.append(
    f"Section headers found: {len(found_headers)}"
)

validation.append(
    "Section header count: "
    + (
        "PASS"
        if len(found_headers) == len(section_headers)
        else "FAIL"
    )
)

validation.append(
    f"Non-header content lines: {len(content_lines)}"
)

validation.append(
    f"Extracted paragraph count expected: {total_paragraphs}"
)

validation.append(
    "Paragraph serialization check: "
    + (
        "PASS"
        if len(content_lines) == total_paragraphs
        else "FAIL"
    )
)


# ============================================================
# CONTAMINATION CHECKS
# ============================================================

lower = clean_text.lower()

validation.append("")
validation.append("6. INTERFACE CONTAMINATION CHECKS")

for forbidden in [
    "log in",
    "create account",
    "donate",
    "main menu",
    "sidebar",
]:

    validation.append(
        f"Interface marker {forbidden!r}: "
        f"{'FOUND' if forbidden in lower else 'NOT FOUND'}"
    )


# ============================================================
# SECTION HEADER CHECK
# ============================================================

headers_found = sum(
    1
    for section, _, _, _ in all_sections
    if f"===== TITLI SECTION {section} |" in clean_text
)

validation.append("")
validation.append("7. STRUCTURAL CHECKS")

validation.append(
    f"Expected section headers: {len(SOURCE_FILES)}"
)

validation.append(
    f"Found section headers: {headers_found}"
)

validation.append(
    "Section-header count: "
    + (
        "PASS"
        if headers_found == len(SOURCE_FILES)
        else "FAIL"
    )
)


# ============================================================
# CONCLUSION
# ============================================================

validation.append("")
validation.append("8. CONCLUSION")

validation.append(
    "Canonical clean source constructed from all available "
    "verified Wikisource novel sections."
)

validation.append(
    "Missing sections 2.6, 2.7, and 2.8 remain explicitly "
    "unavailable and were not synthesized."
)

validation.append(
    "Paragraph-level source structure is preserved as "
    "one extracted paragraph per physical content line."
)

validation.append(
    "No dialogue extraction or speaker attribution was "
    "performed at this stage."
)


# ============================================================
# WRITE VALIDATION
# ============================================================

VALIDATION.write_text(
    "\n".join(validation) + "\n",
    encoding="utf-8",
)


# ============================================================
# CONSOLE OUTPUT
# ============================================================

print(f"Clean source: {OUT}")
print(f"Validation: {VALIDATION}")
print(f"Sections used: {len(SOURCE_FILES)}")
print(
    f"Missing sections: {', '.join(MISSING_SECTIONS)}"
)
print(f"Clean paragraphs: {total_paragraphs}")
print(f"Clean bytes: {len(clean_bytes)}")
print(
    f"Clean SHA256: {sha256_bytes(clean_bytes)}"
)