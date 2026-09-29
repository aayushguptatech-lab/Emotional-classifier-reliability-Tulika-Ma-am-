import requests
from pathlib import Path
from datetime import datetime

SOURCE_URL = "https://www.gutenberg.org/cache/epub/1695/pg1695.txt"

OUTPUT_FILE = Path(
    "data/raw/english/the_man_who_was_thursday_raw.txt"
)

print("Downloading The Man Who Was Thursday...")

response = requests.get(SOURCE_URL, timeout=30)
response.raise_for_status()

text = response.text

if len(text.strip()) == 0:
    raise ValueError("Downloaded file is empty.")

if "The Man Who Was Thursday" not in text:
    raise ValueError(
        "The downloaded text does not appear to be "
        "The Man Who Was Thursday."
    )

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE.write_text(text, encoding="utf-8")

print("Download successful.")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Characters downloaded: {len(text):,}")
print(
    f"Downloaded at: "
    f"{datetime.now().isoformat(timespec='seconds')}"
)