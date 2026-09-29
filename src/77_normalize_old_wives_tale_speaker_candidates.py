from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v3.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v4.csv"
)


print("Normalizing speaker identities")
print("================================")
print()


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


def normalize_speaker(value):

    if pd.isna(value):
        return "Unknown"

    value = str(value).strip()

    if not value:
        return "Unknown"

    # Remove terminal punctuation only.
    value = re.sub(
        r"[.!?,;:]+$",
        "",
        value
    ).strip()

    # Collapse whitespace.
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


df["speaker_before"] = (
    df["proposed_speaker"]
    .apply(normalize_speaker)
)


# Preserve Unknown exactly.
df.loc[
    df["speaker_before"] == "",
    "speaker_before"
] = "Unknown"


# --------------------------------------------------
# REPORT NORMALIZATION
# --------------------------------------------------

print("NORMALIZED SPEAKER COUNTS")
print("--------------------------")

print(
    df[
        df["speaker_before"] != "Unknown"
    ][
        "speaker_before"
    ].value_counts()
    .head(60)
)

print()


# --------------------------------------------------
# CHECK FOR REMAINING TERMINAL PUNCTUATION
# --------------------------------------------------

remaining_punctuation = df[
    (
        df["speaker_before"]
        != "Unknown"
    )
    &
    (
        df["speaker_before"]
        .astype(str)
        .str.contains(
            r"[.!?,;:]$",
            regex=True
        )
    )
]


print(
    "SPEAKERS WITH TERMINAL PUNCTUATION "
    "AFTER NORMALIZATION:",
    len(remaining_punctuation)
)

print()


# --------------------------------------------------
# IMPORTANT IDENTITY COLLAPSE CHECK
# --------------------------------------------------

print("IDENTITY COLLAPSE CHECK")
print("-----------------------")

for name in [
    "Sophia",
    "Constance",
    "Mrs. Baines",
    "Mr. Povey",
    "Mr. Critchlow",
    "Lily",
    "Amy",
    "Gerald",
    "Samuel",
    "Cyril",
    "Matthew",
]:

    count = (
        df["speaker_before"]
        == name
    ).sum()

    if count:
        print(
            f"{name}: {count}"
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
    "SPEAKER IDENTITY NORMALIZATION COMPLETE."
)