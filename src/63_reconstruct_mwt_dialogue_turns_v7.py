import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_attribution_context_resolved.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/"
    "the_man_who_was_thursday_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v7.csv"
)


# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

df = df.sort_values(
    "start_char"
).reset_index(
    drop=True
)


print(
    "MWT dialogue turn reconstruction V7"
)

print(
    "=================================="
)

print()

print(
    f"Candidate spans: {len(df):,}"
)

print()


# =========================================================
# HELPERS
# =========================================================

def normalize_space(text):

    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def speaker_value(row):

    value = str(
        row["resolved_speaker"]
    ).strip()

    if (
        not value
        or value.lower() == "unknown"
    ):

        return "Unknown"

    return normalize_space(
        value
    )


def resolution_confidence(row):

    value = str(
        row["resolution_confidence"]
    ).strip().lower()

    if value in {
        "high",
        "medium",
        "review"
    }:

        return value

    return "review"


def attribution_type(row):

    return str(
        row["attribution_type"]
    ).strip()


def speaker_evidence(row):

    return str(
        row["speaker_evidence"]
    ).strip()


def has_own_attribution(row):

    """
    IMPORTANT:

    If the candidate itself has an attribution after it,
    that attribution belongs to THIS candidate.

    Therefore the next candidate normally starts a new
    quotation fragment / turn.
    """

    return attribution_type(row) in {
        "named_speaker",
        "role_speaker",
        "pronoun_speaker",
        "pronoun_speaker_named_target",
        "unresolved_attribution"
    }


def is_narrative_quote(row):

    return (
        attribution_type(row)
        == "narrative_quote"
    )


def gap_between(row_a, row_b):

    end_a = int(
        row_a["end_char"]
    )

    start_b = int(
        row_b["start_char"]
    )

    if start_b <= end_a:

        return ""

    return normalize_space(
        clean_text[
            end_a:start_b
        ]
    )


# =========================================================
# CONTINUATION TEST
# =========================================================

def continuation_evidence(
    previous_row,
    next_row
):

    """
    Conservative continuation rule.

    The NEXT candidate must NOT have its own attribution.

    This prevents errors such as:

        C00006 -> C00007

    where C00007 is independently attributed to Gregory.

    """

    # -----------------------------------------------------
    # Critical boundary rule
    # -----------------------------------------------------

    if has_own_attribution(
        next_row
    ):

        return (
            False,
            "next_candidate_has_own_attribution"
        )


    # -----------------------------------------------------
    # Narrative quote
    # -----------------------------------------------------

    if is_narrative_quote(
        previous_row
    ):

        return (
            False,
            "previous_candidate_is_narrative_quote"
        )


    # -----------------------------------------------------
    # Gap
    # -----------------------------------------------------

    gap = gap_between(
        previous_row,
        next_row
    )

    previous_text = normalize_space(
        previous_row["quoted_text"]
    )

    next_text = normalize_space(
        next_row["quoted_text"]
    )


    # -----------------------------------------------------
    # Explicit continuation language
    # -----------------------------------------------------

    if re.search(
        r"\bcontinued\b"
        r"|\bwent on\b"
        r"|\bresumed\b"
        r"|\badded\b"
        r"|\bthen he said\b"
        r"|\bthen she said\b"
        r"|\bhe added\b"
        r"|\bshe added\b",
        gap,
        flags=re.IGNORECASE
    ):

        return (
            True,
            "explicit_continuation_language"
        )


    # -----------------------------------------------------
    # Unfinished quotation + short attribution gap
    #
    # Examples:
    #
    # "Only in that sense I speak of," replied Syme;
    # "or if you prefer it..."
    #
    # "I tell you," went on Syme...
    # "that every time..."
    # -----------------------------------------------------

    unfinished = previous_text.endswith(
        (
            ",",
            ";",
            ":",
            "—",
            "–",
            "..."
        )
    )


    if unfinished:

        if len(gap) <= 120:

            # A lowercase beginning is particularly strong.
            if next_text:

                if next_text[0].islower():

                    return (
                        True,
                        "unfinished_quote_lowercase_continuation"
                    )

            # Even without lowercase, a short gap after an
            # explicitly attributed quotation can indicate
            # interrupted speech.
            return (
                True,
                "unfinished_quote_short_gap"
            )


    # -----------------------------------------------------
    # Lowercase continuation
    # -----------------------------------------------------

    if next_text:

        if next_text[0].islower():

            if len(gap) <= 100:

                return (
                    True,
                    "lowercase_continuation"
                )


    # -----------------------------------------------------
    # Default
    # -----------------------------------------------------

    return (
        False,
        "insufficient_continuation_evidence"
    )


# =========================================================
# BUILD TURNS
# =========================================================

turns = []

current = []

turn_number = 0


