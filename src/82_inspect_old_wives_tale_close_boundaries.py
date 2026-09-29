from pathlib import Path
import pandas as pd


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_turn_boundary_audit_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_close_boundary_review_v1.csv"
)


print("Inspecting close dialogue boundaries")
print("=====================================")
print()


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
)


df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# CLOSE SAME-SPEAKER BOUNDARIES
# --------------------------------------------------

close_same = df[
    (
        df["same_speaker"]
        == True
    )
    &
    (
        df["character_gap"]
        <= 500
    )
].copy()


print(
    "CLOSE SAME-SPEAKER BOUNDARIES"
)
print(
    "-----------------------------"
)

print(
    f"Cases requiring inspection: "
    f"{len(close_same):,}"
)

print()


for _, row in close_same.iterrows():

    print("=" * 75)

    print(
        f'CURRENT: {row["current_turn_id"]} '
        f'| SPEAKER: {row["current_speaker"]}'
    )

    print(
        f'CURRENT TEXT: '
        f'{row["current_text"]}'
    )

    print()

    print(
        f'NEXT: {row["next_turn_id"]} '
        f'| SPEAKER: {row["next_speaker"]}'
    )

    print(
        f'NEXT TEXT: '
        f'{row["next_text"]}'
    )

    print()

    print(
        f'CHARACTER GAP: '
        f'{row["character_gap"]}'
    )


# --------------------------------------------------
# CLOSE UNKNOWN BOUNDARIES
# --------------------------------------------------

close_unknown = df[
    (
        df["unknown_boundary"]
        == True
    )
    &
    (
        df["character_gap"]
        <= 500
    )
].copy()


print()
print()
print(
    "CLOSE UNKNOWN / REVIEW BOUNDARIES"
)
print(
    "--------------------------------"
)

print(
    f"Cases requiring inspection: "
    f"{len(close_unknown):,}"
)

print()


for _, row in close_unknown.iterrows():

    print("=" * 75)

    print(
        f'CURRENT: {row["current_turn_id"]} '
        f'| SPEAKER: {row["current_speaker"]}'
    )

    print(
        f'CURRENT TEXT: '
        f'{row["current_text"]}'
    )

    print()

    print(
        f'NEXT: {row["next_turn_id"]} '
        f'| SPEAKER: {row["next_speaker"]}'
    )

    print(
        f'NEXT TEXT: '
        f'{row["next_text"]}'
    )

    print()

    print(
        f'CHARACTER GAP: '
        f'{row["character_gap"]}'
    )


# --------------------------------------------------
# SAVE REVIEW FILE
# --------------------------------------------------

review = pd.concat(
    [
        close_same.assign(
            review_type="CLOSE_SAME_SPEAKER"
        ),
        close_unknown.assign(
            review_type="CLOSE_UNKNOWN"
        ),
    ],
    ignore_index=True
)


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


review.to_csv(
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
    "CLOSE BOUNDARY INSPECTION COMPLETE."
)
