from pathlib import Path


# ---------------------------------------------------------
# 1. Locate the raw source
# ---------------------------------------------------------

RAW_FILE = Path("data/raw/english/the_valley_of_fear_raw.txt")


# ---------------------------------------------------------
# 2. Check that the file exists
# ---------------------------------------------------------

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Raw source not found: {RAW_FILE}"
    )


# ---------------------------------------------------------
# 3. Read the raw source
# ---------------------------------------------------------

text = RAW_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------
# 4. Basic measurements
# ---------------------------------------------------------

character_count = len(text)
line_count = len(text.splitlines())
word_count = len(text.split())


# ---------------------------------------------------------
# 5. Display basic information
# ---------------------------------------------------------

print("=" * 60)
print("RAW SOURCE VERIFICATION")
print("=" * 60)

print(f"File: {RAW_FILE}")
print(f"Characters: {character_count:,}")
print(f"Words: {word_count:,}")
print(f"Lines: {line_count:,}")


# ---------------------------------------------------------
# 6. Check important identifying text
# ---------------------------------------------------------

print("\nIDENTITY CHECKS")
print("-" * 60)

checks = {
    "Valley of Fear": "Valley of Fear" in text,
    "Arthur Conan Doyle": "Arthur Conan Doyle" in text,
    "Project Gutenberg": "Project Gutenberg" in text,
    "eBook #3289": "3289" in text,
}

for item, result in checks.items():
    status = "FOUND" if result else "NOT FOUND"
    print(f"{item}: {status}")


# ---------------------------------------------------------
# 7. Display the beginning of the raw source
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("BEGINNING OF RAW SOURCE")
print("=" * 60)

print(text[:2000])


# ---------------------------------------------------------
# 8. Display the end of the raw source
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("END OF RAW SOURCE")
print("=" * 60)

print(text[-2000:])


# ---------------------------------------------------------
# 9. Final status
# ---------------------------------------------------------

print("\n" + "=" * 60)

if character_count > 0:
    print("RAW SOURCE CHECK: PASSED")
else:
    print("RAW SOURCE CHECK: FAILED")

print("=" * 60)