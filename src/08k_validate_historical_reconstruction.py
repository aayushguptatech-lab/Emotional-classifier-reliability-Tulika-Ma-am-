from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

OLD = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4.csv"
NEW = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4_rebuilt.csv"

old = pd.read_csv(OLD).fillna("")
new = pd.read_csv(NEW).fillna("")

checks = {
    "row_count": len(old) == len(new),
    "dialogue": old["dialogue_text"].astype(str).tolist() == new["dialogue_text"].astype(str).tolist(),
    "speaker": old["speaker"].astype(str).tolist() == new["speaker"].astype(str).tolist(),
    "unit_type": old["unit_type"].astype(str).tolist() == new["unit_type"].astype(str).tolist(),
    "turn_id": old["turn_id"].astype(str).tolist() == new["turn_id"].astype(str).tolist(),
}

print("=" * 70)
print("VOF — HISTORICAL RECONSTRUCTION VALIDATION")
print("=" * 70)

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")

print()
print(f"Historical rows: {len(old):,}")
print(f"Rebuilt rows:    {len(new):,}")
print()
print(f"Overall: {'PASS' if all(checks.values()) else 'FAIL'}")
print("=" * 70)