from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DATA = ROOT / "data" / "extracted" / "english"

checks = [
    ("07", "07_extract_dialogue_english.py",
     "the_valley_of_fear_dialogue.csv"),

    ("08", "08_reconstruct_dialogue_turns_english.py",
     "the_valley_of_fear_dialogue_v3.csv"),

    ("09", "09_recover_speakers_english.py",
     "the_valley_of_fear_dialogue_v4.csv"),

    ("12", "12_normalize_speakers.py",
     "the_valley_of_fear_dialogue_v5.csv"),

    ("19", "19_apply_internal_boundary_repairs.py",
     "the_valley_of_fear_dialogue_v6.csv"),
]

print("=" * 80)
print("VOF — REPRODUCIBLE PIPELINE CHECK")
print("=" * 80)

for number, script_name, output_name in checks:
    script = SRC / script_name
    output = DATA / output_name

    print()
    print(f"STEP {number}")
    print("-" * 80)
    print(f"Script : {script_name}")
    print(f"Exists : {script.exists()}")
    print(f"Output : {output_name}")
    print(f"Exists : {output.exists()}")

    if script.exists():
        text = script.read_text(encoding="utf-8", errors="ignore")

        writes_output = output_name in text
        reads_v2 = "dialogue_v2.csv" in text
        reads_v4 = "dialogue_v4.csv" in text
        reads_v5 = "dialogue_v5.csv" in text

        print(f"Writes expected output : {writes_output}")
        print(f"Reads V2              : {reads_v2}")
        print(f"Reads V4              : {reads_v4}")
        print(f"Reads V5              : {reads_v5}")

print()
print("=" * 80)
print("MISSING / ORPHANED INTERMEDIATES")
print("=" * 80)

for name in [
    "the_valley_of_fear_dialogue.csv",
    "the_valley_of_fear_dialogue_v2.csv",
    "the_valley_of_fear_dialogue_v2_rebuilt.csv",
    "the_valley_of_fear_dialogue_v3.csv",
    "the_valley_of_fear_dialogue_v4.csv",
    "the_valley_of_fear_dialogue_v5.csv",
    "the_valley_of_fear_dialogue_v6.csv",
]:
    path = DATA / name
    print(f"{name}: {'EXISTS' if path.exists() else 'MISSING'}")

print()
print("=" * 80)
print("CHECK COMPLETE")
print("=" * 80)