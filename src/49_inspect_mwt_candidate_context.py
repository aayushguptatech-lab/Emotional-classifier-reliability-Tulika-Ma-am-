from pathlib import Path
import csv


CLEAN_FILE = Path(
    "data/cleaned/english/"
    "the_man_who_was_thursday_clean.txt"
)

CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_context_review.csv"
)


print("Preparing MWT candidate context review...")


if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean file not found: {CLEAN_FILE}"
    )

if not CANDIDATE_FILE.exists():
    raise FileNotFoundError(
        f"Candidate file not found: {CANDIDATE_FILE}"
    )


text = CLEAN_FILE.read_text(
    encoding="utf-8"
)


with CANDIDATE_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:

    candidates = list(csv.DictReader(f))


review_rows = []


for row in candidates:

    start_char = int(row["start_char"])
    end_char = int(row["end_char"])

    context_before = text[
        max(0, start_char - 250):
        start_char
    ]

    context_after = text[
        end_char:
        min(len(text), end_char + 350)
    ]

    review_rows.append(
        {
            "candidate_id": row["candidate_id"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "quoted_text": row["quoted_text"],
            "context_before": context_before,
            "context_after": context_after,
        }
    )


fieldnames = [
    "candidate_id",
    "start_line",
    "end_line",
    "quoted_text",
    "context_before",
    "context_after",
]


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(review_rows)


print()
print("Candidates processed:", len(review_rows))
print()
print("FIRST 40 CANDIDATES WITH LOCAL TEXT CONTEXT")
print("---------------------------------------------")


for row in review_rows[:40]:

    before = row["context_before"].replace(
        "\n",
        " "
    )

    after = row["context_after"].replace(
        "\n",
        " "
    )

    quoted = row["quoted_text"].replace(
        "\n",
        " "
    )

    print()
    print("=" * 80)
    print(
        f'{row["candidate_id"]} | '
        f'lines {row["start_line"]}-{row["end_line"]}'
    )

    print()
    print("BEFORE:")
    print(before)

    print()
    print("QUOTED:")
    print(quoted)

    print()
    print("AFTER:")
    print(after)


print()
print("Context review file created.")
print(f"Saved to: {OUTPUT_FILE}")