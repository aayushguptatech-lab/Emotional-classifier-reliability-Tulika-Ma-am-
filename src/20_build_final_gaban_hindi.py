from pathlib import Path
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}

RAW = Path("data/raw/hindi/gaban")
CLEAN = Path("data/cleaned/hindi/gaban_clean.txt")
FINAL = Path("data/final/hindi/gaban_dialogue_final.csv")
REVIEW = Path("data/final/hindi/gaban_dialogue_review.csv")
VALIDATION = Path("data/final/hindi/gaban_final_validation.txt")

for p in [RAW, CLEAN.parent, FINAL.parent]:
    p.mkdir(parents=True, exist_ok=True)

NAMES = {
    "जालपा", "रमानाथ", "रमा", "रतन", "देवीदीन", "रमेश",
    "रमेश बाबू", "दारोग़ा", "दारोगा", "दयानाथ", "जागेश्वरी",
    "ज़ोहरा", "जोहरा", "जग्गो", "मणिभूषण", "डिप्टी",
    "इंस्पेक्टर", "गंगू", "चपरासी", "जौहरी", "चरनदास",
    "दीनदयाल", "प्यादा", "टिकट बाबू", "मानकी", "टीमल",
    "बिसाती", "शहजादी", "खां साहब", "मुंशीजी"
}

BAD = {
    "मैंने", "तुमने", "उसने", "उन्होंने", "हमने", "फिर",
    "सहसा", "खड़े", "डरते", "करके", "होकर", "जाकर",
    "आकर", "लेकर", "देकर", "देखकर", "सुनकर", "मुझे",
    "तुम", "वह", "यह", "और", "लेकिन", "पास जाकर"
}

ATTR = (
    r"(?:ने\s+)?(?:कहा|कहता|कहती|कहते|बोला|बोली|बोले|"
    r"पूछा|पूछती|पूछते|जवाब दिया|उत्तर दिया|बताया|"
    r"चिल्लाया|पुकारा|कह उठा|कह उठी|कहने लगा|कहने लगी)"
)

DASH = r"[-–—]"

def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()

def valid_name(raw):
    s = clean(raw)
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

def add(rows, chapter, paragraph, speaker, dialogue, method, source):
    dialogue = clean(dialogue).strip(" '\"‘’“”")

    if len(dialogue) < 8:
        return

    rows.append({
        "chapter": chapter,
        "paragraph_no": paragraph,
        "speaker": valid_name(speaker),
        "dialogue": dialogue,
        "method": method,
        "source_text": source
    })

def extract(text, chapter, paragraph):
    text = clean(text)
    rows = []

    patterns = [
        (
            rf"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{{1,55}}?)"
            rf"\s+{ATTR}\s*[,:\s]*{DASH}\s*"
            rf"(?P<quote>['‘“][^'’”\n]+['’”])",
            "attribution_dash_quote"
        ),
        (
            rf"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{{1,55}}?)"
            rf"\s+{ATTR}\s*[,:\s]+"
            rf"(?P<quote>['‘“][^'’”\n]+['’”])",
            "attribution_comma_quote"
        ),
        (
            rf"(?P<speaker>[अ-हक़-य़़][^।!?;:\n]{{1,45}}?)"
            rf"\s*{DASH}\s*"
            rf"(?P<quote>['‘“][^'’”\n]+['’”])",
            "named_dash_quote"
        )
    ]

    for pattern, method in patterns:
        for m in re.finditer(pattern, text):
            speaker = valid_name(m.group("speaker"))

            if speaker != "Unknown":
                add(
                    rows,
                    chapter,
                    paragraph,
                    speaker,
                    m.group("quote"),
                    method,
                    text
                )

    if rows:
        return rows

    # Leading quoted speech is retained only as Unknown review.
    m = re.match(r"^\s*['‘“](?P<quote>.+?)['’”]\s*$", text)

    if m:
        add(
            rows,
            chapter,
            paragraph,
            "Unknown",
            m.group("quote"),
            "leading_quote",
            text
        )

    return rows

