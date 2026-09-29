from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v3.csv"
)


print("Preparing v3 conservative speaker candidates")
print("==============================================")
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
# PRONOUNS
# --------------------------------------------------

PRONOUNS = {
    "he", "she", "him", "her",
    "they", "them", "it",
    "we", "us", "i", "you",
    "me", "his", "hers",
    "their", "our", "my"
}


# --------------------------------------------------
# SAFE DESCRIPTIVE SPEAKERS
#
# Only accept short, stable descriptions.
# --------------------------------------------------

SAFE_DESCRIPTIVE = {
    "the doctor",
    "the waiter",
    "the landlady",
    "the landlord",
    "the boy",
    "the auctioneer",
    "the englishman",
    "the man",
    "the other",
    "the mistress",
    "the postman",
    "the policeman",
    "the apprentice",
    "the girl",
    "the sailor",
    "the driver",
    "the portress",
}


# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------

def normalize(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# --------------------------------------------------
# EXTRACT LEADING PROPER NAME
# --------------------------------------------------

def extract_leading_named_speaker(value):

    value = normalize(value)

    if not value:
        return None

    # Remove leading quotation/punctuation artifacts.
    value = re.sub(
        r'^[\s,;:]+',
        '',
        value
    )

    # ------------------------------------------------
    # TITLED NAMES
    # ------------------------------------------------
    #
    # Examples:
    # Mr. Povey
    # Mrs. Baines
    # Miss Chetwynd
    # Dr. X
    #

    match = re.match(
        r"^(Mr\.|Mrs\.|Miss|Dr\.)\s+"
        r"([A-Z][A-Za-z.'-]*)",
        value
    )

    if match:
        return (
            match.group(1)
            + " "
            + match.group(2)
        )

    # ------------------------------------------------
    # MADAME / MONSIEUR
    # ------------------------------------------------

    match = re.match(
        r"^(Madame|Monsieur)\s+"
        r"([A-Z][A-Za-z.'-]*)",
        value
    )

    if match:
        return (
            match.group(1)
            + " "
            + match.group(2)
        )

    # ------------------------------------------------
    # TWO-WORD PROPER NAME
    # ------------------------------------------------

    match = re.match(
        r"^([A-Z][A-Za-z.'-]*)\s+"
        r"([A-Z][A-Za-z.'-]*)",
        value
    )

    if match:

        first = match.group(1)
        second = match.group(2)

        # Do not interpret a sequence such as
        # "Sophia. Constance" as a two-word name.
        if "." in first or "." in second:
            return None

        return (
            first
            + " "
            + second
        )

    # ------------------------------------------------
    # SINGLE PROPER NAME
    # ------------------------------------------------

    match = re.match(
        r"^([A-Z][A-Za-z.'-]*)",
        value
    )

    if match:

        name = match.group(1)

        # Do not accept sentence-like fragments.
        if name.lower() in {
            "the",
            "and",
            "but",
            "then",
            "this",
            "that",
            "yes",
            "no",
            "oh",
            "what",
            "why",
            "how",
            "well",
        }:
            return None

        return name

    return None


# --------------------------------------------------
# DESCRIPTIVE SPEAKER
# --------------------------------------------------

def extract_safe_descriptive(value):

    value = normalize(value)

    if not value:
        return None

    lower = value.lower()

    # Exact safe descriptions only.
    if lower in SAFE_DESCRIPTIVE:

        return value

    return None


# --------------------------------------------------
# PRONOUN CHECK
# --------------------------------------------------

def is_pronoun(value):

    value = normalize(value)

    return (
        value.lower() in PRONOUNS
    )


# --------------------------------------------------
# PROCESS
# --------------------------------------------------

records = []


for _, row in df.iterrows():

    after_raw = normalize(
        row["speaker_after_raw"]
    )

    before_raw = normalize(
        row["speaker_before_raw"]
    )

    proposed_speaker = "Unknown"
    attribution_source = "NO_RECOVERABLE_SPEAKER"
    candidate_status = "SPEAKER_REVIEW"

    # ----------------------------------------------
    # AFTER-QUOTE NAMED SPEAKER
    # ----------------------------------------------

    speaker = extract_leading_named_speaker(
        after_raw
    )

    if speaker:

        proposed_speaker = speaker
        attribution_source = (
            "AFTER_QUOTE_LEADING_NAMED"
        )
        candidate_status = (
            "ATTRIBUTED_DIALOGUE_CANDIDATE"
        )

    # ----------------------------------------------
    # BEFORE-QUOTE NAMED SPEAKER
    # ----------------------------------------------

    else:

        speaker = extract_leading_named_speaker(
            before_raw
        )

        if speaker:

            proposed_speaker = speaker
            attribution_source = (
                "BEFORE_QUOTE_LEADING_NAMED"
            )
            candidate_status = (
                "ATTRIBUTED_DIALOGUE_CANDIDATE"
            )

    # ----------------------------------------------
    # SAFE DESCRIPTIVE SPEAKER
    # ----------------------------------------------

    if proposed_speaker == "Unknown":

        speaker = extract_safe_descriptive(
            after_raw
        )

        if speaker:

            proposed_speaker = speaker
            attribution_source = (
                "AFTER_QUOTE_SAFE_DESCRIPTIVE"
            )
            candidate_status = (
                "ATTRIBUTED_DIALOGUE_CANDIDATE"
            )

    if proposed_speaker == "Unknown":

        speaker = extract_safe_descriptive(
            before_raw
        )

        if speaker:

            proposed_speaker = speaker
            attribution_source = (
                "BEFORE_QUOTE_SAFE_DESCRIPTIVE"
            )
            candidate_status = (
                "ATTRIBUTED_DIALOGUE_CANDIDATE"
            )

    # ----------------------------------------------
    # PRONOUN ATTRIBUTION
    # ----------------------------------------------

    if proposed_speaker == "Unknown":

        if is_pronoun(after_raw):

            attribution_source = (
                "PRONOUN_AFTER_REQUIRES_CONTEXT"
            )
            candidate_status = (
                "PRONOUN_DIALOGUE_REVIEW"
            )

        elif is_pronoun(before_raw):

            attribution_source = (
                "PRONOUN_BEFORE_REQUIRES_CONTEXT"
            )
            candidate_status = (
                "PRONOUN_DIALOGUE_REVIEW"
            )

    # ----------------------------------------------
    # STORE
    # ----------------------------------------------

    records.append({

        "candidate_id":
            row["candidate_id"],

        "quoted_text":
            row["quoted_text"],

        "start_char":
            row["start_char"],

        "end_char":
            row["end_char"],

        "speaker_after_raw":
            row["speaker_after_raw"],

        "speaker_before_raw":
            row["speaker_before_raw"],

        "proposed_speaker":
            proposed_speaker,

        "attribution_source":
            attribution_source,

        "candidate_status":
            candidate_status,

        "context_before":
            row["context_before"],

        "context_after":
            row["context_after"],
    })


out = pd.DataFrame(records)


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# REPORT
# --------------------------------------------------

print("CANDIDATE STATUS")
print("----------------")

print(
    out[
        "candidate_status"
    ].value_counts(
        dropna=False
    )
)

print()


print("ATTRIBUTION SOURCE")
print("------------------")

print(
    out[
        "attribution_source"
    ].value_counts(
        dropna=False
    )
)

print()


print("PROPOSED SPEAKER COUNTS")
print("-----------------------")

print(
    out[
        out["proposed_speaker"]
        != "Unknown"
    ][
        "proposed_speaker"
    ].value_counts()
    .head(60)
)

print()


# --------------------------------------------------
# CHECK SUSPICIOUS LABELS
# --------------------------------------------------

print("SUSPICIOUS LABEL CHECK")
print("----------------------")


suspicious = []

for _, row in out.iterrows():

    speaker = str(
        row["proposed_speaker"]
    )

    if speaker == "Unknown":
        continue

    if (
        len(speaker.split()) > 3
        or len(speaker) > 40
    ):
        suspicious.append(row)


print(
    f"Suspicious labels remaining: "
    f"{len(suspicious):,}"
)

print()


for row in suspicious[:50]:

    print(
        f'{row["candidate_id"]}: '
        f'{row["proposed_speaker"]}'
    )

print()


# --------------------------------------------------
# SAMPLE ATTRIBUTED DIALOGUE
# --------------------------------------------------

print("SAMPLE ATTRIBUTED DIALOGUE")
print("--------------------------")

attributed = out[
    out["candidate_status"]
    ==
    "ATTRIBUTED_DIALOGUE_CANDIDATE"
]

for _, row in attributed.head(30).iterrows():

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
        f'{row["candidate_id"]}: '
        f'{row["proposed_speaker"]}: '
        f'"{preview}"'
    )

print()


print("OUTPUT")
print("------")
print(OUTPUT_FILE)
print()

print(
    "V3 SPEAKER CANDIDATE "
    "PREPARATION COMPLETE."
)