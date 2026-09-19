from pathlib import Path


# ---------------------------------------------------------
# 1. File locations
# ---------------------------------------------------------

RAW_FILE = Path(
    "data/raw/english/the_valley_of_fear_raw.txt"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)


# ---------------------------------------------------------
# 2. Read the immutable raw source
# ---------------------------------------------------------

text = RAW_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------
# 3. Define the Gutenberg boundaries
# ---------------------------------------------------------

START_MARKER = (
    "*** START OF THE PROJECT GUTENBERG "
    "EBOOK THE VALLEY OF FEAR ***"
)

END_MARKER = (
    "*** END OF THE PROJECT GUTENBERG "
    "EBOOK THE VALLEY OF FEAR ***"
)


# ---------------------------------------------------------
# 4. Find the boundaries
# ---------------------------------------------------------

start_position = text.find(START_MARKER)
end_position = text.find(END_MARKER)


if start_position == -1:
    raise ValueError("Gutenberg START marker was not found.")


if end_position == -1:
    raise ValueError("Gutenberg END marker was not found.")


if start_position >= end_position:
    raise ValueError(
        "The Gutenberg START marker occurs after the END marker."
    )


# ---------------------------------------------------------
# 5. Extract only the literary text
# ---------------------------------------------------------

clean_text = text[
    start_position + len(START_MARKER):end_position
]


# ---------------------------------------------------------
# 6. Remove excess blank space at the boundaries
# ---------------------------------------------------------

clean_text = clean_text.strip()


# ---------------------------------------------------------
# 7. Save the cleaned copy
# ---------------------------------------------------------

CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)

CLEAN_FILE.write_text(
    clean_text,
    encoding="utf-8"
)


# ---------------------------------------------------------
# 8. Report what happened
# ---------------------------------------------------------

print("=" * 60)
print("ENGLISH SOURCE CLEANING")
print("=" * 60)

print(f"Raw file:   {RAW_FILE}")
print(f"Clean file: {CLEAN_FILE}")

print()
print(f"Raw characters:   {len(text):,}")
print(f"Clean characters: {len(clean_text):,}")

print()
print(f"Start marker position: {start_position:,}")
print(f"End marker position:   {end_position:,}")

print()
print("Removed:")
print("- Gutenberg introductory material")
print("- Gutenberg closing/license material")

print()
print("Preserved:")
print("- Novel text")
print("- Chapter headings")
print("- Original spelling")
print("- Original punctuation")
print("- Quotation marks")
print("- Dialogue")
print("- Literary structure")

print()
print("CLEANING COMPLETE")
print("=" * 60)