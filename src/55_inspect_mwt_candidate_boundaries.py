import pandas as pd
from pathlib import Path


CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/"
    "the_man_who_was_thursday_clean.txt"
)


print("MWT candidate-boundary inspection")
print("----------------------------------")
print()


candidates = pd.read_csv(CANDIDATE_FILE)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

candidates = candidates.sort_values(
    by=["start_char", "end_char"]
).reset_index(drop=True)


print(
    f"Candidates loaded: {len(candidates):,}"
)

print()


# ---------------------------------------------------------
# Inspect selected ranges
# ---------------------------------------------------------

ranges = [
    (1, 40),
    (40, 80),
    (80, 120),
]


for start_num, end_num in ranges:

    print()
    print("=" * 80)
    print(
        f"CANDIDATES {start_num} TO {end_num}"
    )
    print("=" * 80)

    for i in range(
        start_num - 1,
        min(end_num, len(candidates))
    ):

        row = candidates.iloc[i]

        candidate_id = row["candidate_id"]

        start_char = int(
            row["start_char"]
        )

        end_char = int(
            row["end_char"]
        )

        quoted_text = str(
            row["quoted_text"]
        ).replace("\n", " ")

        print()
        print("-" * 80)

        print(
            f"{candidate_id} | "
            f"lines {row['start_line']}-"
            f"{row['end_line']}"
        )

        print(
            "QUOTED TEXT:"
        )

        print(
            quoted_text[:500]
        )

        # -------------------------------------------------
        # Text AFTER this candidate and BEFORE next
        # -------------------------------------------------

        if i < len(candidates) - 1:

            next_row = candidates.iloc[i + 1]

            next_start = int(
                next_row["start_char"]
            )

            gap = clean_text[
                end_char:next_start
            ]

            print()
            print(
                f"NEXT CANDIDATE: "
                f"{next_row['candidate_id']}"
            )

            print(
                "TEXT BETWEEN CANDIDATES:"
            )

            print(
                gap[:1200]
                .replace("\n", " ")
            )

        else:

            print(
                "No next candidate."
            )


print()
print("=" * 80)
print("BOUNDARY INSPECTION COMPLETE")
print("=" * 80)
