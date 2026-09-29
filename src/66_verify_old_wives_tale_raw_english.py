from pathlib import Path


FILE = Path(
    "data/raw/english/the_old_wives_tale_raw.txt"
)


print("Verifying The Old Wives' Tale raw source")
print("=========================================")
print()


if not FILE.exists():
    raise FileNotFoundError(
        f"Raw file not found: {FILE}"
    )


text = FILE.read_text(
    encoding="utf-8"
)


print("FILE CHECK")
print("----------")
print(f"Exists: YES")
print(f"Characters: {len(text):,}")
print(f"Words: {len(text.split()):,}")
print(f"Lines: {len(text.splitlines()):,}")
print()


# ---------------------------------------------------------
# Expected source markers
# ---------------------------------------------------------

markers = [
    "THE OLD WIVES' TALE",
    "ARNOLD BENNETT",
]


print("EXPECTED MARKERS")
print("----------------")

for marker in markers:

    found = marker.lower() in text.lower()

    print(
        f"{marker}: "
        f"{'FOUND' if found else 'NOT FOUND'}"
    )

    if not found:
        raise ValueError(
            f"Required marker not found: {marker}"
        )


print()


# ---------------------------------------------------------
# Show beginning of raw source
# ---------------------------------------------------------

print("FIRST 30 LINES")
print("--------------")

for i, line in enumerate(
    text.splitlines()[:30],
    start=1
):

    print(
        f"{i:02d}: {line}"
    )


print()
print("RAW SOURCE VERIFICATION PASSED.")