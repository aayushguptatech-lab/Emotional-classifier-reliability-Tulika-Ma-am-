from pathlib import Path

RAW_FILE = Path(
    "data/raw/english/the_man_who_was_thursday_raw.txt"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_man_who_was_thursday_clean.txt"
)

print("Preparing to clean The Man Who Was Thursday...")

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Raw file not found: {RAW_FILE}"
    )

text = RAW_FILE.read_text(encoding="utf-8")

# Project Gutenberg text commonly contains a header
# before the actual novel and a license/footer after it.
# We will locate the boundaries first and refuse to
# clean automatically if the expected markers are absent.

start_marker = "THE MAN WHO WAS THURSDAY"

end_markers = [
    "*** END OF THE PROJECT GUTENBERG EBOOK",
    "*** END OF THIS PROJECT GUTENBERG EBOOK",
]

start_index = text.find(start_marker)

if start_index == -1:
    raise ValueError(
        "Could not find the novel start marker."
    )

print(f"Novel start marker found at character: {start_index:,}")

end_index = -1
matched_end_marker = None

for marker in end_markers:
    position = text.find(marker)

    if position != -1:
        end_index = position
        matched_end_marker = marker
        break

if end_index == -1:
    raise ValueError(
        "Could not find a Project Gutenberg ending marker. "
        "Do not clean the file manually."
    )

print(
    f"Novel/end boundary marker found at character: "
    f"{end_index:,}"
)
print(f"Matched ending marker: {matched_end_marker}")

if start_index >= end_index:
    raise ValueError(
        "Novel start occurs after the detected ending marker."
    )

# Keep the text beginning at the title marker.
# Remove the Gutenberg material after the novel.
clean_text = text[start_index:end_index].strip()

if len(clean_text) < 1000:
    raise ValueError(
        "Cleaned text is unexpectedly short."
    )

CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)

CLEAN_FILE.write_text(
    clean_text,
    encoding="utf-8"
)

print()
print("Cleaning successful.")
print(f"Saved to: {CLEAN_FILE}")
print(f"Clean characters: {len(clean_text):,}")
print(f"Clean words: {len(clean_text.split()):,}")
print(f"Clean lines: {len(clean_text.splitlines()):,}")