from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "hindi" / "titli"
OUT = ROOT / "data" / "extracted" / "hindi" / "titli" / "titli_raw_source_inventory.txt"

OUT.parent.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


files = sorted(RAW_DIR.glob("*.html"))

numbered = {}
special = []

for path in files:
    m = re.fullmatch(r"titli_(\d+)\.html", path.name)
    if m:
        numbered[int(m.group(1))] = path
    else:
        special.append(path)

expected = list(range(1, 32))
missing = [n for n in expected if n not in numbered]
extra = [n for n in numbered if n not in expected]

lines = []

lines.append("TITLI (तितली) — RAW SOURCE INVENTORY AUDIT")
lines.append("")
lines.append(f"Raw directory: {RAW_DIR}")
lines.append(f"HTML files found: {len(files)}")
lines.append("")

lines.append("1. NUMBERED SOURCE FILES")
for n in sorted(numbered):
    p = numbered[n]
    lines.append(
        f"{n:02d} | {p.name} | bytes={p.stat().st_size} | sha256={sha256(p)}"
    )

lines.append("")
lines.append("2. EXPECTED NUMBERED RANGE")
lines.append("Expected: titli_01.html through titli_31.html")
lines.append(
    "Present: " + ", ".join(f"{n:02d}" for n in sorted(numbered))
)
lines.append(
    "Missing: " + (
        ", ".join(f"{n:02d}" for n in missing) if missing else "NONE"
    )
)
lines.append(
    "Extra numeric files: " + (
        ", ".join(f"{n:02d}" for n in extra) if extra else "NONE"
    )
)

lines.append("")
lines.append("3. SPECIAL / NON-NUMERICALLY STANDARD FILES")

if special:
    for p in special:
        lines.append(
            f"{p.name} | bytes={p.stat().st_size} | sha256={sha256(p)}"
        )
else:
    lines.append("NONE")

lines.append("")
lines.append("4. DUPLICATE HASH CHECK")

hash_groups = {}

for p in files:
    digest = sha256(p)
    hash_groups.setdefault(digest, []).append(p.name)

duplicate_groups = [
    names for names in hash_groups.values()
    if len(names) > 1
]

if duplicate_groups:
    for names in duplicate_groups:
        lines.append("DUPLICATE HASH GROUP:")
        for name in names:
            lines.append(f"  {name}")
else:
    lines.append("No byte-identical duplicate files detected.")

lines.append("")
lines.append("5. SOURCE DECISION")
lines.append(
    "The raw source inventory is evidence only at this stage."
)
lines.append(
    "Missing source pages must be investigated before canonical cleaning."
)
lines.append(
    "Duplicate-looking files must not be silently deleted; their identity "
    "and provenance must be documented first."
)
lines.append(
    "Special file titli_part_1.html must be inspected before inclusion."
)

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Report: {OUT}")
print(f"HTML files: {len(files)}")
print(f"Numbered files: {len(numbered)}")
print(f"Missing numbered pages: {missing}")
print(f"Special files: {[p.name for p in special]}")
print(f"Duplicate hash groups: {len(duplicate_groups)}")

