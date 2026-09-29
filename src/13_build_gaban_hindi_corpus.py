import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

RAW_DIR = Path("data/raw/hindi/gaban")
CLEAN_DIR = Path("data/cleaned/hindi")
FINAL_DIR = Path("data/final/hindi")

RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_FILE = CLEAN_DIR / "gaban_clean.txt"
FINAL_FILE = FINAL_DIR / "gaban_dialogue_candidates.csv"
AUDIT_FILE = FINAL_DIR / "gaban_validation.txt"


def fetch_chapter(n):
    url = BASE.format(n=n)
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text("\n", strip=True), url


def extract_book_text(text):
    markers = [
        "अनुक्रम | अध्याय",
        "अध्याय 1 | आगे",
        "अध्याय 2 | पीछे | आगे",
        "अध्याय 3 | पीछे | आगे",
        "अध्याय 4 | पीछे | आगे",
        "अध्याय 5 | पीछे"
    ]

    positions = [text.find(x) for x in markers if text.find(x) >= 0]

    if positions:
        text = text[min(positions):]

    lines = [x.strip() for x in text.splitlines() if x.strip()]

    remove = {
        "मुखपृष्ठ", "उपन्यास", "कहानी", "कविता", "व्यंग्य",
        "नाटक", "निबंध", "आलोचना", "विमर्श", "बाल साहित्य",
        "संस्मरण", "यात्रा वृत्तांत", "सिनेमा", "विविध",
        "लघुकथाएँ", "लोककथा", "बात-चीत", "वैचारिकी", "शोध",
        "डायरी", "सूक्तियाँ", "आत्मकथ्य", "जीवनी", "अन्य",
        "कोश", "समग्र-संचयन", "खोज", "संपर्क", "विश्वविद्यालय",
        "संग्रहालय", "लेखक को जानिए", "Change Script to",
        "Urdu", "Roman", "Devnagari"
    }

    lines = [x for x in lines if x not in remove]

    return "\n".join(lines)


def dialogue_candidates(text, chapter):
    rows = []
    turn_id = 1

    patterns = [
        r'“([^”]{2,})”',
        r'‘([^’]{2,})’',
        r'"([^"]{2,})"',
        r"'([^']{2,})'"
    ]

    occupied = []

    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.DOTALL):
            start, end = m.span()

            if any(start < e and end > s for s, e in occupied):
                continue

            quote = re.sub(r"\s+", " ", m.group(1)).strip()

            if len(quote) < 2:
                continue

            before = text[max(0, start - 180):start]
            after = text[end:min(len(text), end + 180)]

            speaker = "Unknown"
            evidence = "review"

            before_match = re.search(
                r'([अ-हक़-य़][^।!?]{0,60}?)(?:ने|बोला|बोली|कहा|कही|पूछा|उत्तर दिया|जवाब दिया|चिल्लाया|चिल्लाई|समझाया|बताया|कहा था)\s*$',
                before
            )

            after_match = re.search(
                r'^\s*([अ-हक़-य़][^।!?]{0,60}?)(?:ने|बोला|बोली|कहा|कही|पूछा|उत्तर दिया|जवाब दिया|चिल्लाया|चिल्लाई|समझाया|बताया)',
                after
            )

            if before_match:
                speaker = before_match.group(1).strip()
                evidence = "before_quote"
            elif after_match:
                speaker = after_match.group(1).strip()
                evidence = "after_quote"

            rows.append({
                "text_id": "GABAN",
                "turn_id": f"GABAN_T{turn_id:05d}",
                "chapter": chapter,
                "speaker": speaker,
                "speaker_evidence": evidence,
                "dialogue_text": quote,
                "start_char": start,
                "end_char": end,
                "source": "HindiSamay",
                "source_url": BASE.format(n=chapter)
            })

            occupied.append((start, end))
            turn_id += 1

    return rows


chapters = []
all_rows = []

for n in range(1, 6):
    text, url = fetch_chapter(n)

    raw_file = RAW_DIR / f"gaban_chapter_{n}.html.txt"
    raw_file.write_text(text, encoding="utf-8")

    clean = extract_book_text(text)
    chapters.append(f"\n===== अध्याय {n} =====\n{clean}")

    all_rows.extend(dialogue_candidates(clean, n))

clean_text = "\n".join(chapters)
SOURCE_FILE.write_text(clean_text, encoding="utf-8")

df = pd.DataFrame(all_rows)

if not df.empty:
    df = df.drop_duplicates(
        subset=["chapter", "start_char", "end_char", "dialogue_text"]
    ).reset_index(drop=True)

    df["turn_id"] = [
        f"GABAN_T{i:05d}" for i in range(1, len(df) + 1)
    ]

df.to_csv(FINAL_FILE, index=False, encoding="utf-8-sig")

known = 0 if df.empty else (~df["speaker"].eq("Unknown")).sum()
unknown = 0 if df.empty else df["speaker"].eq("Unknown").sum()

audit = [
    "GABAN — HINDI CORPUS VALIDATION",
    "",
    f"Chapters fetched: {len(chapters)}",
    f"Characters in clean source: {len(clean_text)}",
    f"Dialogue candidates: {len(df)}",
    f"Known speakers: {known}",
    f"Unknown speakers: {unknown}",
    f"Unknown percentage: {(unknown / len(df) * 100) if len(df) else 0:.2f}%",
    "",
    "SOURCE",
    "HindiSamay — प्रेमचंद — गबन",
    "https://www.hindisamay.com/",
    "",
    "VALIDATION",
    f"PASS source created: {SOURCE_FILE.exists()}",
    f"PASS final CSV created: {FINAL_FILE.exists()}",
    f"PASS unique turn IDs: {df['turn_id'].is_unique if not df.empty else True}",
    f"PASS non-empty dialogue: {bool(df['dialogue_text'].str.strip().ne('').all()) if not df.empty else True}",
    "",
    "NOTE",
    "Speaker identities are retained only when supported by local attribution patterns.",
    "Unknown values are not guessed."
]

AUDIT_FILE.write_text("\n".join(audit), encoding="utf-8")

print("\nGABAN — HINDI CORPUS BUILD")
print("=" * 45)
print(f"Chapters fetched:       {len(chapters)}")
print(f"Clean characters:       {len(clean_text)}")
print(f"Dialogue candidates:    {len(df)}")
print(f"Known speakers:         {known}")
print(f"Unknown speakers:       {unknown}")
print(f"Unknown percentage:     {(unknown / len(df) * 100) if len(df) else 0:.2f}%")
print()
print("OUTPUTS")
print(SOURCE_FILE)
print(FINAL_FILE)
print(AUDIT_FILE)