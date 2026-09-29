from pathlib import Path
import pandas as pd


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v4.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v5.csv"
)


print("Applying confirmed speaker identity repairs")
print("============================================")
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
# CONFIRMED REPAIRS
# --------------------------------------------------

# "Between" is a narration fragment, not a speaker.
between_mask = (
    df["speaker_before"]
    == "Between"
)

between_count = between_mask.sum()

df.loc[
    between_mask,
    "speaker_before"
] = "Unknown"

df.loc[
    between_mask,
    "attribution_source"
] = (
    "NARRATION_FALSE_POSITIVE"
)

df.loc[
    between_mask,
    "candidate_status"
] = (
    "SPEAKER_REVIEW"
)


# "Mr. Till Boldero" is the actual full identity
# found in the attribution context.
mr_till_mask = (
    df["speaker_before"]
    == "Mr. Till"
)

mr_till_count = mr_till_mask.sum()

df.loc[
    mr_till_mask,
    "speaker_before"
] = "Mr. Till Boldero"


# --------------------------------------------------
# REPORT
# --------------------------------------------------

print("CONFIRMED REPAIRS")
print("-----------------")

print(
    f'Changed "Between" -> "Unknown": '
    f'{between_count}'
)

print(
    f'Changed "Mr. Till" -> "Mr. Till Boldero": '
    f'{mr_till_count}'
)

print()


print("CHECK: BETWEEN")
print("--------------")

print(
    df[
        df["speaker_before"]
        == "Between"
    ]
)

print()


print("CHECK: MR. TILL")
print("---------------")

print(
    df[
        df["speaker_before"]
        .astype(str)
        .str.contains(
            "Mr. Till",
            regex=False
        )
    ][
        [
            "candidate_id",
            "speaker_before",
            "quoted_text",
            "speaker_after_raw"
        ]
    ]
)

print()


print("UPDATED SPEAKER COUNTS")
print("----------------------")

print(
    df[
        df["speaker_before"]
        != "Unknown"
    ][
        "speaker_before"
    ].value_counts()
    .head(70)
)

print()


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print("OUTPUT")
print("------")
print(OUTPUT_FILE)
print()

print(
    "CONFIRMED SPEAKER IDENTITY REPAIRS COMPLETE."
)