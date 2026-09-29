from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"

files = {
    "V1": DATA / "the_valley_of_fear_dialogue.csv",
    "V4": DATA / "the_valley_of_fear_dialogue_v4.csv",
    "V5": DATA / "the_valley_of_fear_dialogue_v5.csv",
    "V6": DATA / "the_valley_of_fear_dialogue_v6.csv",
}

print("=" * 80)
print("VOF CORPUS SIZE ANALYSIS")
print("=" * 80)

for name, path in files.items():
    df = pd.read_csv(path).fillna("")

    print()
    print(name)
    print("-" * 80)
    print(f"Rows: {len(df):,}")
    print(f"Known speakers: {(df['speaker'] != 'Unknown').sum():,}")
    print(f"Unknown speakers: {(df['speaker'] == 'Unknown').sum():,}")

    print("\nUnit types:")
    print(df["unit_type"].value_counts().to_string())

    print("\nDialogue length:")
    print(f"Total characters: {df['dialogue_text'].astype(str).str.len().sum():,}")
    print(f"Median characters: {df['dialogue_text'].astype(str).str.len().median():.1f}")
    print(f"Mean characters: {df['dialogue_text'].astype(str).str.len().mean():.1f}")

print()
print("=" * 80)
print("POSSIBLE TURN-COLLAPSING ANALYSIS")
print("=" * 80)

df = pd.read_csv(files["V6"]).fillna("")

text = df["dialogue_text"].astype(str)

print(f"Current V6 turns: {len(df):,}")
print(f"Turns >= 500 chars: {(text.str.len() >= 500).sum():,}")
print(f"Turns >= 1000 chars: {(text.str.len() >= 1000).sum():,}")
print(f"Turns >= 2000 chars: {(text.str.len() >= 2000).sum():,}")

print("\nSpeaker distribution:")
print(df["speaker"].value_counts().head(25).to_string())

print()
print("=" * 80)
print("NOTE")
print("=" * 80)
print(
    "This script does not assume why the workshop corpus had 172 turns. "
    "It only measures the current corpus so the difference can be explained "
    "from evidence rather than guessed."
)
