from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_attribution_analysis.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v1.csv"
)


print("Preparing conservative speaker candidates")
print("==========================================")
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
# SPEECH VERBS
# --------------------------------------------------

speech_verbs = {
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "shouted",
    "whispered",
    "murmured",
    "remarked",
    "observed",
    "continued",
    "added",
    "declared",
    "suggested",
    "began",
    "interrupted",
    "called",
    "demanded",
    "urged",
    "begged",
    "protested",
    "criticized",
}


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


# --------------------------------------------------
# NORMALIZE LABEL
# --------------------------------------------------

def normalize_label(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    # Remove punctuation only from the END.
    value = re.sub(
        r"[.!?,;:]+$",
        "",
        value
    ).strip()

    return value


# --------------------------------------------------
# DETERMINE SPEAKER TYPE
# --------------------------------------------------

def classify_speaker(value):

    value = normalize_label(value)

    if not value:
        return "NONE"

    if value.lower() in pronouns:
        return "PRONOUN"

    # A clearly named person.
    if (
        re.match(
            r"^(?:Mr\.|Mrs\.|Miss|Dr\.)\s+[A-Z]",
            value
        )
        or re.match(
            r"^[A-Z][A-Za-z.'-]*$",
            value
        )
        or re.match(
            r"^[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)+$",
            value
        )
    ):
        return "NAMED"

    # Descriptive labels such as:
    # the doctor, the waiter, the landlord
    if value.lower().startswith("the "):
        return "DESCRIPTIVE"

    return "REVIEW"


# --------------------------------------------------
# PROCESS
# --------------------------------------------------

records = []

for _, row in df.iterrows():

    speaker_after = normalize_label(
        row["speaker_after"]
    )

    speaker_before = normalize_label(
        row["speaker_before"]
    )

    after_type = classify_speaker(
        speaker_after
    )

    before_type = classify_speaker(
        speaker_before
    )

    # ----------------------------------------------
    # PREFER A NAMED SPEAKER
    # ----------------------------------------------

    if after_type == "NAMED":

        proposed_speaker = speaker_after
        attribution_source = (
            "AFTER_QUOTE_NAMED"
        )

    elif before_type == "NAMED":

        proposed_speaker = speaker_before
        attribution_source = (
            "BEFORE_QUOTE_NAMED"
        )

    elif after_type == "DESCRIPTIVE":

        proposed_speaker = speaker_after
        attribution_source = (
            "AFTER_QUOTE_DESCRIPTIVE"
        )

    elif before_type == "DESCRIPTIVE":

        proposed_speaker = speaker_before
        attribution_source = (
            "BEFORE_QUOTE_DESCRIPTIVE"
        )

    elif after_type == "PRONOUN":

        proposed_speaker = "Unknown"
        attribution_source = (
            "PRONOUN_AFTER_REQUIRES_CONTEXT"
        )

    elif before_type == "PRONOUN":

        proposed_speaker = "Unknown"
        attribution_source = (
            "PRONOUN_BEFORE_REQUIRES_CONTEXT"
        )

    else:

        proposed_speaker = "Unknown"
        attribution_source = (
            "NO_RECOVERABLE_SPEAKER"
        )

    # ----------------------------------------------
    # DIALOGUE CANDIDATE STATUS
    # ----------------------------------------------

    has_speech_verb = (
        bool(row["attribution_after"])
        or
        bool(row["attribution_before"])
    )

    if (
        after_type in {
            "NAMED",
            "DESCRIPTIVE"
        }
        or
        before_type in {
            "NAMED",
            "DESCRIPTIVE"
        }
    ):
        candidate_status = (
            "ATTRIBUTED_DIALOGUE_CANDIDATE"
        )

    elif (
        after_type == "PRONOUN"
        or
        before_type == "PRONOUN"
    ):
        candidate_status = (
            "PRONOUN_DIALOGUE_REVIEW"
        )

    elif has_speech_verb:
        candidate_status = (
            "SPEECH_VERB_REVIEW"
        )

    else:
        candidate_status = (
            "UNATTRIBUTED_QUOTED_TEXT"
        )

    records.append(
        {
            "candidate_id": row[
                "candidate_id"
            ],

            "quoted_text": row[
                "quoted_text"
            ],

            "start_char": row[
                "start_char"
            ],

            "end_char": row[
                "end_char"
            ],

            "speaker_after_raw": row[
                "speaker_after"
            ],

            "speaker_before_raw": row[
                "speaker_before"
            ],

            "speaker_after_normalized": (
                speaker_after
            ),

            "speaker_before_normalized": (
                speaker_before
            ),

            "speaker_after_type": (
                after_type
            ),

            "speaker_before_type": (
                before_type
            ),

            "proposed_speaker": (
                proposed_speaker
            ),

            "attribution_source": (
                attribution_source
            ),

            "candidate_status": (
                candidate_status
            ),

            "context_before": row[
                "context_before"
            ],

            "context_after": row[
                "context_after"
            ],
        }
    )


out = pd.DataFrame(records)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

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
# SUMMARY
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

print("PROPOSED SPEAKER TYPE")
print("---------------------")

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
        out["proposed_speaker"] != "Unknown"
    ]["proposed_speaker"]
    .value_counts()
    .head(40)
)

print()

print("PRONOUN REVIEW COUNT")
print("--------------------")

pronoun_review = out[
    out["candidate_status"]
    ==
    "PRONOUN_DIALOGUE_REVIEW"
]

print(
    f"Pronoun review candidates: "
    f"{len(pronoun_review):,}"
)

print()

print("SAMPLE PRONOUN REVIEW CASES")
print("---------------------------")

for _, row in pronoun_review.head(20).iterrows():

    preview = " ".join(
        str(
            row["quoted_text"]
        ).split()
    )

    if len(preview) > 200:
        preview = (
            preview[:200]
            + "..."
        )

    print(
        f"{row['candidate_id']}: "
        f'"{preview}"'
    )

    print(
        f"  Proposed speaker: "
        f"{row['proposed_speaker']}"
    )

    print(
        f"  Attribution: "
        f"{row['attribution_source']}"
    )

    print()


print("OUTPUT")
print("------")
print(OUTPUT_FILE)

print()

print(
    "CONSERVATIVE SPEAKER CANDIDATE PREPARATION COMPLETE."
)