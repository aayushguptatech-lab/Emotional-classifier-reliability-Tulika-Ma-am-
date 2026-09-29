from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]

EXTRACTED = (
    ROOT
    / "data"
    / "extracted"
    / "english"
)


def inspect_csv(path):

    try:
        with path.open(
            "r",
            encoding="utf-8",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            rows = list(reader)

            fields = reader.fieldnames or []

        if not rows:
            return None

        return {
            "rows": len(rows),
            "fields": fields,
        }

    except Exception as e:

        return {
            "error": str(e)
        }


def main():

    print("=" * 70)
    print("VOF — HISTORICAL V2 ARTIFACT SEARCH")
    print("=" * 70)

    print(
        f"\nSearching:\n{EXTRACTED}\n"
    )

    results = []

    for path in sorted(
        EXTRACTED.glob("*.csv")
    ):

        info = inspect_csv(path)

        if not info:
            continue

        if "error" in info:

            print(
                f"\nERROR | {path.name}"
                f"\n{info['error']}"
            )

            continue

        results.append(
            (
                path.name,
                info["rows"],
                info["fields"]
            )
        )

    print(
        "\nCSV inventory:"
    )

    for name, rows, fields in results:

        print(
            f"\n{name}"
            f"\n  rows   : {rows:,}"
            f"\n  fields : {fields}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "FILES WITH 1,266 ROWS"
    )

    print(
        "=" * 70
    )

    matches = [
        item
        for item in results
        if item[1] == 1266
    ]

    if not matches:

        print(
            "\nNo CSV currently contains exactly 1,266 rows."
        )

    else:

        for name, rows, fields in matches:

            print(
                f"\n{name}"
                f"\n  rows   : {rows:,}"
                f"\n  fields : {fields}"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "FILES WITH V2-LIKE FIELDS"
    )

    print(
        "=" * 70
    )

    for name, rows, fields in results:

        field_text = " ".join(
            fields
        ).lower()

        if (
            "dialogue_text" in field_text
            and "speaker" in field_text
        ):

            print(
                f"\n{name}"
                f"\n  rows: {rows:,}"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "SEARCH COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()