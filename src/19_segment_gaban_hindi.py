from pathlib import Path
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

RAW = Path("data/raw/hindi/gaban")
CLEAN = Path("data/cleaned/hindi/gaban_clean.txt")
OUT = Path("data/final/hindi/gaban_dialogue_segmented_v2.csv")
REV = Path("data/final/hindi/gaban_dialogue_segmented_review_v2.csv")
VAL = Path("data/final/hindi/gaban_dialogue_segmented_validation_v2.txt")

for p in [RAW, CLEAN.parent, OUT.parent]:
    p.mkdir(parents=True, exist_ok=True)

NAMES = {
    "जालपा","रमानाथ","रमा","रतन","देवीदीन","रमेश","रमेश बाबू",
    "दारोग़ा","दारोगा","दयानाथ","जागेश्वरी","ज़ोहरा","जोहरा","जग्गो",
    "मणिभूषण","डिप्टी","इंस्पेक्टर","गंगू","चपरासी","जौहरी","चरनदास",
    "दीनदयाल","प्यादा","टिकट बाबू","मानकी","टीमल","बिसाती","शहजादी"
}

BAD = {
    "मैंने","तुमने","उसने","उन्होंने","हमने","फिर","सहसा","खड़े",
    "डरते","भाव से","करके","होकर","जाकर","आकर","लेकर","देकर",
    "देखकर","सुनकर","पास जाकर","मुझे","तुम","वह","यह","और","लेकिन"
}

ATTR_WORDS = r"(?:कहा|कहता|कहती|कहते|बोला|बोली|बोले|पूछा|पूछती|पूछते|जवाब दिया|उत्तर दिया|बताया|चिल्लाया|पुकारा|कह उठा|कह उठी|कहने लगा|कहने लगी)"

def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()

def normalize_speaker(s):
    s = clean(s)
    s = re.sub(r"^(और|फिर|तब|लेकिन|मगर|सहसा)\s+", "", s)
    s = re.sub(r"\s+ने$", "", s).strip()

    if s in NAMES:
        return s

    if s in BAD:
        return "Unknown"

    for name in sorted(NAMES, key=len, reverse=True):
        if s.startswith(name + " "):
            return name

    return "Unknown"

def add(rows, chapter, pno, speaker, speech, method, source):
    speech = clean(speech).strip(" '\"‘’“”")
    if len(speech) < 8:
        return

    sp = normalize_speaker(speaker)

    rows.append({
        "chapter": chapter,
        "paragraph_no": pno,
        "speaker": sp,
        "dialogue": speech,
        "method": method,
        "source_text": source
    })

