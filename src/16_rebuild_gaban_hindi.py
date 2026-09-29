import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}

RAW_DIR = Path("data/raw/hindi/gaban")
CLEAN_DIR = Path("data/cleaned/hindi")
FINAL_DIR = Path("data/final/hindi")

for p in [RAW_DIR, CLEAN_DIR, FINAL_DIR]:
    p.mkdir(parents=True, exist_ok=True)

CLEAN_FILE = CLEAN_DIR / "gaban_clean.txt"
FINAL_FILE = FINAL_DIR / "gaban_dialogue_final.csv"
REVIEW_FILE = FINAL_DIR / "gaban_dialogue_review.csv"
VALIDATION_FILE = FINAL_DIR / "gaban_final_validation.txt"

ATTR = (
    r"कहा|कहकर|कहती|कहते|कहने लगा|कहने लगी|कह उठा|कह उठी|"
    r"बोला|बोली|बोले|पूछा|पूछकर|जवाब दिया|उत्तर दिया|"
    r"बताया|बताकर|समझाया|समझाकर|चिल्लाया|चिल्लाकर|"
    r"पुकारा|पुकारकर|डांटा|डांटकर|फुसफुसाया|फुसफुसाकर|"
    r"मुस्कराकर कहा|हंसकर कहा|रोकर कहा"
)

ATTR_RE = re.compile(
    rf"(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n—–-]{{1,100}}?)"
    rf"\s+(?:ने\s+)?(?:{ATTR})\s*[-–—:]\s*"
    rf"(?P<speech>.+)$"
)

NAMED_DIRECT_RE = re.compile(
    r"^\s*(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n]{1,80}?)"
    r"\s*[-–—]\s*['\"'‘“]?(?P<speech>.+?)['\"'’”]?\s*$"
)

NAMED_COMMA_RE = re.compile(
    r"^\s*(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n]{1,80}?)"
    r"\s*,\s*['\"'‘“](?P<speech>.+?)['\"'’”]?\s*$"
)

INLINE_QUOTE_RE = re.compile(
    r"(?P<speaker>[अ-हक़-य़़A-Za-z][^।!?;:\n]{1,80}?)"
    r"\s+(?:ने\s+)?(?:कहा|बोला|बोली|बोले|पूछा|बताया|समझाया)"
    r"\s*[,:\-–—]\s*['\"'‘“](?P<speech>.+?)['\"'’”]"
)

DASH_RE = re.compile(
    r"^\s*[-–—]\s*(?:['\"'‘“])?(?P<speech>.+?)(?:['\"'’”])?\s*$"
)

BAD_SPEAKERS = {
    "से", "में", "पर", "और", "या", "तो", "ही", "भी", "अब", "तब",
    "जब", "जहां", "वहां", "यहां", "हुए", "हुआ", "हुई", "होकर",
    "जाकर", "आकर", "लेकर", "देकर", "रखकर", "करके", "देखकर",
    "सुनकर", "कहकर", "बोलकर", "आते", "जाते", "आता", "जाता",
    "आई", "गई", "दिया", "दिए", "दी", "था", "थे", "थी",
    "उसने", "उसका", "उसकी", "उसके", "फिर", "तब"
}


