from pathlib import Path
import pandas as pd


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_turns_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_turn_boundary_audit_v1.csv"
)


print("Auditing dialogue turn boundaries")
print("=================================")
print()


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

df = df.sort_values(
    "start_char"
).reset_index(drop=True)


# --------------------------------------------------
# COMPARE ADJACENT TURNS
# --------------------------------------------------

audit_rows = []


for i in range(len(df) - 1):

    current = df.iloc[i]
    nxt = df.iloc[i + 1]

    current_speaker = str(
        current["speaker"]
    ).strip()

    next_speaker = str(
        nxt["speaker"]
    ).strip()

    same_speaker = (
        current_speaker
        == next_speaker
        and current_speaker != "Unknown"
    )

    unknown_boundary = (
        current_speaker == "Unknown"
        or next_speaker == "Unknown"
    )

    gap = (
        float(nxt["start_char"])
        - float(current["end_char"])
    )

    audit_rows.append(
        {
            "current_turn_id":
                current["turn_id"],

            "next_turn_id":
                nxt["turn_id"],

            "current_candidate_id":
                current["candidate_id"],

            "next_candidate_id":
                nxt["candidate_id"],

            "current_speaker":
                current_speaker,

            "next_speaker":
                next_speaker,

            "same_speaker":
                same_speaker,

            "unknown_boundary":
                unknown_boundary,

            "character_gap":
                gap,

            "current_text":
                current["quoted_text"],

            "next_text":
                nxt["quoted_text"],
        }
    )


audit = pd.DataFrame(
    audit_rows
)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

same_speaker_count = int(
    audit["same_speaker"].sum()
)

unknown_boundary_count = int(
    audit["unknown_boundary"].sum()
)


print("BOUNDARY SUMMARY")
print("----------------")

print(
    f"Total adjacent boundaries: "
    f"{len(audit):,}"
)

print(
    f"Same-speaker adjacent boundaries: "
    f"{same_speaker_count:,}"
)

print(
    f"Boundaries involving Unknown: "
    f"{unknown_boundary_count:,}"
)

print()


# --------------------------------------------------
# SAME-SPEAKER CASES
# --------------------------------------------------

same_speaker = audit[
    audit["same_speaker"]
].copy()


print(
    "SAME-SPEAKER ADJACENT CASES"
)
print(
    "---------------------------"
)

print(
    f"Cases requiring inspection: "
    f"{len(same_speaker):,}"
)

print()


for _, row in same_speaker.head(100).iterrows():

    print("=" * 70)

    print(
        f'{row["current_turn_id"]} '
        f'({row["current_speaker"]})'
    )

    print(
        f'CURRENT: '
        f'{row["current_text"]}'
    )

    print()

    print(
        f'{row["next_turn_id"]} '
        f'({row["next_speaker"]})'
    )

    print(
        f'NEXT: '
        f'{row["next_text"]}'
    )

    print()

    print(
        f'Character gap: '
        f'{row["character_gap"]}'
    )


# --------------------------------------------------
# UNKNOWN CASES
# --------------------------------------------------

print()
print(
    "UNKNOWN / REVIEW BOUNDARIES"
)
print(
    "---------------------------"
)

unknown_cases = audit[
    audit["unknown_boundary"]
].copy()

print(
    f"Cases involving Unknown: "
    f"{len(unknown_cases):,}"
)

print()


for _, row in unknown_cases.head(60).iterrows():

    print("=" * 70)

    print(
        f'{row["current_turn_id"]}: '
        f'{row["current_speaker"]}'
    )

    print(
        f'CURRENT: '
        f'{row["current_text"]}'
    )

    print()

    print(
        f'{row["next_turn_id"]}: '
        f'{row["next_speaker"]}'
    )

    print(
        f'NEXT: '
        f'{row["next_text"]}'
    )

    print()

    print(
        f'Character gap: '
        f'{row["character_gap"]}'
    )


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

audit.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("OUTPUT")
print("------")
print(
    OUTPUT_FILE
)
print()

print(
    "TURN BOUNDARY AUDIT COMPLETE."
)
