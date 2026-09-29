import pandas as pd
from pathlib import Path


TURN_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v5.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_speaker_audit_v5.csv"
)


turns = pd.read_csv(
    TURN_FILE
)

audit = pd.read_csv(
    AUDIT_FILE
)


# ---------------------------------------------------------
# Build candidate lookup
# ---------------------------------------------------------

candidate_lookup = {}

for _, row in audit.iterrows():

    candidate_lookup[
        str(row["candidate_id"])
    ] = row


# ---------------------------------------------------------
# Examine multi-candidate turns
# ---------------------------------------------------------

print()
print(
    "MWT V5 BOUNDARY AUDIT"
)

print(
    "====================="
)

print()

multi = turns[
    turns["source_candidate_ids"]
    .astype(str)
    .str.contains(r"\|", regex=True)
]

print(
    f"Total turns: {len(turns):,}"
)

print(
    f"Multi-candidate turns: {len(multi):,}"
)

print()


# ---------------------------------------------------------
# Print suspicious multi-candidate turns
# ---------------------------------------------------------

shown = 0

for _, turn in multi.iterrows():

    ids = str(
        turn["source_candidate_ids"]
    ).split("|")

    if len(ids) < 2:
        continue

    print("=" * 80)

    print(
        f"{turn['turn_id']} | "
        f"speaker={turn['speaker']} | "
        f"confidence={turn['extraction_confidence']}"
    )

    print(
        f"Candidates: {turn['source_candidate_ids']}"
    )

    print()

    for cid in ids:

        if cid not in candidate_lookup:
            continue

        row = candidate_lookup[cid]

        print(
            f"{cid} | "
            f"attr={row['attribution_type']} | "
            f"explicit={row['explicit_speaker']} | "
            f"resolved={row['resolved_speaker']}"
        )

        print(
            "  QUOTE:",
            str(
                row["quoted_text"]
            )[:500]
        )

        gap = str(
            row["gap_text"]
        )

        if gap:
            print(
                "  GAP:",
                gap[:300]
            )

        print()

    shown += 1

    if shown >= 60:
        break


print()

print(
    "Displayed first 60 multi-candidate turns."
)