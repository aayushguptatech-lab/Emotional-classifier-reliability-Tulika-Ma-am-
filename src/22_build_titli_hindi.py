import re
import csv
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://hi.wikisource.org/wiki/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

RAW = Path("data/raw/hindi/titli")
FINAL = Path("data/final/hindi")
RAW.mkdir(parents=True, exist_ok=True)
FINAL.mkdir(parents=True, exist_ok=True)

pages = []

for section, count in [(1, 8), (2, 10), (3, 8), (4, 5)]:
    for chapter in range(1, count + 1):
        pages.append(f"{BASE}तितली/{section}.{chapter}")

s = requests.Session()
s.headers.update(HEADERS)

rows = []

ATTR = re.compile(
    r"([^।!?]{1,45}?)(?:ने\s+)?"
    r"(?:कहा|कहती|कहता|कहते|बोली|बोला|बोले|पूछा|"
    r"जवाब दिया|उत्तर दिया)"
    r"\s*[-—:]?\s*[\"'“‘]?\s*(.+)",
    re.S
)

DASH = re.compile(
    r"^\s*([अ-हक़-य़][अ-हक़-य़\s]{0,35})\s*[-—]\s*[\"'“‘]?\s*(.+)",
    re.S
)

for page_no, url in enumerate(pages, 1):
    try:
        r = s.get(url, timeout=30)
        r.raise_for_status()

        (RAW / f"titli_{page_no:02d}.html").write_text(
            r.text, encoding="utf-8"
        )

        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.select_one("#mw-content-text")

        if not content:
            print(f"PAGE {page_no}: NO CONTENT")
            continue

        text = content.get_text("\n", strip=True)

        lines = [
            re.sub(r"\s+", " ", x).strip()
            for x in text.splitlines()
            if x.strip()
        ]

        for i, line in enumerate(lines):
            if len(line) < 3:
                continue

            if any(x in line for x in [
                "विकिस्रोत", "मुखपृष्ठ", "स्रोत देखें",
                "इतिहास देखें", "श्रेणियाँ", "जयशंकर प्रसाद",
                "सार्वजनिक डोमेन", "CC BY-SA"
            ]):
                continue

            speaker = "Unknown"
            dialogue = ""
            method = ""

            m = ATTR.search(line)

            if m:
                candidate = re.sub(r"\s+", " ", m.group(1)).strip(
                    " ,;:-—"
                )
                speech = re.sub(r"\s+", " ", m.group(2)).strip()

                bad = [
                    "जिस", "जिसने", "जिसको", "जब", "तब",
                    "फिर", "वह", "उस", "एक", "अपने",
                    "कुछ", "किसी", "और"
                ]

                if (
                    1 <= len(candidate) <= 45
                    and len(speech) >= 3
                    and not any(x in candidate for x in bad)
                ):
                    speaker = candidate
                    dialogue = speech
                    method = "attribution"

            if not dialogue:
                m = DASH.search(line)

                if m:
                    candidate = m.group(1).strip(" ,;:-—")
                    speech = re.sub(r"\s+", " ", m.group(2)).strip()

                    if 1 <= len(candidate) <= 35 and len(speech) >= 3:
                        speaker = candidate
                        dialogue = speech
                        method = "named_dash"

            if dialogue:
                rows.append([
                    f"TITLI_{page_no:02d}_{i:04d}",
                    page_no,
                    url,
                    speaker,
                    dialogue,
                    method,
                    line
                ])

        print(f"PAGE {page_no}: OK")

    except Exception as e:
        print(f"PAGE {page_no}: ERROR {e}")

out = FINAL / "titli_dialogue_candidates.csv"

with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow([
        "turn_id",
        "page",
        "source_url",
        "speaker",
        "dialogue",
        "method",
        "source_text"
    ])
    w.writerows(rows)

known = sum(1 for x in rows if x[3] != "Unknown")
unknown = len(rows) - known

validation = FINAL / "titli_validation.txt"

validation.write_text(
    "\n".join([
        "TITLI HINDI CORPUS VALIDATION",
        "",
        "Source: Hindi Wikisource",
        "Novel: तितली",
        "Author: जयशंकर प्रसाद",
        f"Pages attempted: {len(pages)}",
        f"Dialogue candidates: {len(rows)}",
        f"Known speakers: {known}",
        f"Unknown speakers: {unknown}",
        f"CSV: {out}"
    ]),
    encoding="utf-8"
)

print()
print("DONE")
print("Pages:", len(pages))
print("Dialogue candidates:", len(rows))
print("Known:", known)
print("Unknown:", unknown)
print("CSV:", out)