def looks_like_navigation(text):
    terms = [
        "मुखपृष्ठ", "विषय-सूची", "कहानियाँ", "उपन्यास",
        "संपर्क", "अनुक्रम", "अध्याय सूची"
    ]
    return any(x in text for x in terms)

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    paragraphs = []
    clean_parts = []

    print()
    print("GABAN FINAL REBUILD")
    print("=" * 55)

    for chapter in range(1, 6):
        r = session.get(BASE.format(n=chapter), timeout=30)
        r.raise_for_status()

        (RAW / f"gaban_chapter_{chapter}.html.txt").write_text(
            r.text,
            encoding="utf-8"
        )

        soup = BeautifulSoup(r.text, "html.parser")

        chapter_paragraphs = []

        for p in soup.find_all("p"):
            text = clean(p.get_text(" ", strip=True))

            if len(text) >= 20:
                chapter_paragraphs.append(text)

        clean_parts.append("\n\n".join(chapter_paragraphs))

        for number, text in enumerate(chapter_paragraphs, 1):
            paragraphs.append((chapter, number, text))

        print(
            f"Chapter {chapter}: "
            f"{len(chapter_paragraphs)} paragraphs"
        )

    clean_source = "\n\n".join(clean_parts)
    CLEAN.write_text(clean_source, encoding="utf-8")

    rows = []

    for chapter, paragraph, text in paragraphs:
        rows.extend(
            extract(text, chapter, paragraph)
        )

    if not rows:
        raise RuntimeError("No dialogue candidates found.")

    df = pd.DataFrame(rows)

    df = df.drop_duplicates(
        subset=[
            "chapter",
            "paragraph_no",
            "speaker",
            "dialogue"
        ]
    ).reset_index(drop=True)

    df.insert(
        0,
        "id",
        [f"GABAN_T{i:05d}" for i in range(1, len(df) + 1)]
    )

    # Review conditions.
    review = (
        df["speaker"].eq("Unknown")
        | df["dialogue"].str.len().gt(900)
        | df["dialogue"].str.contains(
            r"कथा|उपन्यास|मुखपृष्ठ|विषय-सूची|अध्याय सूची|संपर्क",
            regex=True
        )
    )

    # Detect obvious narrative contamination.
    narrative_words = [
        "उसने", "उन्होंने", "उसका", "उसकी", "उसके",
        "रमा ने", "जालपा ने", "देवीदीन ने",
        "रमानाथ ने", "वह सोच", "मन में"
    ]

    for word in narrative_words:
        review |= (
            df["dialogue"].str.contains(
                word,
                regex=False,
                na=False
            )
            & df["dialogue"].str.len().gt(350)
        )

    final = df[~review].copy()
    review_df = df[review].copy()

    # Never retain obviously invalid speaker names.
    final = final[
        final["speaker"].isin(NAMES)
    ].copy()

    final = final.drop_duplicates(
        subset=["dialogue"]
    ).reset_index(drop=True)

    final["id"] = [
        f"GABAN_T{i:05d}"
        for i in range(1, len(final) + 1)
    ]

    final.to_csv(
        FINAL,
        index=False,
        encoding="utf-8-sig"
    )

    review_df.to_csv(
        REVIEW,
        index=False,
        encoding="utf-8-sig"
    )

    known = len(final)
    unknown = 0

    chapter_counts = (
        final["chapter"]
        .value_counts()
        .sort_index()
    )

    lines = [
        "GABAN FINAL CORPUS VALIDATION",
        "=" * 60,
        "",
        f"Source paragraphs: {len(paragraphs)}",
        f"Raw dialogue candidates: {len(df)}",
        f"Final retained turns: {len(final)}",
        f"Review records: {len(review_df)}",
        "",
        f"Known speakers: {known}",
        f"Unknown speakers: {unknown}",
        "",
        "CHAPTER DISTRIBUTION"
    ]

    for chapter in range(1, 6):
        lines.append(
            f"Chapter {chapter}: "
            f"{chapter_counts.get(chapter, 0)}"
        )

    lines += [
        "",
        "SPEAKER COUNT",
        f"Distinct speakers: {final['speaker'].nunique()}",
        "",
        "TOP SPEAKERS"
    ]

    for speaker, count in final["speaker"].value_counts().head(25).items():
        lines.append(f"{speaker}: {count}")

    lines += [
        "",
        "STRUCTURAL CHECKS",
        f"Rows: {len(final)}",
        f"IDs unique: {final['id'].is_unique}",
        f"Empty dialogue: {final['dialogue'].str.strip().eq('').sum()}",
        f"Duplicate dialogue: {final.duplicated('dialogue').sum()}",
        f"Source characters: {len(clean_source)}",
        "",
        "OUTPUT FILES",
        str(FINAL),
        str(REVIEW),
        str(VALIDATION)
    ]

    VALIDATION.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print()
    print("\n".join(lines))
    print()
    print("REVIEW SAMPLE")
    print(
        review_df[
            [
                "id",
                "chapter",
                "paragraph_no",
                "speaker",
                "method",
                "dialogue"
            ]
        ].head(25).to_string(index=False)
    )

if __name__ == "__main__":
    main()
    