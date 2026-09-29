from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "english" / "the_valley_of_fear_raw.txt"
CLEAN = ROOT / "data" / "cleaned" / "english" / "the_valley_of_fear_clean.txt"

raw = RAW.read_text(encoding="utf-8")
clean = CLEAN.read_text(encoding="utf-8")

patterns = [
    r"\bMr\.",
    r"\bMrs\.",
    r"\bDr\.",
    r"\bSt\.",
]

print("=" * 80)
print("VOF CANONICAL TEXT AUDIT")
print("=" * 80)

print(f"Raw characters:   {len(raw):,}")
print(f"Clean characters: {len(clean):,}")

print("\nTITLE ABBREVIATION COUNTS")
print("-" * 80)

for pattern in patterns:
    name = pattern.replace(r"\b", "").replace(r"\.", ".")
    raw_count = len(re.findall(pattern, raw))
    clean_count = len(re.findall(pattern, clean))
    lower_count = len(re.findall(pattern.lower(), clean))

    print(
        f"{name:<6} raw={raw_count:<5} "
        f"clean={clean_count:<5} lowercase={lower_count:<5}"
    )

print("\nLOWERCASE TITLE FORMS")
print("-" * 80)

for term in ["mr.", "mrs.", "dr.", "st."]:
    count = len(re.findall(r"\b" + re.escape(term) + r"\b", clean))
    print(f"{term:<6} {count}")

print("\nCANONICAL CHECK")
print("-" * 80)

if any(re.search(r"\b" + re.escape(x) + r"\b", clean) for x in ["mr.", "mrs.", "dr.", "st."]):
    print("FAIL: lowercase title abbreviations exist in cleaned text.")
else:
    print("PASS: no lowercase title abbreviations detected.")

print("=" * 80)