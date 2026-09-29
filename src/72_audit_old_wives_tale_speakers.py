from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_attribution_analysis.csv"
)


print("Auditing speaker attribution in The Old Wives' Tale")
print("===================================================")
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
# BASIC NORMALIZATION
# --------------------------------------------------

def normalize_speaker(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    # Remove trailing punctuation.
    value = re.sub(
        r"[,:;.!?]+$",
        "",
        value
    ).strip()

    # Normalize repeated whitespace.
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


df["normalized_speaker_after"] = (
    df["speaker_after"]
    .apply(normalize_speaker)
)

df["normalized_speaker_before"] = (
    df["speaker_before"]
    .apply(normalize_speaker)
)


# --------------------------------------------------
# PRONOUN CHECK
# --------------------------------------------------

pronouns = {
    "he",
    "she",
    "him",
    "her",
    "they",
    "them",
    "it",
    "we",
    "us",
    "i",
    "you",
    "me",
    "his",
    "hers",
    "their",
    "our",
    "my",
}


def is_pronoun(value):

    return value.lower() in pronouns


df["speaker_after_is_pronoun"] = (
    df["normalized_speaker_after"]
    .apply(
        lambda x: bool(x)
        and is_pronoun(x)
    )
)

df["speaker_before_is_pronoun"] = (
    df["normalized_speaker_before"]
    .apply(
        lambda x: bool(x)
        and is_pronoun(x)
    )
)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("RAW → NORMALIZED SPEAKER CHECK")
print("------------------------------")

raw_after = (
    df["speaker_after"]
    .replace("", pd.NA)
    .dropna()
)

normalized_after = (
    df["normalized_speaker_after"]
    .replace("", pd.NA)
    .dropna()
)

print(
    f"Attributed after-quote rows: "
    f"{len(raw_after):,}"
)

print(
    f"Unique raw speaker labels: "
    f"{raw_after.nunique():,}"
)

print(
    f"Unique normalized speaker labels: "
    f"{normalized_after.nunique():,}"
)

print()


# --------------------------------------------------
# PRONOUNS
# --------------------------------------------------

print("PRONOUN-LIKE SPEAKER LABELS")
print("---------------------------")

pronoun_after = df[
    df["speaker_after_is_pronoun"]
]

print(
    f"After-quote pronoun labels: "
    f"{len(pronoun_after):,}"
)

print(
    pronoun_after[
        "normalized_speaker_after"
    ].value_counts()
)

print()


# --------------------------------------------------
# PUNCTUATION NORMALIZATION
# --------------------------------------------------

print("LABELS CHANGED BY PUNCTUATION NORMALIZATION")
print("--------------------------------------------")

changed = df[
    (
        df["speaker_after"].fillna("")
        !=
        df["normalized_speaker_after"]
    )
    &
    (
        df["normalized_speaker_after"] != ""
    )
]

print(
    f"Rows affected: "
    f"{len(changed):,}"
)

print()

for _, row in changed.head(30).iterrows():

    print(
        f"{row['candidate_id']}: "
        f"{row['speaker_after']!r} "
        f"-> "
        f"{row['normalized_speaker_after']!r}"
    )

print()


# --------------------------------------------------
# TOP NORMALIZED SPEAKERS
# --------------------------------------------------

print("TOP NORMALIZED SPEAKER LABELS")
print("-----------------------------")

speaker_counts = (
    df[
        df["normalized_speaker_after"] != ""
    ]["normalized_speaker_after"]
    .value_counts()
)

print(
    speaker_counts.head(40)
)

print()


# --------------------------------------------------
# SUSPICIOUS PRONOUN EXAMPLES
# --------------------------------------------------

print("SUSPICIOUS PRONOUN EXAMPLES")
print("---------------------------")

for _, row in pronoun_after.head(30).iterrows():

    preview = " ".join(
        str(
            row["quoted_text"]
        ).split()
    )

    if len(preview) > 180:
        preview = (
            preview[:180]
            + "..."
        )

    print(
        f"{row['candidate_id']}: "
        f'"{preview}"'
    )

    print(
        f"  Detected: "
        f"{row['speaker_after']}"
    )

    print(
        f"  Context after: "
        f"{row['context_after'][:250]}"
    )

    print()


print(
    "SPEAKER AUDIT COMPLETE."
)