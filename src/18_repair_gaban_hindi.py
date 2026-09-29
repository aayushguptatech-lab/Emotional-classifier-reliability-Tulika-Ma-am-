from pathlib import Path
import pandas as pd
import re

INPUT = Path("data/final/hindi/gaban_dialogue_final.csv")
OUTPUT = Path("data/final/hindi/gaban_dialogue_final_v9.csv")
REVIEW = Path("data/final/hindi/gaban_dialogue_review_v9.csv")
VALIDATION = Path("data/final/hindi/gaban_final_v9_validation.txt")

df = pd.read_csv(INPUT)

ATTR = r"(?:ने\s+)?(?:कहा|बोला|बोली|बोले|पूछा|बताया|उत्तर दिया|जवाब दिया|चिल्लाया|पुकारा|कहकर कहा|मुस्कराकर कहा|हंसकर कहा)"

EXPLICIT = re.compile(
    rf"(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n—–-]{{1,60}}?)"
    rf"\s+{ATTR}\s*[,:\-–—]\s*"
    rf"['\"'‘“]?(?P<speech>.+?)['\"'’”]?$"
)

DIRECT = re.compile(
    r"^\s*(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n—–-]{1,50}?)"
    r"\s*[-–—]\s*['\"'‘“](?P<speech>.+?)['\"'’”]?\s*$"
)

NAMES = {
    "जालपा","रमानाथ","रमा","देवीदीन","रतन","दारोग़ा","दारोगा",
    "रमेश","दयानाथ","जागेश्वरी","ज़ोहरा","जोहरा","जग्गो",
    "मणिभूषण","डिप्टी","गंगू","इंस्पेक्टर","वकील साहब","जौहरी",
    "शहजादी","दीनदयाल","चरनदास","चपरासी","बुढिया","महराज",
    "रमेश बाबू","टीमल","मानकी"
}

BAD = {
    "से","में","पर","और","या","तो","ही","भी","हुए","हुआ","हुई",
    "होकर","जाकर","आकर","लेकर","देकर","करके","देखकर","सुनकर",
    "उसने","उसका","उसकी","उसके","मैंने","तुमने","उन्होंने",
    "एक दिन","एक बार","विवश होकर"
}


def norm(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    s = s.strip(" -–—,:;।'\"‘’“”")

    if " ने " in s:
        s = s.split(" ने ")[0].strip()

    if s.endswith(" ने"):
        s = s[:-3].strip()

    return s


def valid_name(s):
    s = norm(s)

    if not s or s in BAD:
        return False

    if s in NAMES:
        return True

    if len(s.split()) > 4:
        return False

    if any(x in s for x in [
        "करके","होकर","जाकर","आकर","लेकर",
        "देकर","देखकर","सुनकर"
    ]):
        return False

    return True


def extract(row):
    source = str(row["source_text"]).strip()
    old_speaker = str(row["speaker"]).strip()
    dialogue = str(row["dialogue"]).strip()

    m = EXPLICIT.search(source)

    if m:
        speaker = norm(m.group("speaker"))
        if valid_name(speaker):
            speech = m.group("speech").strip()
            return speaker, speech, "explicit_attribution"

    m = DIRECT.match(source)

    if m:
        speaker = norm(m.group("speaker"))
        if valid_name(speaker):
            return speaker, m.group("speech").strip(), "direct_named"

    old = norm(old_speaker)

    if old in NAMES:
        return old, dialogue, "validated_existing_name"

    return "Unknown", dialogue, "unknown"


rows = []

for _, row in df.iterrows():
    speaker, dialogue, method = extract(row)

    rows.append({
        "chapter": row["chapter"],
        "paragraph_no": row["paragraph_no"],
        "speaker": speaker,
        "dialogue": dialogue,
        "source_text": row["source_text"],
        "method": method
    })

out = pd.DataFrame(rows)

out["dialogue"] = (
    out["dialogue"]
    .astype(str)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

out = out[out["dialogue"].str.len() >= 5].copy()

out = out.drop_duplicates(
    subset=["chapter","paragraph_no","speaker","dialogue"]
).reset_index(drop=True)

out.insert(
    0,
    "id",
    [f"GABAN_V9_T{i:05d}" for i in range(1, len(out)+1)]
)

review_mask = (
    out["speaker"].eq("Unknown")
    | out["dialogue"].str.len().gt(1200)
    | out["dialogue"].str.count(r"\bकहा\b").gt(1)
    | out["dialogue"].str.count(r"\bबोला\b").gt(1)
    | out["dialogue"].str.count(r"\bबोली\b").gt(1)
    | out["dialogue"].str.count(r"\bपूछा\b").gt(1)
)

final = out[~review_mask].copy()
review = out[review_mask].copy()

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

validation = [
    "GABAN V9 STRUCTURAL REPAIR",
    "=" * 50,
    f"Input rows: {len(df)}",
    f"Candidate rows: {len(out)}",
    f"Final rows: {len(final)}",
    f"Review rows: {len(review)}",
    "",
    f"Known speakers: {known}",
    f"Unknown speakers: {unknown}",
    f"Unknown percentage: {(unknown/len(final)*100):.2f}%"
    if len(final) else "Unknown percentage: 0.00%",
    "",
    "CHAPTER DISTRIBUTION"
]

for ch in range(1,6):
    validation.append(
        f"Chapter {ch}: {(final.chapter == ch).sum()}"
    )

validation += [
    "",
    "EXTRACTION METHODS",
]

for k,v in out["method"].value_counts().items():
    validation.append(f"{k}: {v}")

validation += [
    "",
    "STRUCTURAL CHECKS",
    f"Unique IDs: {final.id.is_unique}",
    f"Empty dialogue: {final.dialogue.str.strip().eq('').sum()}",
    f"Duplicate dialogue: {final.duplicated('dialogue').sum()}",
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
print(final.speaker.value_counts().head(30).to_string())
print()
print("REVIEW SAMPLE")
print(
    review[
        ["id","chapter","speaker","method","dialogue"]
    ].head(40).to_string(index=False)
)