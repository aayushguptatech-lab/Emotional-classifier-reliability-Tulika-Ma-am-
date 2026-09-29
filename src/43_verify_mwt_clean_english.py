from pathlib import Path

CLEAN_FILE = Path(
    "data/cleaned/english/the_man_who_was_thursday_clean.txt"
)

print("Verifying cleaned text:", CLEAN_FILE)

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )

text = CLEAN_FILE.read_text(encoding="utf-8")

print()
print("CLEAN FILE VERIFICATION")
print("------------------------")
print(f"File exists: YES")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")

if len(text.strip()) == 0:
    raise ValueError("Clean file is empty.")

# The Gutenberg wrapper should no longer be present.
for forbidden_marker in [
    "This eBook is for the use of anyone anywhere",
    "*** END OF THE PROJECT GUTENBERG EBOOK",
]:
    if forbidden_marker in text:
        raise ValueError(
            f"Gutenberg wrapper text still present: "
            f"{forbidden_marker}"
        )

print()
print("Checking expected novel markers...")

required_markers = [
    "THE MAN WHO WAS THURSDAY",
    "A NIGHTMARE",
    "G. K. CHESTERTON",
]

for marker in required_markers:
    if marker.lower() in text.lower():
        print(f"[PASS] Found: {marker}")
    else:
        print(f"[REVIEW] Not found: {marker}")

print()
print("First 30 lines of cleaned text:")
print("-------------------------------")

for i, line in enumerate(text.splitlines()[:30], start=1):
    print(f"{i:02d}: {line}")

print()
print("Clean-file verification complete.")