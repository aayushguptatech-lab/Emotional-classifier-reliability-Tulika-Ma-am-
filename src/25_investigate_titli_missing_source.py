from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "hindi" / "titli"
OUT = ROOT / "data" / "extracted" / "hindi" / "titli" / "titli_missing_source_investigation.txt"

OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

BASE = "https://hi.wikisource.org/wiki/तितली"

lines = []
lines.append("TITLI (तितली) — MISSING SOURCE INVESTIGATION")
lines.append("")

session = requests.Session()
session.headers.update(HEADERS)

# ------------------------------------------------------------
# 1. Inspect special local file
# ------------------------------------------------------------

special = RAW_DIR / "titli_part_1.html"

lines.append("1. SPECIAL FILE: titli_part_1.html")

if special.exists():
    raw = special.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text("\n", strip=True)

    lines.append(f"Exists: YES")
    lines.append(f"Bytes: {special.stat().st_size}")
    lines.append(f"HTML title: {title}")
    lines.append(f"Extracted text characters: {len(text)}")

    # Look for Wikisource section links.
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        label = a.get_text(" ", strip=True)
        if "तितली" in href or "तितली" in label:
            links.append((label, href))

    lines.append(f"Titli-related links found: {len(links)}")

    for label, href in links[:30]:
        lines.append(f"  LABEL={label!r} | HREF={href!r}")

    # First meaningful text sample.
    meaningful = [
        p.strip()
        for p in text.splitlines()
        if p.strip()
    ]

    lines.append("")
    lines.append("First 25 non-empty text lines:")
    for item in meaningful[:25]:
        lines.append(f"  {item}")

else:
    lines.append("Exists: NO")

# ------------------------------------------------------------
# 2. Investigate missing pages 14, 15, 16
# ------------------------------------------------------------

lines.append("")
lines.append("2. MISSING PAGE INVESTIGATION")

for n in [14, 15, 16]:
    candidates = [
        f"{BASE}/{n}",
        f"{BASE}/1.{n}",
        f"{BASE}/2.{n}",
        f"{BASE}/3.{n}",
        f"{BASE}/4.{n}",
        f"{BASE}/{n}.1",
    ]

    lines.append("")
    lines.append(f"--- PAGE {n} CANDIDATES ---")

    for url in candidates:
        try:
            r = session.get(url, timeout=30)

            status = r.status_code
            content_type = r.headers.get("Content-Type", "")
            final_url = r.url

            if status == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.title.get_text(" ", strip=True) if soup.title else ""

                # Extract visible text.
                text = soup.get_text("\n", strip=True)
                nonempty = [
                    x.strip()
                    for x in text.splitlines()
                    if x.strip()
                ]

                # Detect obvious Wikisource missing-page response.
                missing_markers = [
                    "इस नाम का कोई पृष्ठ नहीं है",
                    "पृष्ठ नहीं मिला",
                    "यह पृष्ठ उपलब्ध नहीं है",
                    "इस पृष्ठ को अभी तक बनाया नहीं गया है",
                ]

                looks_missing = any(
                    marker in text for marker in missing_markers
                )

                lines.append(
                    f"URL={url} | STATUS=200 | FINAL={final_url} | "
                    f"TITLE={title!r} | TEXT_CHARS={len(text)} | "
                    f"LOOKS_MISSING={looks_missing}"
                )

                if nonempty:
                    lines.append(
                        f"  SAMPLE={nonempty[:5]!r}"
                    )
            else:
                lines.append(
                    f"URL={url} | STATUS={status} | FINAL={final_url} | "
                    f"CONTENT_TYPE={content_type}"
                )

        except Exception as exc:
            lines.append(
                f"URL={url} | ERROR={type(exc).__name__}: {exc}"
            )

# ------------------------------------------------------------
# 3. Conclusion
# ------------------------------------------------------------

lines.append("")
lines.append("3. INVESTIGATION RULES")
lines.append(
    "A page is considered recovered only if the response contains "
    "actual Titli novel prose rather than a Wikisource error or navigation page."
)
lines.append(
    "No missing page will be synthesized or inferred from surrounding pages."
)
lines.append(
    "The special local file will be included in the canonical source only "
    "if inspection shows that it contains genuine novel text not already "
    "represented by the numbered source pages."
)

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Report: {OUT}")
print("Investigated: titli_part_1.html")
print("Investigated missing pages: 14, 15, 16")
