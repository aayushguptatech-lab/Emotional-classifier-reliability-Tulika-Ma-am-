from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]

V1 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue.csv"
V4 = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v4.csv"
OUT = ROOT / "data" / "extracted" / "english" / "the_valley_of_fear_dialogue_v2_rebuilt.csv"

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

    while i < len(v1):
        parts.append(v1.iloc[i]["dialogue_text"])
        i += 1

        current = norm(" ".join(parts))

        if current == target_text:
            break

        if not target_text.startswith(current):
            break

    dialogue = " ".join(parts)

    if norm(dialogue) != target_text:
        raise ValueError(f"Could not reconstruct turn {target['turn_id']}")

    source_rows = v1.iloc[start:i]

    speakers = source_rows["speaker"].astype(str).tolist()
    known = [s for s in speakers if s and s != "Unknown"]

    speaker = known[0] if known else "Unknown"

    unit_type = (
        "speaker_attributed_dialogue"
        if speaker != "Unknown"
        else "dialogue_candidate"
    )

    rows.append({
        "text_id": target["text_id"],
        "turn_id": target["turn_id"],
        "speaker": speaker,
        "dialogue_text": dialogue,
        "unit_type": unit_type,
        "extraction_confidence": target["extraction_confidence"],
        "source": target["source"]
    })

result = pd.DataFrame(rows)
result.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 70)
print("VOF — REBUILD DIALOGUE V2")
print("=" * 70)
print(f"V1 rows: {len(v1):,}")
print(f"V2 rows: {len(result):,}")
print(f"Known speakers: {(result['speaker'] != 'Unknown').sum():,}")
print(f"Unknown speakers: {(result['speaker'] == 'Unknown').sum():,}")
print(f"Created: {OUT}")
print("=" * 70)