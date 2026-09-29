import pandas as pd
from pathlib import Path

p = Path("data/final/hindi/gaban_dialogue_final.csv")
df = pd.read_csv(p)

print("\nGABAN — QUICK QUALITY CHECK")
print("=" * 55)

print("\nBY CHAPTER")
print(df.groupby("chapter").size().to_string())

print("\nBY FLAG")
print(df["flag"].value_counts().to_string())

print("\nSPEAKERS")
print(df["speaker"].value_counts().head(20).to_string())

print("\nSHORTEST 20")
print(
    df.nsmallest(20, "dialogue_len")
    [["id","chapter","speaker","dialogue","dialogue_len"]]
    .to_string(index=False)
)

print("\nLONGEST 10")
print(
    df.nlargest(10, "dialogue_len")
    [["id","chapter","speaker","dialogue","dialogue_len"]]
    .to_string(index=False)
)

print("\nUNKNOWN SAMPLE")
print(
    df[df["speaker"] == "Unknown"]
    .head(15)
    [["id","chapter","dialogue","dialogue_len"]]
    .to_string(index=False)
)