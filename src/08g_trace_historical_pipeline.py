from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


FILES = [
    "07_extract_dialogue_english.py",
    "08_reconstruct_dialogue_turns_english.py",
    "09_recover_speakers_english.py",
    "10_audit_speakers_english.py",
    "11_audit_contextual_speakers_english.py",
    "12_normalize_speakers_english.py",
]


def read_file(path):
    return path.read_text(
        encoding="utf-8",
        errors="replace"
    )


def extract_paths(text):
    patterns = [
        r'["\']([^"\']*dialogue[^"\']*\.csv)["\']',
        r'["\']([^"\']*\.csv)["\']',
    ]

    found = []

    for pattern in patterns:

        for match in re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            if match not in found:
                found.append(match)

    return found


def main():

    print("=" * 70)
    print("VOF — HISTORICAL PIPELINE TRACE")
    print("=" * 70)

    for filename in FILES:

        path = SRC / filename

        print("\n" + "=" * 70)
        print(filename)
        print("=" * 70)

        if not path.exists():

            print("FILE NOT FOUND")
            continue

        text = read_file(path)

        print(
            f"\nLines: {len(text.splitlines()):,}"
        )

        print("\nReferenced CSV paths:")

        paths = extract_paths(text)

        if paths:

            for item in paths:
                print(f"  {item}")

        else:

            print("  None found")

        # --------------------------------------------------
        # Search for important pipeline operations
        # --------------------------------------------------

        keywords = [
            "read_csv",
            "to_csv",
            "writerow",
            "DictWriter",
            "reconstruct",
            "merge",
            "turn",
            "speaker",
            "Unknown",
            "unit_type",
        ]

        print("\nRelevant code lines:")

        lines = text.splitlines()

        shown = 0

        for i, line in enumerate(lines, start=1):

            if any(
                keyword.lower() in line.lower()
                for keyword in keywords
            ):

                print(
                    f"{i:4}: {line[:240]}"
                )

                shown += 1

                if shown >= 80:
                    print(
                        "  ... output limited to first 80 matching lines"
                    )
                    break

    print("\n" + "=" * 70)
    print("PIPELINE TRACE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()