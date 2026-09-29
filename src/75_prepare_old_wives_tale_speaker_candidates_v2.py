from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v2.csv"
)


print("Preparing stricter speaker candidates")
print("======================================")
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
# KNOWN SPEECH VERBS
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


# --------------------------------------------------
# PRONOUNS
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


# --------------------------------------------------
# WORDS THAT STRONGLY INDICATE NARRATION
# --------------------------------------------------

narrative_markers = {
    "then",
    "and",
    "but",
    "this",
    "that",
    "these",
    "those",
    "she",
    "he",
    "they",
    "it",
    "which",
    "who",
    "when",
    "while",
    "because",
    "after",
    "before",
    "though",
    "although",
    "as",
    "was",
    "were",
    "had",
    "has",
    "have",
    "began",
    "started",
    "looked",
    "turned",
    "went",
    "came",
    "moved",
    "stood",
    "sat",
    "walked",
    "smiled",
    "laughed",
    "cried",
    "thought",
    "felt",
    "knew",
    "saw",
    "heard",
    "told",
    "asked",
    "said",
    "added",
}


# --------------------------------------------------
# NORMALIZE
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

    value = re.sub(
        r"[.!?,;:]+$",
        "",
        value
    )

    return value.strip()


# --------------------------------------------------
# CHECK WHETHER A LABEL IS A CLEAN PERSON NAME
# --------------------------------------------------

def is_clean_named_person(value):

    value = normalize(value)

    if not value:
        return False

    lower = value.lower()

    # Never accept pronouns.
    if lower in pronouns:
        return False

    # Reject obvious sentence continuation.
    words = lower.split()

    if any(
        word in narrative_markers
        for word in words[1:]
    ):
        return False

    # Reject overly long labels.
    if len(words) > 4:
        return False

    if len(value) > 50:
        return False

    # Titles.
    if re.fullmatch(
        r"(?:Mr\.|Mrs\.|Miss|Dr\.)\s+[A-Z][A-Za-z.'-]*",
        value
    ):
        return True

    # Two-word proper name.
    if re.fullmatch(
        r"[A-Z][A-Za-z.'-]*\s+[A-Z][A-Za-z.'-]*",
        value
    ):
        return True

    # Single proper name.
    if re.fullmatch(
        r"[A-Z][A-Za-z.'-]*",
        value
    ):
        return True

    # Hyphenated surname/name.
    if re.fullmatch(
        r"[A-Z][A-Za-z.'-]*-[A-Z][A-Za-z.'-]*",
        value
    ):
        return True

    return False


# --------------------------------------------------
# CHECK DESCRIPTIVE SPEAKER
# --------------------------------------------------

def is_safe_descriptive_speaker(value):

    value = normalize(value)

    if not value:
        return False

    lower = value.lower()
    words = lower.split()

    # Too long -> almost certainly surrounding narration.
    if len(words) > 5:
        return False

    if len(value) > 55:
        return False

    # Reject obvious narration continuations.
    if any(
        word in narrative_markers
        for word in words[1:]
    ):
        return False

    # Certain descriptive forms are unsafe.
    unsafe_phrases = {
        "the top of her head",
        "the ceiling",
        "the tone in which she",
        "the commonsense of mr. povey",
        "the old man from the",
        "the great daniel",
        "the assistant",
        "the auctioneer",
    }

    if lower in unsafe_phrases:
        return False

    # Accept concise descriptive labels.
    if lower.startswith("the "):
        return True

    return False


# --------------------------------------------------
# PROCESS
# --------------------------------------------------

records = []


for _, row in df.iterrows():

    after = normalize(
        row["speaker_after_normalized"]
    )

    before = normalize(
        row["speaker_before_normalized"]
    )

    proposed = "Unknown"
    source = "NO_RECOVERABLE_SPEAKER"
    status = "UNKNOWN_REVIEW"

    # ----------------------------------------------
    # AFTER-QUOTE CLEAN NAME
    # ----------------------------------------------

    if is_clean_named_person(after):

        proposed = after
        source = "AFTER_QUOTE_CLEAN_NAMED"
        status = "ATTRIBUTED_DIALOGUE_CANDIDATE"

    # ----------------------------------------------
    # BEFORE-QUOTE CLEAN NAME
    # ----------------------------------------------

    elif is_clean_named_person(before):

        proposed = before
        source = "BEFORE_QUOTE_CLEAN_NAMED"
        status = "ATTRIBUTED_DIALOGUE_CANDIDATE"

    # ----------------------------------------------
    # SAFE DESCRIPTIVE LABEL
    # ----------------------------------------------

    elif is_safe_descriptive_speaker(after):

        proposed = after
        source = "AFTER_QUOTE_SAFE_DESCRIPTIVE"
        status = "ATTRIBUTED_DIALOGUE_CANDIDATE"

    elif is_safe_descriptive_speaker(before):

        proposed = before
        source = "BEFORE_QUOTE_SAFE_DESCRIPTIVE"
        status = "ATTRIBUTED_DIALOGUE_CANDIDATE"

    # ----------------------------------------------
    # PRONOUN
    # ----------------------------------------------

    elif after.lower() in pronouns:

        proposed = "Unknown"
        source = "PRONOUN_AFTER_REQUIRES_CONTEXT"
        status = "PRONOUN_DIALOGUE_REVIEW"

    elif before.lower() in pronouns:

        proposed = "Unknown"
        source = "PRONOUN_BEFORE_REQUIRES_CONTEXT"
        status = "PRONOUN_DIALOGUE_REVIEW"

    # ----------------------------------------------
    # SPEECH VERB BUT NO SAFE SPEAKER
    # ----------------------------------------------

    elif (
        bool(row["speaker_after_normalized"])
        or bool(row["speaker_before_normalized"])
    ):

        proposed = "Unknown"
        source = "ATTRIBUTION_REQUIRES_REVIEW"
        status = "SPEAKER_REVIEW"

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

        "speaker_after_normalized":
            after,

        "speaker_before_normalized":
            before,

        "proposed_speaker":
            proposed,

        "attribution_source":
            source,

        "candidate_status":
            status,

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
    ].value_counts().head(50)
)

print()


# --------------------------------------------------
# REVIEW CASES
# --------------------------------------------------

review = out[
    out["candidate_status"]
    == "SPEAKER_REVIEW"
]

print(
    f"SPEAKER REVIEW CASES: "
    f"{len(review):,}"
)

print()


print("SAMPLE SPEAKER REVIEW CASES")
print("---------------------------")

for _, row in review.head(50).iterrows():

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
        f'{row["candidate_id"]}: '
        f'"{preview}"'
    )

    print(
        f'  After: '
        f'{row["speaker_after_raw"]}'
    )

    print(
        f'  Before: '
        f'{row["speaker_before_raw"]}'
    )

    print()


print("OUTPUT")
print("------")
print(OUTPUT_FILE)
print()

print(
    "STRICT SPEAKER CANDIDATE "
    "PREPARATION COMPLETE."
)