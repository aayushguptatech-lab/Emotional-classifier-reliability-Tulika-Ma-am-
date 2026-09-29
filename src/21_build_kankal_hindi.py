import re
import csv
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

BASE = "http://gadyakosh.org/gk/कंकाल_/_जयशंकर_प्रसाद"
HEADERS = {"User-Agent": "Mozilla/5.0"}

RAW = Path("data/raw/hindi/kankal")
FINAL = Path("data/final/hindi")
RAW.mkdir(parents=True, exist_ok=True)
FINAL.mkdir(parents=True, exist_ok=True)

s = requests.Session()
s.headers.update(HEADERS)

r = s.get(BASE, timeout=30)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

links = []
for a in soup.find_all("a", href=True):
    text = a.get_text(" ", strip=True)
    href = urljoin(BASE, a["href"])
    if "कंकाल" in text and href not in links and href != BASE:
        links.append(href)

print("PART LINKS:", len(links))

rows = []
part_no = 0

ATTR = re.compile(
    r"([अ-हक़-य़][^।!?]{0,40}?)"
    r"(?:ने\s+)?(?:कहा|कहती|कहता|कहते|बोली|बोला|बोले|पूछा|जवाब दिया|उत्तर दिया)"
    r"\s*[-—:]*\s*[\"'“‘]?\s*(.+)",
    re.S
)

DASH = re.compile(
    r"^\s*([अ-हक़-य़][^।!?]{0,30})\s*[-—]\s*[\"'“‘]?\s*(.+)",
    re.S
)

NAME = re.compile(r"^[अ-हक़-य़][अ-हक़-य़\s]{0,35}$")

for i, url in enumerate(links, 1):
    try:
        rr = s.get(url, timeout=30)
        rr.raise_for_status()
        html = rr.text
        (RAW / f"kankal_part_{i}.html").write_text(html, encoding="utf-8")

        psoup = BeautifulSoup(html, "html.parser")

        container = None
        for d in psoup.find_all("div"):
            txt = d.get_text(" ", strip=True)
            if len(txt) > 1000 and ("कंकाल" in txt or "जयशंकर प्रसाद" in txt):
                container = d
                break

        if not container:
            container = psoup

        blocks = []
        for tag in container.find_all(["p", "div"]):
            txt = tag.get_text(" ", strip=True)
            if 20 <= len(txt) <= 5000:
                if txt not in blocks:
                    blocks.append(txt)

        for j, text in enumerate(blocks, 1):
            if any(x in text.lower() for x in [
                "मुखपृष्ठ", "कविता कोश", "गद्य कोश", "संपर्क", "लॉग इन"
            ]):
                continue

            speaker = ""
            dialogue = ""
            method = ""

            m = ATTR.search(text)
            if m:
                candidate = m.group(1).strip(" ,;:-—")
                speech = m.group(2).strip()
                if NAME.match(candidate) and len(speech) >= 3:
                    speaker = candidate
                    dialogue = speech
                    method = "attribution"

            if not dialogue:
                m = DASH.search(text)
                if m:
                    candidate = m.group(1).strip(" ,;:-—")
                    speech = m.group(2).strip()
                    if NAME.match(candidate) and len(speech) >= 3:
                        speaker = candidate
                        dialogue = speech
                        method = "named_dash"

            if dialogue:
                dialogue = re.sub(r"\s+", " ", dialogue).strip()
                rows.append([
                    f"KANKAL_{i:02d}_{j:04d}",
                    i,
                    speaker,
                    dialogue,
                    method,
                    text
                ])

        part_no += 1
        print(f"PART {i}: OK")

    except Exception as e:
        print(f"PART {i}: ERROR {e}")

out = FINAL / "kankal_dialogue_final.csv"

with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow([
        "turn_id",
        "part",
        "speaker",
        "dialogue",
        "method",
        "source_text"
    ])
    w.writerows(rows)

known = sum(1 for x in rows if x[2])
unknown = len(rows) - known

validation = FINAL / "kankal_validation.txt"
validation.write_text(
    "\n".join([
        "KANKAL HINDI CORPUS VALIDATION",
        "",
        f"Source URL: {BASE}",
        f"Parts found: {len(links)}",
        f"Parts processed: {part_no}",
        f"Dialogue turns: {len(rows)}",
        f"Known speakers: {known}",
        f"Unknown speakers: {unknown}",
        f"CSV: {out}",
    ]),
    encoding="utf-8"
)

print()
print("DONE")
print("Parts:", len(links))
print("Processed:", part_no)
print("Dialogue turns:", len(rows))
print("Known:", known)
print("Unknown:", unknown)
print("CSV:", out)