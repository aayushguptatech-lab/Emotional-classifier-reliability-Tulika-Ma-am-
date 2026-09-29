from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

OLD = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4.csv"
NEW = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v2_rebuilt.csv"

old = pd.read_csv(OLD).fillna("")
new = pd.read_csv(NEW).fillna("")

print("=" * 70)
print("VOF — V2 REBUILD VALIDATION")
print("=" * 70)

print(f"V4 rows: {len(old):,}")
print(f"V2 rebuilt rows: {len(new):,}")

print()
print("Dialogue coverage:")
print(f"V2 dialogue rows: {len(new):,}")
print(f"V4 dialogue rows: {len(old):,}")

print()
print("Speaker distribution:")
print(f"V2 known: {(new['speaker'] != 'Unknown').sum():,}")
print(f"V2 unknown: {(new['speaker'] == 'Unknown').sum():,}")

print()
print("Required historical counts:")
print("Rows == 1266:", len(new) == 1266)
print("Known == 299:", (new["speaker"] != "Unknown").sum() == 299)
print("Unknown == 967:", (new["speaker"] == "Unknown").sum() == 967)

print()
print("Turn IDs sequential:", list(new["turn_id"]) == list(old["turn_id"]))

print("=" * 70)