from pathlib import Path


FILE = Path(
    "data/cleaned/english/the_old_wives_tale_clean.txt"
)


print("Verifying The Old Wives' Tale clean source")
print("===========================================")
print()


if not FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {FILE}"
    )


text = FILE.read_text(
    encoding="utf-8"
)


print("FILE CHECK")
print("----------")
print("Exists: YES")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")
print()


print("EXPECTED NOVEL MARKERS")
print("----------------------")

markers = [
    "The Old Wives' Tale",
    "A Tale",
    "Arnold Bennett",
]


for marker in markers:

    found = marker.lower() in text.lower()

    print(
        f"{marker}: "
        f"{'FOUND' if found else 'NOT FOUND'}"
    )


print()


print("GUTENBERG WRAPPER CHECK")
print("------------------------")

wrapper_markers = [
    "*** START OF THE PROJECT GUTENBERG EBOOK",
    "*** END OF THE PROJECT GUTENBERG EBOOK",
]


for marker in wrapper_markers:

    found = marker.lower() in text.lower()

    print(
        f"{marker}: "
        f"{'PRESENT — REVIEW NEEDED' if found else 'ABSENT — PASS'}"
    )

    if found:

        raise ValueError(
            f"Gutenberg wrapper marker still present: {marker}"
        )


print()


print("FIRST 30 CLEAN LINES")
print("---------------------")

for i, line in enumerate(
    text.splitlines()[:30],
    start=1
):

    print(
        f"{i:02d}: {line}"
    )


print()
print("CLEAN SOURCE VERIFICATION PASSED.")