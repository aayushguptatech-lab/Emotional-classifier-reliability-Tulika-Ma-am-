from pathlib import Path


CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)


if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )


text = CLEAN_FILE.read_text(encoding="utf-8")


print("=" * 60)
print("CLEAN SOURCE VERIFICATION")
print("=" * 60)

print(f"File: {CLEAN_FILE}")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")


print("\nBOUNDARY CHECKS")
print("-" * 60)

checks = {
    "Gutenberg START marker removed":
        "*** START OF THE PROJECT GUTENBERG" not in text,

    "Gutenberg END marker removed":
        "*** END OF THE PROJECT GUTENBERG" not in text,

    "Novel title present":
        "THE VALLEY OF FEAR" in text,

    "Chapter I present":
        "Chapter I" in text,

    "Quotation marks present":
        '"' in text or "“" in text,

    "Gutenberg license removed":
        "Section 5. General Information About Project Gutenberg" not in text,
}


for name, result in checks.items():
    status = "PASS" if result else "FAIL"
    print(f"{status}: {name}")


print("\n" + "=" * 60)
print("BEGINNING OF CLEANED TEXT")
print("=" * 60)

print(text[:1500])


print("\n" + "=" * 60)
print("END OF CLEANED TEXT")
print("=" * 60)

print(text[-1500:])


print("\n" + "=" * 60)
print("CLEAN SOURCE VERIFICATION COMPLETE")
print("=" * 60)