def extract_paragraph(text, chapter, pno):
    rows = []
    text = clean(text)

    # 1. Named direct speech:
    # रमानाथ-'...'
    # देवीदीन -'...'
    for m in re.finditer(
        r"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{1,45}?)"
        r"\s*[-–—]\s*"
        r"(?P<quote>['‘“][^'’”\n]+['’”])",
        text
    ):
        add(rows, chapter, pno, m.group("speaker"), m.group("quote"),
            "named_dash_quote", text)

    # 2. Explicit attribution immediately before quote:
    # रमा ने कहा, '...'
    # दारोग़ा ने पूछा-'...'
    for m in re.finditer(
        rf"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{{1,55}}?)"
        rf"\s+{ATTR_WORDS}\s*[,:\-–—]\s*"
        rf"(?P<quote>['‘“][^'’”\n]+['’”])",
        text
    ):
        add(rows, chapter, pno, m.group("speaker"), m.group("quote"),
            "attribution_quote", text)

    # 3. Hindi dialogue often has: रमा ने कहा, '...' रतन ने कहा, '...'
    # Catch additional quoted spans only when preceded by a speech verb.
    for m in re.finditer(
        rf"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{{1,55}}?)"
        rf"\s+{ATTR_WORDS}\s*[,:\-–—]\s*"
        rf"(?P<quote>['‘“][^'’”]+['’”])",
        text
    ):
        add(rows, chapter, pno, m.group("speaker"), m.group("quote"),
            "attribution_quote", text)

    # 4. Paragraph beginning with quoted speech = continuation.
    if not rows:
        m = re.match(r"^\s*['‘“](?P<quote>.+?)['’”](?:\s|$)", text)
        if m:
            add(rows, chapter, pno, "Unknown", m.group("quote"),
                "leading_quote", text)

    # 5. Do NOT treat arbitrary quotation marks as dialogue.
    return rows

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    paragraphs = []
    clean_parts = []

    for chapter in range(1, 6):
        r = session.get(BASE.format(n=chapter), timeout=30)
        r.raise_for_status()

        (RAW / f"gaban_chapter_{chapter}.html.txt").write_text(
            r.text, encoding="utf-8"
        )

        soup = BeautifulSoup(r.text, "html.parser")

        ps = []
        for p in soup.find_all("p"):
            t = clean(p.get_text(" ", strip=True))
            if len(t) >= 20:
                ps.append(t)

        clean_parts.append("\n\n".join(ps))

        for i, t in enumerate(ps, 1):
            paragraphs.append((chapter, i, t))

        print(f"Chapter {chapter}: {len(ps)} paragraphs")

    clean_source = "\n\n".join(clean_parts)
    CLEAN.write_text(clean_source, encoding="utf-8")

    rows = []

    for chapter, pno, text in paragraphs:
        rows.extend(extract_paragraph(text, chapter, pno))

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("No dialogue found.")

    df = df.drop_duplicates(
        subset=["chapter", "paragraph_no", "speaker", "dialogue"]
    ).reset_index(drop=True)

    df.insert(
        0, "id",
        [f"GABAN_V2_T{i:05d}" for i in range(1, len(df) + 1)]
    )

    review = (
        df["speaker"].eq("Unknown")
        | df["dialogue"].str.len().gt(900)
        | df["dialogue"].str.contains(
            r"कथा|उपन्यास|अध्याय|मुखपृष्ठ|विषय-सूची|कहानियाँ",
            regex=True
        )
    )

    final = df[~review].copy()
    review_df = df[review].copy()

    final.to_csv(OUT, index=False, encoding="utf-8-sig")
    review_df.to_csv(REV, index=False, encoding="utf-8-sig")

    known = final["speaker"].ne("Unknown").sum()
    unknown = final["speaker"].eq("Unknown").sum()

    lines = [
        "GABAN DIALOGUE SEGMENTATION V2",
        "=" * 55,
        f"Source paragraphs: {len(paragraphs)}",
        f"Raw segments: {len(df)}",
        f"Final segments: {len(final)}",
        f"Review segments: {len(review_df)}",
        f"Known speakers: {known}",
        f"Unknown speakers: {unknown}",
        f"Unknown percentage: {(unknown / len(final) * 100):.2f}%" if len(final) else "Unknown percentage: 0",
        "",
        "CHAPTER DISTRIBUTION"
    ]

    counts = final["chapter"].value_counts().sort_index()
    for ch in range(1, 6):
        lines.append(f"Chapter {ch}: {counts.get(ch, 0)}")

    lines += [
        "",
        "METHODS"
    ]

    for k, v in df["method"].value_counts().items():
        lines.append(f"{k}: {v}")

    lines += [
        "",
        "STRUCTURAL CHECKS",
        f"Unique IDs: {final['id'].is_unique}",
        f"Empty dialogue: {final['dialogue'].str.strip().eq('').sum()}",
        f"Duplicate dialogue: {final.duplicated('dialogue').sum()}",
        f"Clean source characters: {len(clean_source)}"
    ]

    VAL.write_text("\n".join(lines), encoding="utf-8")

    print()
    print("\n".join(lines))
    print()
    print("TOP SPEAKERS")
    print(final["speaker"].value_counts().head(25).to_string())
    print()
    print("REVIEW SAMPLE")
    print(
        review_df[
            ["id","chapter","paragraph_no","speaker","method","dialogue"]
        ].head(25).to_string(index=False)
    )

if __name__ == "__main__":
    main()