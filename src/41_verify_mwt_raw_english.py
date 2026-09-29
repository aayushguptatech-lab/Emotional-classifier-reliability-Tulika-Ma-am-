from pathlib import Path

RAW_FILE = Path(
    "data/raw/english/the_man_who_was_thursday_raw.txt"
)

print("Verifying raw text:", RAW_FILE)

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Raw file not found: {RAW_FILE}"
    )

text = RAW_FILE.read_text(encoding="utf-8")

print()
print("RAW FILE VERIFICATION")
print("----------------------")
print(f"File exists: YES")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")

if len(text.strip()) == 0:
    raise ValueError("Raw file is empty.")

required_markers = [
    "THE MAN WHO WAS THURSDAY",
    "A NIGHTMARE",
    "G. K. CHESTERTON",
]

print()
print("Checking expected markers...")

for marker in required_markers:
    if marker.lower() in text.lower():
        print(f"[PASS] Found: {marker}")
    else:
        print(f"[REVIEW] Not found: {marker}")

print()
print("First 20 lines:")
print("----------------")

for i, line in enumerate(text.splitlines()[:20], start=1):
    print(f"{i:02d}: {line}")

print()
print("Raw-file verification complete.")