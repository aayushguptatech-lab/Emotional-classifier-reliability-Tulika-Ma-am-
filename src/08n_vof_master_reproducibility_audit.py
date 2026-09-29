from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"

files = {
    "V1": DATA / "the_valley_of_fear_dialogue.csv",
    "V2": DATA / "the_valley_of_fear_dialogue_v2_rebuilt.csv",
    "V4": DATA / "the_valley_of_fear_dialogue_v4.csv",
    "V5": DATA / "the_valley_of_fear_dialogue_v5.csv",
    "V6": DATA / "the_valley_of_fear_dialogue_v6.csv",
}

dfs = {k: pd.read_csv(v).fillna("") for k, v in files.items()}

print("=" * 80)
print("VOF — MASTER REPRODUCIBILITY AUDIT")
print("=" * 80)

for name, df in dfs.items():
    print(f"{name}: {len(df):,} rows")

print()
print("SPEAKER COUNTS")
print("-" * 80)

for name in ["V2", "V4", "V5", "V6"]:
    df = dfs[name]
    known = (df["speaker"] != "Unknown").sum()
    unknown = (df["speaker"] == "Unknown").sum()
    print(f"{name}: known={known:,} | unknown={unknown:,}")

print()
print("V2 → V4")
print("-" * 80)

v2 = dfs["V2"]
v4 = dfs["V4"]

m = v2[["turn_id", "speaker", "dialogue_text"]].merge(
    v4[["turn_id", "speaker", "dialogue_text"]],
    on="turn_id",
    suffixes=("_v2", "_v4")
)

speaker_same = m["speaker_v2"] == m["speaker_v4"]
dialogue_same = m["dialogue_text_v2"].map(
    lambda x: re.sub(r"\s+", " ", str(x)).strip()
) == m["dialogue_text_v4"].map(
    lambda x: re.sub(r"\s+", " ", str(x)).strip()
)

print(f"Rows compared: {len(m):,}")
print(f"Speaker same: {speaker_same.sum():,}")
print(f"Speaker different: {(~speaker_same).sum():,}")
print(f"Dialogue same after whitespace normalization: {dialogue_same.sum():,}")

print()
print("V4 → V5")
print("-" * 80)

v5 = dfs["V5"]

m45 = v4[["turn_id", "speaker"]].merge(
    v5[["turn_id", "speaker"]],
    on="turn_id",
    suffixes=("_v4", "_v5")
)

same45 = m45["speaker_v4"] == m45["speaker_v5"]

print(f"Rows compared: {len(m45):,}")
print(f"Speaker same: {same45.sum():,}")
print(f"Speaker changed: {(~same45).sum():,}")

print()
print("V5 → V6")
print("-" * 80)

v6 = dfs["V6"]

m56 = v5[["turn_id", "speaker", "dialogue_text"]].merge(
    v6[["turn_id", "speaker", "dialogue_text"]],
    on="turn_id",
    suffixes=("_v5", "_v6")
)

same56 = (
    m56["speaker_v5"] == m56["speaker_v6"]
)

print(f"Rows compared: {len(m56):,}")
print(f"Speaker same: {same56.sum():,}")
print(f"Speaker changed: {(~same56).sum():,}")

print()
print("V6 STRUCTURE")
print("-" * 80)

print(f"V6 rows: {len(v6):,}")
print(f"Unique turn IDs: {v6['turn_id'].nunique():,}")
print(f"Duplicate turn IDs: {v6['turn_id'].duplicated().sum():,}")

print()
print("DIALOGUE LENGTHS")
print("-" * 80)

for name in ["V2", "V4", "V5", "V6"]:
    df = dfs[name]
    lengths = df["dialogue_text"].astype(str).str.len()
    print(
        f"{name}: min={lengths.min():,} | "
        f"median={lengths.median():,.0f} | "
        f"max={lengths.max():,}"
    )

print()
print("LONG RECORDS")
print("-" * 80)

for name in ["V2", "V4", "V5", "V6"]:
    df = dfs[name].copy()
    df["length"] = df["dialogue_text"].astype(str).str.len()
    print(f"{name} >1000 chars: {(df['length'] > 1000).sum():,}")

print()
print("HISTORICAL TARGETS")
print("-" * 80)

checks = {
    "V2 rows == 1266": len(v2) == 1266,
    "V2 known == 299": (v2["speaker"] != "Unknown").sum() == 299,
    "V2 unknown == 967": (v2["speaker"] == "Unknown").sum() == 967,
    "V4 rows == 1266": len(v4) == 1266,
    "V5 rows == 1266": len(v5) == 1266,
    "V6 rows == 1267": len(v6) == 1267,
}

for label, result in checks.items():
    print(f"{label}: {'PASS' if result else 'FAIL'}")

print()
print("SAMPLE V2 → V4 DIFFERENCES")
print("-" * 80)

diff = m.loc[~speaker_same, [
    "turn_id",
    "speaker_v2",
    "speaker_v4"
]].head(50)

if len(diff):
    print(diff.to_string(index=False))
else:
    print("None")

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)