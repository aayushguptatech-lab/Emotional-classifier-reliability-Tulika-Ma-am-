from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

V2 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v2_rebuilt.csv"
V4 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4.csv"

v2 = pd.read_csv(V2).fillna("")
v4 = pd.read_csv(V4).fillna("")

merged = v2.merge(
    v4[["turn_id", "speaker"]],
    on="turn_id",
    suffixes=("_v2", "_v4")
)

same = merged["speaker_v2"] == merged["speaker_v4"]

print("=" * 70)
print("VOF — V2 REBUILT VS HISTORICAL V4 SPEAKERS")
print("=" * 70)

print(f"Rows compared: {len(merged):,}")
print(f"Speaker matches: {same.sum():,}")
print(f"Speaker differences: {(~same).sum():,}")
print(f"Speaker match rate: {same.mean() * 100:.2f}%")

if (~same).sum():
    print()
    print("First differences:")
    print(merged.loc[~same, [
        "turn_id",
        "speaker_v2",
        "speaker_v4"
    ]].head(30).to_string(index=False))

print("=" * 70)