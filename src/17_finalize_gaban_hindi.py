from pathlib import Path
import pandas as pd
import re

INPUT = Path("data/final/hindi/gaban_dialogue_final.csv")
REVIEW = Path("data/final/hindi/gaban_dialogue_review.csv")
OUTPUT = Path("data/final/hindi/gaban_dialogue_final_v8.csv")
VALIDATION = Path("data/final/hindi/gaban_final_v8_validation.txt")

df = pd.read_csv(INPUT)

BAD = {
    "से", "में", "पर", "और", "या", "तो", "ही", "भी",
    "हुए", "हुआ", "हुई", "होकर", "जाकर", "आकर", "लेकर",
    "देकर", "करके", "देखकर", "सुनकर", "उसने", "उसका",
    "उसकी", "उसके", "मैंने", "तुमने", "उन्होंने"
}

PRONOUNS = {
    "उसने", "उसका", "उसकी", "उसके", "मैंने", "तुमने",
    "उन्होंने", "उन्होंने", "उसको", "उसे", "जिसने"
}

def clean_speaker(s):
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)

    if not s:
        return "Unknown"

    if s in BAD or s in PRONOUNS:
        return "Unknown"

    if " ने " in s:
        s = s.split(" ने ")[0].strip()

    elif s.endswith(" ने"):
        s = s[:-3].strip()

    s = re.sub(
        r"^(एक दिन|एक बार|फिर|तब|लेकिन|मगर|इस पर|इसपर|और)\s+",
        "",
        s
    ).strip()

    if not s:
        return "Unknown"

    if s in BAD or s in PRONOUNS:
        return "Unknown"

    if len(s.split()) > 5:
        return "Unknown"

    if any(x in s for x in [
        "करके", "होकर", "जाकर", "आकर", "लेकर",
        "देकर", "देखकर", "सुनकर", "से", "में"
    ]):
        return "Unknown"

    return s


df["speaker_before"] = df["speaker"].astype(str)
df["speaker"] = df["speaker"].map(clean_speaker)

df["dialogue"] = (
    df["dialogue"]
    .astype(str)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df = df[df["dialogue"].str.len() >= 5].copy()

df = df.drop_duplicates(
    subset=["chapter", "paragraph_no", "speaker", "dialogue"]
).reset_index(drop=True)

df.insert(
    0,
    "new_id",
    [f"GABAN_V8_T{i:05d}" for i in range(1, len(df) + 1)]
)

review_mask = (
    df["speaker"].eq("Unknown")
    | df["dialogue"].str.len().gt(1800)
)

review = df[review_mask].copy()
final = df[~review_mask].copy()

final = final.drop(columns=["speaker_before"])
review = review.drop(columns=["speaker_before"])

final.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

review.to_csv(
    REVIEW,
    index=False,
    encoding="utf-8-sig"
)

known = final["speaker"].ne("Unknown").sum()
unknown = len(final) - known

chapter_counts = final["chapter"].value_counts().sort_index()

validation = [
    "GABAN V8 FINALIZATION AUDIT",
    "=" * 50,
    f"Input rows: {len(df)}",
    f"Final rows: {len(final)}",
    f"Review rows: {len(review)}",
    "",
    f"Known speakers: {known}",
    f"Unknown speakers: {unknown}",
    f"Unknown percentage: {(unknown / len(final) * 100):.2f}%"
    if len(final) else "Unknown percentage: 0.00%",
    "",
    "CHAPTER DISTRIBUTION"
]

for ch in range(1, 6):
    validation.append(
        f"Chapter {ch}: {chapter_counts.get(ch, 0)}"
    )

validation += [
    "",
    "STRUCTURAL CHECKS",
    f"Unique IDs: {final['new_id'].is_unique}",
    f"Empty dialogue: {final['dialogue'].str.strip().eq('').sum()}",
    f"Duplicate dialogue: {final.duplicated('dialogue').sum()}",
    "",
    "SPEAKER CHECK",
    f"Distinct speakers: {final['speaker'].nunique()}",
    "",
    "OUTPUTS",
    str(OUTPUT),
    str(REVIEW)
]

VALIDATION.write_text(
    "\n".join(validation),
    encoding="utf-8"
)

print()
print("\n".join(validation))
print()
print("TOP SPEAKERS")
print(final["speaker"].value_counts().head(25).to_string())
print()
print("REVIEW SAMPLE")
print(
    review[
        ["new_id", "chapter", "speaker", "dialogue"]
    ].head(30).to_string(index=False)
)