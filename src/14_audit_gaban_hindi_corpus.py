import pandas as pd
from pathlib import Path

INPUT = Path("data/final/hindi/gaban_dialogue_candidates.csv")
SOURCE = Path("data/cleaned/hindi/gaban_clean.txt")
FINAL = Path("data/final/hindi/gaban_dialogue_final.csv")
AUDIT = Path("data/final/hindi/gaban_final_validation.txt")
REVIEW = Path("data/final/hindi/gaban_dialogue_review.csv")

df = pd.read_csv(INPUT)
source = SOURCE.read_text(encoding="utf-8")

df["dialogue_text"] = df["dialogue_text"].fillna("").astype(str)
df["speaker"] = df["speaker"].fillna("Unknown").astype(str)
df["dialogue_len"] = df["dialogue_text"].str.len()
df["word_count"] = df["dialogue_text"].str.split().str.len()

def unknown(x):
    return not x.strip() or x.strip().lower() == "unknown"

df["speaker_unknown"] = df["speaker"].apply(unknown)
df["flag"] = ""

df.loc[df["dialogue_len"] < 3, "flag"] = "very_short"
df.loc[df["dialogue_len"] > 1000, "flag"] = "very_long"
df.loc[
    (df["dialogue_len"] > 500) & (df["flag"] == ""),
    "flag"
] = "long_candidate"

narrative_pattern = (
    r"[।]\s+[अ-हक़-य़]{2,}\s+"
    r"(?:ने|बोला|बोली|कहा|कही|पूछा|उत्तर दिया|जवाब दिया|"
    r"चिल्लाया|चिल्लाई|समझाया|बताया)\s+"
)

mask = (
    df["dialogue_text"].str.contains(
        narrative_pattern,
        regex=True,
        na=False
    )
    & (df["dialogue_len"] > 300)
    & (df["flag"] == "")
)

df.loc[mask, "flag"] = "possible_narrative_span"

mask = (
    (df["dialogue_text"].str.count("।") > 20)
    & (df["flag"] == "")
)

df.loc[mask, "flag"] = "narrative_heavy"

df["review_required"] = (
    df["speaker_unknown"] | df["flag"].ne("")
)

review = df[df["review_required"]].copy()
review.to_csv(REVIEW, index=False, encoding="utf-8-sig")

final = df[
    (~df["dialogue_text"].str.strip().eq("")) &
    (~df["flag"].isin([
        "narrative_heavy",
        "possible_narrative_span"
    ]))
].copy()

final = final.reset_index(drop=True)
final["turn_id"] = [
    f"GABAN_T{i:05d}" for i in range(1, len(final) + 1)
]

required = [
    "turn_id",
    "chapter",
    "speaker",
    "speaker_evidence",
    "dialogue_text",
    "start_char",
    "end_char",
    "source",
    "source_url"
]

final = final[required]
final.to_csv(FINAL, index=False, encoding="utf-8-sig")

known = (~final["speaker"].apply(unknown)).sum()
unknown_count = final["speaker"].apply(unknown).sum()

counts = {
    "very_short": (df["flag"] == "very_short").sum(),
    "long_candidate": (df["flag"] == "long_candidate").sum(),
    "very_long": (df["flag"] == "very_long").sum(),
    "possible_narrative_span": (df["flag"] == "possible_narrative_span").sum(),
    "narrative_heavy": (df["flag"] == "narrative_heavy").sum()
}

quote_counts = {
    "“": source.count("“"),
    "”": source.count("”"),
    "‘": source.count("‘"),
    "’": source.count("’"),
    '"': source.count('"')
}

audit = [
    "GABAN — FINAL HINDI CORPUS AUDIT",
    "=" * 50,
    "",
    f"Original candidates:       {len(df)}",
    f"Final retained turns:      {len(final)}",
    f"Review/excluded records:   {len(review)}",
    "",
    f"Known speakers:             {known}",
    f"Unknown speakers:           {unknown_count}",
    f"Unknown percentage:         {(unknown_count / len(final) * 100) if len(final) else 0:.2f}%",
    "",
    "CANDIDATE FLAGS",
    f"Very short:                 {counts['very_short']}",
    f"Long candidates:            {counts['long_candidate']}",
    f"Very long:                  {counts['very_long']}",
    f"Possible narrative spans:   {counts['possible_narrative_span']}",
    f"Narrative-heavy:            {counts['narrative_heavy']}",
    "",
    "QUOTE MARKERS IN CLEAN SOURCE"
]

for k, v in quote_counts.items():
    audit.append(f"{k}: {v}")

audit += [
    "",
    "STRUCTURAL VALIDATION",
    f"Duplicate turn IDs:         {final['turn_id'].duplicated().sum()}",
    f"Empty dialogue rows:        {final['dialogue_text'].str.strip().eq('').sum()}",
    f"Unique IDs:                 {final['turn_id'].is_unique}",
    "",
    "SOURCE",
    "HindiSamay — प्रेमचंद — गबन",
    "",
    "METHODOLOGY",
    "Strong narrative-span indicators are flagged for review.",
    "Unknown speaker identities are retained rather than guessed.",
    "",
    "OUTPUTS",
    str(FINAL),
    str(REVIEW),
    str(AUDIT)
]

AUDIT.write_text("\n".join(audit), encoding="utf-8")

print("\nGABAN — FINAL HINDI CORPUS AUDIT")
print("=" * 50)
print(f"Original candidates:       {len(df)}")
print(f"Final retained turns:      {len(final)}")
print(f"Review/excluded records:   {len(review)}")
print()
print(f"Known speakers:             {known}")
print(f"Unknown speakers:           {unknown_count}")
print(f"Unknown percentage:         {(unknown_count / len(final) * 100) if len(final) else 0:.2f}%")
print()
print("FLAGS")
for k, v in counts.items():
    print(f"{k}:".ljust(28), v)

print()
print("QUOTE MARKERS IN CLEAN SOURCE")
for k, v in quote_counts.items():
    print(f"{k}: {v}")

print()
print("VALIDATION")
print(f"Unique IDs:                 {final['turn_id'].is_unique}")
print(f"Non-empty dialogue:         {final['dialogue_text'].str.strip().ne('').all()}")

print()
print("OUTPUTS")
print(FINAL)
print(REVIEW)
print(AUDIT)