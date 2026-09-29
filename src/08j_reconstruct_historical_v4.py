from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]

V1 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue.csv"
V4 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4.csv"
OUT = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4_rebuilt.csv"

v1 = pd.read_csv(V1).fillna("")
v4 = pd.read_csv(V4).fillna("")

def norm(text):
    return re.sub(r"\s+", " ", str(text)).strip()

v1["dialogue_norm"] = v1["dialogue_text"].map(norm)
v4["dialogue_norm"] = v4["dialogue_text"].map(norm)

rows = []
i = 0

for _, target in v4.iterrows():
    target_text = target["dialogue_norm"]
    parts = []
    start = i

    while i < len(v1) and len(norm(" ".join(parts))) < len(target_text):
        parts.append(v1.iloc[i]["dialogue_text"])
        i += 1

        current = norm(" ".join(parts))

        if current == target_text:
            break

        if target_text.startswith(current):
            continue

        combined = norm(" ".join(parts))
        if target_text.startswith(combined):
            continue

        break

    if norm(" ".join(parts)) != target_text:
        matches = v1.index[v1["dialogue_norm"] == target_text].tolist()

        if matches:
            idx = matches[0]
            start = idx
            i = idx + 1
            parts = [v1.iloc[idx]["dialogue_text"]]

    row = target.to_dict()
    row["historical_v1_start"] = start + 1
    row["historical_v1_end"] = i
    row["reconstructed_from_v1"] = norm(" ".join(parts)) == target_text
    rows.append(row)

result = pd.DataFrame(rows)
result.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 70)
print("VOF — HISTORICAL V4 RECONSTRUCTION")
print("=" * 70)
print(f"V1 rows: {len(v1):,}")
print(f"Historical V4 rows: {len(v4):,}")
print(f"Rebuilt rows: {len(result):,}")
print(f"Exact reconstructions: {result['reconstructed_from_v1'].sum():,}")
print(f"Failed reconstructions: {(~result['reconstructed_from_v1']).sum():,}")
print()
print(f"Created: {OUT}")
print("=" * 70)