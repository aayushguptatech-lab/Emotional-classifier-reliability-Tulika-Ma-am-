import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

for n in range(1, 6):
    url = BASE.format(n=n)
    r = requests.get(url, headers=HEADERS, timeout=30)
    print(f"\nCHAPTER {n}")
    print("URL:", url)
    print("STATUS:", r.status_code)
    print("BYTES:", len(r.content))

    if r.status_code != 200:
        continue

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    print("TEXT LENGTH:", len(text))
    print("TITLE:", soup.title.get_text(" ", strip=True) if soup.title else "None")
    print("PREVIEW:")
    print(text[:800].replace("\n", " | "))