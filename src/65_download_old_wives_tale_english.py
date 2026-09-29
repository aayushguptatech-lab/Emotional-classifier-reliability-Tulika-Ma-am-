import requests
from pathlib import Path
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================

URL = "https://www.gutenberg.org/cache/epub/5247/pg5247.txt"

OUTPUT = Path(
    "data/raw/english/the_old_wives_tale_raw.txt"
)


# =========================================================
# DOWNLOAD
# =========================================================

print("Downloading The Old Wives' Tale")
print("================================")
print()

print(f"Source: {URL}")
print(f"Output: {OUTPUT}")
print()


response = requests.get(
    URL,
    timeout=30
)

response.raise_for_status()


text = response.text


# =========================================================
# BASIC SOURCE CHECK
# =========================================================

if "THE OLD WIVES" not in text.upper():

    raise ValueError(
        "Expected title marker was not found "
        "in the downloaded source."
    )


if "ARNOLD BENNETT" not in text.upper():

    raise ValueError(
        "Expected author marker was not found "
        "in the downloaded source."
    )


# =========================================================
# WRITE RAW FILE
# =========================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT.write_text(
    text,
    encoding="utf-8"
)


# =========================================================
# REPORT
# =========================================================

print("DOWNLOAD SUCCESSFUL")
print("-------------------")

print(
    f"Characters: {len(text):,}"
)

print(
    f"Words: {len(text.split()):,}"
)

print(
    f"Lines: {len(text.splitlines()):,}"
)

print(
    f"Downloaded at: "
    f"{datetime.now().isoformat(timespec='seconds')}"
)

print()

print(
    f"Saved to: {OUTPUT}"
)