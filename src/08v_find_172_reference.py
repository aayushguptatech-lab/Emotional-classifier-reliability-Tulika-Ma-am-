from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

terms = [
    "172 turns",
    "172 turn",
    "172",
]

extensions = {
    ".py", ".txt", ".md", ".csv", ".json",
    ".xlsx", ".docx", ".pdf"
}

print("=" * 80)
print("SEARCHING PROJECT FOR THE 172-TURN REFERENCE")
print("=" * 80)

hits = []

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    if path.suffix.lower() not in extensions:
        continue
    if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
        continue

    try:
        if path.suffix.lower() in {".xlsx", ".docx", ".pdf"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"\b172\b", line, re.IGNORECASE):
            hits.append((path.relative_to(ROOT), i, line.strip()))

if not hits:
    print("\nNo textual reference to 172 found in the project.")
else:
    print(f"\nFound {len(hits)} matching lines:\n")

    for path, line_no, line in hits:
        print(f"{path}:{line_no}")
        print(f"  {line[:300]}")
        print()

print("=" * 80)