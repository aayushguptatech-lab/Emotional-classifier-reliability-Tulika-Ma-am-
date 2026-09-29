from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"

files = {
    "V4_hist": DATA / "the_valley_of_fear_dialogue_v4.csv",
    "V4_new": DATA / "the_valley_of_fear_dialogue_v4_rebuilt.csv",
    "V5_hist": DATA / "the_valley_of_fear_dialogue_v5.csv",
    "V5_new": DATA / "the_valley_of_fear_dialogue_v5_rebuilt.csv",
    "V6_hist": DATA / "the_valley_of_fear_dialogue_v6.csv",
    "V6_new": DATA / "the_valley_of_fear_dialogue_v6_rebuilt.csv",
}

dfs = {k: pd.read_csv(v).fillna("") for k, v in files.items()}

print("=" * 80)
print("VOF REMAINING DIFFERENCES")
print("=" * 80)

for stage in ["V4", "V5", "V6"]:
    old = dfs[f"{stage}_hist"]
    new = dfs[f"{stage}_new"]

    print()
    print(stage)
    print("-" * 80)

    for col in ["speaker", "unit_type"]:
        mask = old[col].astype(str) != new[col].astype(str)
        diff = old.loc[mask, ["turn_id", "speaker", "unit_type", "dialogue_text"]].copy()
        diff["rebuilt_speaker"] = new.loc[mask, "speaker"].values
        diff["rebuilt_unit_type"] = new.loc[mask, "unit_type"].values

        print(f"{col} differences: {len(diff)}")

        if len(diff):
            print(
                diff[
                    [
                        "turn_id",
                        "speaker",
                        "rebuilt_speaker",
                        "unit_type",
                        "rebuilt_unit_type",
                        "dialogue_text",
                    ]
                ].to_string(index=False)
            )

print()
print("=" * 80)
print("V6 SPECIAL SPLIT CHECK")
print("=" * 80)

for tid in ["VOF_T00431", "VOF_T00433", "VOF_T00557",
            "VOF_T00751", "VOF_T00766", "VOF_T00907",
            "VOF_T01202", "VOF_T01237"]:
    old = dfs["V6_hist"]
    new = dfs["V6_new"]

    a = old[old["turn_id"] == tid]
    b = new[new["turn_id"] == tid]

    print()
    print(tid)

    if len(a):
        print("HISTORICAL:")
        print(a[["turn_id", "speaker", "unit_type", "dialogue_text"]].to_string(index=False))

    if len(b):
        print("REBUILT:")
        print(b[["turn_id", "speaker", "unit_type", "dialogue_text"]].to_string(index=False))

print()
print("=" * 80)