def clean_text(s):
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def clean_speech(s):
    s = re.sub(r"^\s*[-–—:]+\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip(" '\"‘’“”")
    return s.strip()


def normalize_speaker(s):
    s = clean_text(s)
    s = s.strip(" -–—,:;।'\"‘’“”")
    s = re.sub(
        r"^(और|फिर|तब|लेकिन|मगर|अतः|इसपर|इस पर)\s+",
        "",
        s
    )
    return s.strip()


def valid_speaker(s):
    s = normalize_speaker(s)

    if not s or s in BAD_SPEAKERS:
        return False

    if len(s) < 2 or len(s) > 80:
        return False

    if len(s.split()) > 10:
        return False

    return True


def narrative_score(s):
    patterns = [
        r"\bउसने\b", r"\bउसका\b", r"\bउसकी\b", r"\bउसके\b",
        r"\bउन्होंने\b", r"\bवह घर\b", r"\bघर जाकर\b",
        r"\bमन में\b", r"\bहृदय में\b", r"\bसोचने लगा\b",
        r"\bसोचने लगी\b", r"\bविचार करने\b", r"\bदेखकर वह\b",
        r"\bसुनकर वह\b"
    ]
    return sum(bool(re.search(p, s)) for p in patterns)


def quality(speech, speaker):
    words = len(speech.split())
    chars = len(speech)

    if chars < 5:
        return "very_short"

    if chars > 1800 or words > 300:
        return "review_long"

    if narrative_score(speech) >= 3 and words > 80:
        return "review_narrative"

    if speaker == "Unknown" and words > 130:
        return "review_long"

    return "ok"


def result(speaker, speech):
    speech = clean_speech(speech)

    if len(speech) < 5:
        return None

    speaker = normalize_speaker(speaker)

    if not valid_speaker(speaker):
        speaker = "Unknown"

    return speaker, speech


def extract_one(text):
    text = clean_text(text)

    if not text:
        return None

    m = INLINE_QUOTE_RE.search(text)
    if m:
        r = result(m.group("speaker"), m.group("speech"))
        if r:
            return r

    m = ATTR_RE.search(text)
    if m:
        r = result(m.group("speaker"), m.group("speech"))
        if r:
            return r

    m = NAMED_DIRECT_RE.match(text)
    if m:
        r = result(m.group("speaker"), m.group("speech"))
        if r and r[0] != "Unknown":
            return r

    m = NAMED_COMMA_RE.match(text)
    if m:
        r = result(m.group("speaker"), m.group("speech"))
        if r and r[0] != "Unknown":
            return r

    m = DASH_RE.match(text)
    if m:
        return result("Unknown", m.group("speech"))

    return None


def main():
    print()
    print("GABAN — REBUILT V7 HINDI CORPUS")
    print("=" * 50)

    paragraphs = []
    chapter_sources = []

    session = requests.Session()
    session.headers.update(HEADERS)

    for chapter in range(1, 6):
        r = session.get(BASE.format(n=chapter), timeout=30)
        r.raise_for_status()

        (RAW_DIR / f"gaban_chapter_{chapter}.html.txt").write_text(
            r.text,
            encoding="utf-8"
        )

        soup = BeautifulSoup(r.text, "html.parser")
        chapter_paragraphs = []

        for p in soup.find_all("p"):
            t = clean_text(p.get_text(" ", strip=True))

            if len(t) >= 20:
                chapter_paragraphs.append(t)

        chapter_sources.append("\n\n".join(chapter_paragraphs))

        for i, t in enumerate(chapter_paragraphs, 1):
            paragraphs.append({
                "chapter": chapter,
                "paragraph_no": i,
                "text": t
            })

    clean_source = "\n\n".join(chapter_sources)
    CLEAN_FILE.write_text(clean_source, encoding="utf-8")

    records = []

    for p in paragraphs:
        r = extract_one(p["text"])

        if not r:
            continue

        speaker, speech = r

        records.append({
            "chapter": p["chapter"],
            "paragraph_no": p["paragraph_no"],
            "speaker": speaker,
            "dialogue": speech,
            "source_text": p["text"],
            "flag": quality(speech, speaker)
        })

    df = pd.DataFrame(records)

    if df.empty:
        raise RuntimeError("No dialogue candidates found.")

    df["speaker"] = df["speaker"].fillna("Unknown")
    df["dialogue"] = df["dialogue"].map(clean_speech)

    df = df[df["dialogue"].str.len() >= 5].copy()

    df = df.drop_duplicates(
        subset=["chapter", "paragraph_no", "speaker", "dialogue"]
    ).reset_index(drop=True)

    review_mask = df["flag"].isin(
        ["review_long", "review_narrative", "very_short"]
    )

    final_df = df[~review_mask].copy()
    review_df = df[review_mask].copy()

    final_df.insert(
        0,
        "id",
        [f"GABAN_T{i:05d}" for i in range(1, len(final_df) + 1)]
    )

    review_df.insert(
        0,
        "id",
        [f"GABAN_REVIEW_{i:05d}" for i in range(1, len(review_df) + 1)]
    )

    columns = [
        "id",
        "chapter",
        "paragraph_no",
        "speaker",
        "dialogue",
        "source_text",
        "flag"
    ]

    final_df[columns].to_csv(
        FINAL_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    review_df[columns].to_csv(
        REVIEW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    known = (
        final_df["speaker"].ne("Unknown")
        & final_df["speaker"].str.strip().ne("")
    ).sum()

    unknown = len(final_df) - known

    chapter_counts = final_df["chapter"].value_counts().sort_index()
    flag_counts = df["flag"].value_counts()

    validation = [
        "GABAN — V7 VALIDATION",
        "=" * 50,
        f"Source paragraphs: {len(paragraphs)}",
        f"Dialogue candidates: {len(df)}",
        f"Final retained turns: {len(final_df)}",
        f"Review records: {len(review_df)}",
        "",
        f"Known speakers: {known}",
        f"Unknown speakers: {unknown}",
        f"Unknown percentage: {unknown / len(final_df) * 100:.2f}%"
        if len(final_df) else "Unknown percentage: 0.00%",
        "",
        "BY CHAPTER"
    ]

    for ch in range(1, 6):
        validation.append(
            f"chapter {ch}: {chapter_counts.get(ch, 0)}"
        )

    validation += ["", "FLAGS"]

    for flag in [
        "ok",
        "review_long",
        "review_narrative",
        "very_short"
    ]:
        validation.append(
            f"{flag}: {flag_counts.get(flag, 0)}"
        )

    validation += [
        "",
        "VALIDATION",
        f"Unique IDs: {final_df['id'].is_unique}",
        f"Non-empty dialogue: {final_df['dialogue'].str.strip().ne('').all()}",
        f"Clean source characters: {len(clean_source)}",
        "",
        "OUTPUTS",
        str(FINAL_FILE),
        str(REVIEW_FILE),
        str(VALIDATION_FILE)
    ]

    VALIDATION_FILE.write_text(
        "\n".join(validation),
        encoding="utf-8"
    )

    print()
    print("\n".join(validation))


if __name__ == "__main__":
    main()