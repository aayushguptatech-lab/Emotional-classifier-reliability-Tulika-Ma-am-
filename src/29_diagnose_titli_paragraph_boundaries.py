from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"

text = SOURCE.read_text(encoding="utf-8")

print("FILE:", SOURCE)
print("BYTES:", len(text.encode("utf-8")))
print("TOTAL \\n:", text.count("\n"))
print("TOTAL \\r:", text.count("\r"))
print("DOUBLE NEWLINE:", text.count("\n\n"))
print("TRIPLE NEWLINE:", text.count("\n\n\n"))
print("UNICODE PARAGRAPH SEPARATOR:", text.count("\u2029"))
print("ZERO-WIDTH SPACE:", text.count("\u200b"))
print("ZERO-WIDTH NO-BREAK SPACE:", text.count("\ufeff"))

print("\n--- FIRST 2000 RAW CHARACTERS ---\n")
print(repr(text[:2000]))

print("\n--- NEWLINE CONTEXT SAMPLES ---\n")

positions = []
start = 0

while True:
    pos = text.find("\n", start)

    if pos == -1:
        break

    positions.append(pos)
    start = pos + 1

    if len(positions) >= 30:
        break

for i, pos in enumerate(positions, start=1):
    left = max(0, pos - 40)
    right = min(len(text), pos + 80)

    print(f"\nNEWLINE {i} @ {pos}")
    print(repr(text[left:right]))

print("\n--- SECTION 1.1 ANALYSIS ---\n")

marker = "===== TITLI SECTION 1.1 | SOURCE titli_01.html ====="

start = text.find(marker)

if start == -1:
    print("SECTION 1.1 MARKER NOT FOUND")
else:
    start += len(marker)

    next_marker = text.find(
        "===== TITLI SECTION 1.2 | SOURCE titli_02.html =====",
        start,
    )

    body = text[start:next_marker]

    print("SECTION 1.1 BODY LENGTH:", len(body))
    print("SECTION 1.1 \\n COUNT:", body.count("\n"))
    print("SECTION 1.1 \\n\\n COUNT:", body.count("\n\n"))
    print("SECTION 1.1 \\u2029 COUNT:", body.count("\u2029"))

    print("\nFIRST 3000 CHARACTERS OF SECTION 1.1:")
    print(repr(body[:3000]))