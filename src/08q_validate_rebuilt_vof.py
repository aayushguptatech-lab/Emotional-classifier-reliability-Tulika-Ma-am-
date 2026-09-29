from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"

pairs = {
    "V4": (
        DATA / "the_valley_of_fear_dialogue_v4.csv",
        DATA / "the_valley_of_fear_dialogue_v4_rebuilt.csv",
    ),
    "V5": (
        DATA / "the_valley_of_fear_dialogue_v5.csv",
        DATA / "the_valley_of_fear_dialogue_v5_rebuilt.csv",
    ),
    "V6": (
        DATA / "the_valley_of_fear_dialogue_v6.csv",
        DATA / "the_valley_of_fear_dialogue_v6_rebuilt.csv",
    ),
}

print("=" * 80)
print("VOF — HISTORICAL VS REBUILT VALIDATION")
print("=" * 80)

for name, (old_path, new_path) in pairs.items():
    old = pd.read_csv(old_path).fillna("")
    new = pd.read_csv(new_path).fillna("")

    print()
    print(name)
    print("-" * 80)
    print(f"Historical rows: {len(old):,}")
    print(f"Rebuilt rows:    {len(new):,}")

    if len(old) != len(new):
        print("ROW COUNT: FAIL")
        continue

    cols = ["turn_id", "speaker", "dialogue_text", "unit_type"]

    for col in cols:
        same = old[col].astype(str).tolist() == new[col].astype(str).tolist()
        print(f"{col}: {'PASS' if same else 'FAIL'}")

        if not same:
            diff = old[col].astype(str) != new[col].astype(str)
            print(f"  Differences: {diff.sum():,}")

            if col == "speaker":
                print(
                    pd.DataFrame({
                        "turn_id": old.loc[diff, "turn_id"],
                        "historical": old.loc[diff, col],
                        "rebuilt": new.loc[diff, col],
                    }).head(20).to_string(index=False)
                )

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

for name, (old_path, new_path) in pairs.items():
    old = pd.read_csv(old_path).fillna("")
    new = pd.read_csv(new_path).fillna("")

    checks = {
        "rows": len(old) == len(new),
        "turn_id": old["turn_id"].astype(str).tolist()
        == new["turn_id"].astype(str).tolist(),
        "speaker": old["speaker"].astype(str).tolist()
        == new["speaker"].astype(str).tolist(),
        "dialogue": old["dialogue_text"].astype(str).tolist()
        == new["dialogue_text"].astype(str).tolist(),
        "unit_type": old["unit_type"].astype(str).tolist()
        == new["unit_type"].astype(str).tolist(),
    }

    print(
        f"{name}: "
        + ("PASS" if all(checks.values()) else "DIFFERENCES REMAIN")
    )

print("=" * 80)