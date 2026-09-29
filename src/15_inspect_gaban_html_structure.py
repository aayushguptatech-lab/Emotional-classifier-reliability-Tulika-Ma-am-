import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.hindisamay.com/content/226/{n}/प्रेमचंद--धनपत-राय-उपन्यास-गबन-अध्याय-1.cspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

for n in [1]:
    url = BASE.format(n=n)
    html = requests.get(url, headers=HEADERS, timeout=60).text
    soup = BeautifulSoup(html, "html.parser")

    print("\nGABAN HTML STRUCTURE")
    print("=" * 60)
    print("URL:", url)
    print("HTML characters:", len(html))

    print("\nELEMENT COUNTS")
    for tag in ["p", "div", "article", "section", "blockquote", "span", "td"]:
        print(f"{tag:12} {len(soup.find_all(tag))}")

    print("\nCLASSES CONTAINING TEXT")
    classes = {}

    for tag in soup.find_all(True):
        cls = tag.get("class")
        if cls:
            key = " ".join(cls)
            text = tag.get_text(" ", strip=True)
            if len(text) > 100:
                classes[key] = classes.get(key, 0) + 1

    for cls, count in sorted(classes.items(), key=lambda x: -x[1])[:30]:
        print(f"{count:5}  {cls}")

    print("\nLONG TEXT ELEMENTS")
    shown = 0

    for tag in soup.find_all(["p", "div", "article", "section", "td"]):
        text = tag.get_text(" ", strip=True)

        if len(text) >= 200:
            print("\nTAG:", tag.name)
            print("CLASS:", tag.get("class"))
            print("ID:", tag.get("id"))
            print("TEXT:", text[:700])

            shown += 1

            if shown >= 15:
                break

    print("\nTEXT WITH DIALOGUE-LIKE MARKERS")

    markers = [
        "कहा", "कही", "बोला", "बोली", "पूछा",
        "उत्तर", "जवाब", "चिल्लाया", "चिल्लाई",
        "बोले", "कहने लगा", "कहने लगी"
    ]

    count = 0

    for tag in soup.find_all(["p", "div", "td"]):
        text = tag.get_text(" ", strip=True)

        if any(x in text for x in markers):
            print("\nTAG:", tag.name)
            print("CLASS:", tag.get("class"))
            print(text[:1000])

            count += 1

            if count >= 15:
                break