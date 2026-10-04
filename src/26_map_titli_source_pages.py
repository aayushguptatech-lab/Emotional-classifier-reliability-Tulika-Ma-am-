
from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "hindi" / "titli"
OUT = ROOT / "data" / "extracted" / "hindi" / "titli" / "titli_source_page_mapping.txt"

OUT.parent.mkdir(parents=True, exist_ok=True)

files = sorted(
    RAW_DIR.glob("titli_*.html"),
    key=lambda p: (
        9999 if not re.fullmatch(r"titli_\d+\.html", p.name) else
        int(re.search(r"(\d+)", p.stem).group(1)),
        p.name
    )
)

lines = []
lines.append("TITLI (तितली) — SOURCE PAGE MAPPING")
lines.append("")

for path in files:
    if path.name == "titli_part_1.html":
        continue

    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    # Collect links that point to Titli subpages.
    titli_links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        label = a.get_text(" ", strip=True)

        if "/wiki/तितली/" in href or "तितली/" in href:
            pair = (label, href)
            if pair not in titli_links:
                titli_links.append(pair)

    # Visible text.
    text = soup.get_text("\n", strip=True)
    lines_clean = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    lines.append("=" * 80)
    lines.append(f"FILE: {path.name}")
    lines.append(f"BYTES: {path.stat().st_size}")
    lines.append(f"TITLE: {title}")
    lines.append(f"TEXT_CHARS: {len(text)}")

    lines.append("TITLI SUBPAGE LINKS:")

    if titli_links:
        for label, href in titli_links[:20]:
            lines.append(f"  LABEL={label!r} | HREF={href!r}")
    else:
        lines.append("  NONE")

    lines.append("FIRST 12 NON-EMPTY TEXT LINES:")

    for item in lines_clean[:12]:
        lines.append(f"  {item}")

    lines.append("")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Report: {OUT}")
print(f"Files mapped: {len(files) - 1}")

