from pathlib import Path
import re
import pandas as pd


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_attribution_analysis.csv"
)


print("Analyzing speaker attribution in The Old Wives' Tale")
print("=====================================================")
print()


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Candidate file not found: {INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# SPEECH VERBS
# --------------------------------------------------

speech_verbs = [
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
]


speech_verbs_pattern = "|".join(
    re.escape(v)
    for v in speech_verbs
)


# --------------------------------------------------
# NAME / SPEAKER EXTRACTION
# --------------------------------------------------

def extract_after_speaker(attribution):
    """
    Try to identify a speaker from text after
    the quoted dialogue.

    Examples:
        said Constance
        exclaimed Sophia
        said Mr. Povey
        murmured Sophia
    """

    if not attribution:
        return ""

    patterns = [
        rf"\b(?:{speech_verbs_pattern})\s+"
        rf"(?P<speaker>"
        rf"(?:Mr\.|Mrs\.|Miss|Dr\.)?\s*"
        rf"[A-Z][A-Za-z.'-]*"
        rf"(?:\s+[A-Z][A-Za-z.'-]*){{0,4}}"
        rf")",

        rf"\b(?:{speech_verbs_pattern})\s+"
        rf"(?P<speaker>"
        rf"[a-z]+"
        rf"(?:\s+[a-z]+){{0,3}}"
        rf")",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            attribution,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(
                "speaker"
            ).strip()

    return ""


def extract_before_speaker(attribution):
    """
    Try to identify a speaker from text before
    the quoted dialogue.
    """

    if not attribution:
        return ""

    patterns = [
        rf"(?P<speaker>"
        rf"(?:Mr\.|Mrs\.|Miss|Dr\.)?\s*"
        rf"[A-Z][A-Za-z.'-]*"
        rf"(?:\s+[A-Z][A-Za-z.'-]*){{0,4}}"
        rf")\s+"
        rf"(?:{speech_verbs_pattern})",

        rf"(?P<speaker>"
        rf"[a-z]+"
        rf"(?:\s+[a-z]+){{0,3}}"
        rf")\s+"
        rf"(?:{speech_verbs_pattern})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            attribution,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(
                "speaker"
            ).strip()

    return ""


# --------------------------------------------------
# ANALYSIS
# --------------------------------------------------

analysis_records = []


for _, row in df.iterrows():

    after_text = str(
        row.get(
            "attribution_after",
            ""
        )
    )

    before_text = str(
        row.get(
            "attribution_before",
            ""
        )
    )

    speaker_after = extract_after_speaker(
        after_text
    )

    speaker_before = extract_before_speaker(
        before_text
    )

    # --------------------------------------------------
    # ATTRIBUTION CLASS
    # --------------------------------------------------

    if speaker_after:
        attribution_class = (
            "DIRECT_SPEAKER_AFTER"
        )

    elif speaker_before:
        attribution_class = (
            "DIRECT_SPEAKER_BEFORE"
        )

    elif (
        row.get(
            "has_speech_verb_after",
            False
        )
        or row.get(
            "has_speech_verb_before",
            False
        )
    ):
        attribution_class = (
            "SPEECH_VERB_WITHOUT_CLEAR_SPEAKER"
        )

    else:
        attribution_class = (
            "NO_CLEAR_ATTRIBUTION"
        )

    # --------------------------------------------------
    # PRELIMINARY CONFIDENCE
    # --------------------------------------------------

    if (
        speaker_after
        and speaker_before
        and speaker_after.lower()
        != speaker_before.lower()
    ):
        confidence = "REVIEW"

    elif speaker_after or speaker_before:
        confidence = "HIGH"

    elif (
        row.get(
            "has_speech_verb_after",
            False
        )
        or row.get(
            "has_speech_verb_before",
            False
        )
    ):
        confidence = "MEDIUM"

    else:
        confidence = "LOW"

    analysis_records.append(
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
            "attribution_after": (
                after_text
            ),
            "attribution_before": (
                before_text
            ),
            "speaker_after": (
                speaker_after
            ),
            "speaker_before": (
                speaker_before
            ),
            "attribution_class": (
                attribution_class
            ),
            "preliminary_confidence": (
                confidence
            ),
            "context_before": row[
                "context_before"
            ],
            "context_after": row[
                "context_after"
            ],
        }
    )


analysis_df = pd.DataFrame(
    analysis_records
)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

analysis_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("ATTRIBUTION SUMMARY")
print("-------------------")

print(
    f"Total candidates: "
    f"{len(analysis_df):,}"
)

print()

print(
    analysis_df[
        "attribution_class"
    ].value_counts(
        dropna=False
    )
)

print()

print("CONFIDENCE SUMMARY")
print("------------------")

print(
    analysis_df[
        "preliminary_confidence"
    ].value_counts(
        dropna=False
    )
)

print()

# --------------------------------------------------
# SPEAKER COUNTS
# --------------------------------------------------

print("TOP DETECTED SPEAKERS")
print("---------------------")

speaker_series = (
    analysis_df[
        "speaker_after"
    ]
    .replace("", pd.NA)
    .dropna()
)

print(
    speaker_series.value_counts()
    .head(30)
)

print()

# --------------------------------------------------
# REVIEW CASES
# --------------------------------------------------

print("REVIEW CASES")
print("------------")

review_df = analysis_df[
    analysis_df[
        "preliminary_confidence"
    ] == "REVIEW"
]

print(
    f"Review cases: "
    f"{len(review_df):,}"
)

print()

for _, row in review_df.head(30).iterrows():

    preview = " ".join(
        str(
            row["quoted_text"]
        ).split()
    )

    if len(preview) > 250:
        preview = (
            preview[:250]
            + "..."
        )

    print(
        f"{row['candidate_id']}: "
        f'"{preview}"'
    )

    print(
        f"  AFTER SPEAKER: "
        f"{row['speaker_after']}"
    )

    print(
        f"  BEFORE SPEAKER: "
        f"{row['speaker_before']}"
    )

    print()

print(
    "SPEAKER-ATTRIBUTION ANALYSIS COMPLETE."
)