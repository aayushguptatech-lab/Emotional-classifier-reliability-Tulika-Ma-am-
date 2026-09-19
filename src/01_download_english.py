import requests
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------
# 1. Source information
# ---------------------------------------------------------

SOURCE_URL = "https://www.gutenberg.org/cache/epub/3289/pg3289.txt"

OUTPUT_FILE = Path("data/raw/english/the_valley_of_fear_raw.txt")


# ---------------------------------------------------------
# 2. Download the source
# ---------------------------------------------------------

print("Downloading The Valley of Fear...")

response = requests.get(SOURCE_URL, timeout=30)

response.raise_for_status()

text = response.text


# ---------------------------------------------------------
# 3. Basic verification
# ---------------------------------------------------------

if len(text.strip()) == 0:
    raise ValueError("Downloaded file is empty.")

if "Valley of Fear" not in text:
    raise ValueError(
        "The downloaded text does not appear to be The Valley of Fear."
    )


# ---------------------------------------------------------
# 4. Save the raw source
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE.write_text(text, encoding="utf-8")


# ---------------------------------------------------------
# 5. Report what happened
# ---------------------------------------------------------

print("Download successful.")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Characters downloaded: {len(text):,}")
print(f"Downloaded at: {datetime.now().isoformat(timespec='seconds')}")