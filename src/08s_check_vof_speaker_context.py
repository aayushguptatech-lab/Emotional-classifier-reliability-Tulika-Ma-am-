from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"
CLEAN = ROOT / "data" / "cleaned" / "english" / "the_valley_of_fear_clean.txt"

ids = ["VOF_T00431", "VOF_T00433"]

v6 = pd.read_csv(DATA / "the_valley_of_fear_dialogue_v6.csv").fillna("")
text = CLEAN.read_text(encoding="utf-8")

for tid in ids:
    row = v6[v6["turn_id"] == tid].iloc[0]
    dialogue = str(row["dialogue_text"])

    pos = text.lower().find(dialogue.lower().replace(" ", ""))
    if pos == -1:
        pos = text.lower().find(dialogue.lower())

    print("=" * 80)
    print(tid)
    print("Historical speaker:", row["speaker"])
    print("Dialogue:", dialogue)

    if pos == -1:
        print("SOURCE CONTEXT: NOT FOUND")
        continue

    start = max(0, pos - 500)
    end = min(len(text), pos + len(dialogue) + 500)

    print("\nSOURCE CONTEXT:\n")
    print(text[start:end])