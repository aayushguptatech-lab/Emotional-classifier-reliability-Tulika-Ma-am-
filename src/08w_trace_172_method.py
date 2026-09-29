from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

terms = [
    "dialogue turns",
    "dialogue turn",
    "speaker",
    "attributed",
    "attribution",
    "turn_id",
    "The Valley of Fear",
]

files = [
    ROOT / "README.md",
    ROOT / "src",
    ROOT / "data",
]

print("=" * 80)
print("TRACEING THE 172-TURN METHODOLOGY")
print("=" * 80)

for base in files:
    paths = [base] if base.is_file() else base.rglob("*")

    for path in paths:
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".md", ".txt", ".csv"}:
            continue
        if any(x in path.parts for x in [".venv", ".git", "__pycache__"]):
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matches = []

        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()

            if "dialogue" in low or "attribut" in low or "turn" in low:
                if any(term.lower() in low for term in terms):
                    matches.append((i, line.strip()))

        if matches:
            print()
            print(path.relative_to(ROOT))
            print("-" * 80)

            for line_no, line in matches[:40]:
                print(f"{line_no}: {line[:350]}")

print()
print("=" * 80)
print("DONE")
print("=" * 80)