def finalize_turn():

    global turn_number
    global current

    if not current:

        return

    turn_number += 1

    candidate_ids = [
        str(
            row["candidate_id"]
        )
        for row in current
    ]

    quoted_parts = [
        normalize_space(
            row["quoted_text"]
        )
        for row in current
    ]

    speakers = [
        speaker_value(row)
        for row in current
    ]

    confidences = [
        resolution_confidence(row)
        for row in current
    ]


    # -----------------------------------------------------
    # Determine speaker
    # -----------------------------------------------------

    known_speakers = [
        s
        for s in speakers
        if s != "Unknown"
    ]


    if known_speakers:

        # Use the first known speaker.
        #
        # A later audit will detect conflicts if multiple
        # different speakers occur inside one turn.
        speaker = known_speakers[0]

    else:

        speaker = "Unknown"


    # -----------------------------------------------------
    # Speaker confidence
    # -----------------------------------------------------

    if speaker == "Unknown":

        speaker_confidence = "review"

    elif all(
        c == "high"
        for c in confidences
    ):

        speaker_confidence = "high"

    elif any(
        c == "review"
        for c in confidences
    ):

        speaker_confidence = "review"

    else:

        speaker_confidence = "medium"


    # -----------------------------------------------------
    # Extraction confidence
    # -----------------------------------------------------

    if speaker == "Unknown":

        extraction_confidence = "review"

    elif all(
        c == "high"
        for c in confidences
    ):

        extraction_confidence = "high"

    elif any(
        c == "review"
        for c in confidences
    ):

        extraction_confidence = "review"

    else:

        extraction_confidence = "medium"


    # -----------------------------------------------------
    # Detect conflicting speakers
    # -----------------------------------------------------

    unique_known = sorted(
        set(known_speakers)
    )

    if len(unique_known) > 1:

        boundary_confidence = "review"

        boundary_reason = (
            "speaker_conflict_inside_turn"
        )

    else:

        boundary_confidence = (
            "high"
            if len(current) > 1
            else "review"
        )

        if len(current) > 1:

            boundary_reason = (
                "confirmed_interrupted_speech_continuation"
            )

        else:

            boundary_reason = (
                "single_candidate_turn"
            )


    # -----------------------------------------------------
    # Character span
    # -----------------------------------------------------

    start_char = int(
        current[0]["start_char"]
    )

    end_char = int(
        current[-1]["end_char"]
    )


    turns.append({

        "turn_id":
            f"MWT_T{turn_number:05d}",

        "candidate_ids":
            "|".join(candidate_ids),

        "start_char":
            start_char,

        "end_char":
            end_char,

        "speaker":
            speaker,

        "speaker_confidence":
            speaker_confidence,

        "extraction_confidence":
            extraction_confidence,

        "boundary_confidence":
            boundary_confidence,

        "boundary_reason":
            boundary_reason,

        "quoted_text":
            " ".join(
                quoted_parts
            )
    })


    current = []


# =========================================================
# MAIN RECONSTRUCTION
# =========================================================

for i, row in df.iterrows():

    # -----------------------------------------------------
    # Narrative quote
    # -----------------------------------------------------

    if is_narrative_quote(row):

        finalize_turn()

        continue


    # -----------------------------------------------------
    # First candidate
    # -----------------------------------------------------

    if not current:

        current = [
            row
        ]

        continue


    previous = current[-1]


    # -----------------------------------------------------
    # Test continuation
    # -----------------------------------------------------

    merge, reason = continuation_evidence(
        previous,
        row
    )


    if merge:

        current.append(
            row
        )

    else:

        finalize_turn()

        current = [
            row
        ]


# =========================================================
# FINAL TURN
# =========================================================

finalize_turn()


# =========================================================
# DATAFRAME
# =========================================================

out = pd.DataFrame(
    turns
)


# =========================================================
# SAVE
# =========================================================

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# SUMMARY
# =========================================================

print(
    "RECONSTRUCTION SUMMARY"
)

print(
    "----------------------"
)

print(
    f"Candidate spans: "
    f"{len(df):,}"
)

print(
    f"Reconstructed turns: "
    f"{len(out):,}"
)

print()


print(
    "SPEAKER COUNTS"
)

print(
    "--------------"
)

print(
    out[
        "speaker"
    ]
    .value_counts()
    .head(30)
    .to_string()
)

print()


print(
    "SPEAKER CONFIDENCE"
)

print(
    "------------------"
)

print(
    out[
        "speaker_confidence"
    ]
    .value_counts()
    .to_string()
)

print()


print(
    "EXTRACTION CONFIDENCE"
)

print(
    "---------------------"
)

print(
    out[
        "extraction_confidence"
    ]
    .value_counts()
    .to_string()
)

print()


print(
    "BOUNDARY CONFIDENCE"
)

print(
    "-------------------"
)

print(
    out[
        "boundary_confidence"
    ]
    .value_counts()
    .to_string()
)

print()


print(
    "TURN SIZE"
)

print(
    "---------"
)

sizes = (
    out["candidate_ids"]
    .str.count(r"\|")
    + 1
)

print(
    sizes.value_counts()
    .sort_index()
    .to_string()
)

print()


# =========================================================
# FIRST 50
# =========================================================

print(
    "FIRST 50 RECONSTRUCTED TURNS"
)

print(
    "----------------------------"
)

for _, row in out.head(50).iterrows():

    text = normalize_space(
        row["quoted_text"]
    )

    if len(text) > 200:

        text = (
            text[:200]
            + "..."
        )

    print()

    print(
        f'{row["turn_id"]} | '
        f'{row["speaker"]} | '
        f'{row["speaker_confidence"]} | '
        f'{row["candidate_ids"]}'
    )

    print(
        f'  {text}'
    )


print()

print(
    "V7 reconstruction complete."
)

print(
    f"Output: {OUTPUT_FILE}"
)