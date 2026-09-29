import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

RESOLVED_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_attribution_context_resolved.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/"
    "the_man_who_was_thursday_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v6.csv"
)


# =========================================================
# HELPERS
# =========================================================

def normalize_space(text):
    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def is_unknown(value):
    return (
        pd.isna(value)
        or str(value).strip() == ""
        or str(value).strip().lower()
        == "unknown"
    )


def speaker_value(row):

    value = row["resolved_speaker"]

    if is_unknown(value):
        return "Unknown"

    return normalize_space(value)


def confidence_value(row):

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


# =========================================================
# LOAD
# =========================================================

print(
    "MWT dialogue turn reconstruction V6"
)

print(
    "=================================="
)

print()

df = pd.read_csv(
    RESOLVED_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

df = df.sort_values(
    ["start_char", "end_char"]
).reset_index(
    drop=True
)

print(
    f"Candidate rows: {len(df):,}"
)

print()


# =========================================================
# TURN RECONSTRUCTION PRINCIPLE
#
# We do NOT assume:
#
#   current speaker == previous speaker
#
# and we do NOT assume:
#
#   attribution after quote belongs to next quote.
#
# A candidate is anchored by its own attribution evidence.
#
# Unattributed candidates can join the immediately
# preceding candidate when there is evidence that the
# speech continues.
# =========================================================


# =========================================================
# ATTRIBUTION / BOUNDARY HELPERS
# =========================================================

def attribution_is_strong(row):

    return str(
        row["speaker_evidence"]
    ) in {
        "named_speaker",
        "role_speaker"
    }


def attribution_is_pronoun(row):

    return str(
        row["speaker_evidence"]
    ) == "pronoun_speaker"


def attribution_is_none(row):

    return str(
        row["speaker_evidence"]
    ) == "none"


def attribution_is_narrative(row):

    return str(
        row["attribution_type"]
    ) == "narrative_quote"


def explicit_speaker(row):

    speaker = speaker_value(
        row
    )

    if speaker != "Unknown":
        return speaker

    return None


def same_known_speaker(a, b):

    if a is None or b is None:
        return False

    if a == "Unknown" or b == "Unknown":
        return False

    return a == b


# =========================================================
# DETERMINE WHETHER A GAP LOOKS LIKE A CONTINUATION
# =========================================================

def gap_between(row_a, row_b):

    start_a = int(
        row_a["end_char"]
    )

    start_b = int(
        row_b["start_char"]
    )

    if start_b <= start_a:
        return ""

    gap = clean_text[
        start_a:start_b
    ]

    return normalize_space(
        gap
    )


def continuation_signal(
    previous_row,
    current_row
):

    """
    Return:
        True / False
        reason

    Conservative rule.

    We only merge an unattributed candidate into the
    previous candidate when the source structure strongly
    suggests that the speech continues.

    We do NOT merge merely because:
        - there is no attribution
        - the previous speaker is known
        - the previous candidate was dialogue
    """

    gap = gap_between(
        previous_row,
        current_row
    )

    prev_text = str(
        previous_row["quoted_text"]
    ).strip()

    curr_text = str(
        current_row["quoted_text"]
    ).strip()


    # -----------------------------------------------------
    # If there is explicit attribution immediately after
    # the previous quotation, that attribution identifies
    # the previous quotation.
    #
    # It does NOT authorize merging the next quotation.
    # -----------------------------------------------------

    previous_type = str(
        previous_row["attribution_type"]
    )

    if previous_type in {
        "named_speaker",
        "role_speaker",
        "pronoun_speaker",
        "pronoun_speaker_named_target",
        "unresolved_attribution"
    }:

        # An explicit attribution generally closes the
        # evidence unit unless the gap explicitly signals
        # continuation.
        #
        # We look for continuation language such as:
        # "he continued"
        # "she continued"
        # "he went on"
        # "she added"
        # "he resumed"
        #
        # This must refer to the SAME speaker.

        continuation_patterns = [
            r"\bcontinued\b",
            r"\bwent on\b",
            r"\bresumed\b",
            r"\bcontinued to say\b",
            r"\bwent on to say\b",
            r"\badded\b",
            r"\bthen he said\b",
            r"\bthen she said\b",
            r"\bhe added\b",
            r"\bshe added\b",
        ]

        for pattern in continuation_patterns:

            if re.search(
                pattern,
                gap,
                flags=re.IGNORECASE
            ):

                return (
                    True,
                    "explicit_continuation_language"
                )

        return (
            False,
            "previous_attribution_closes_fragment"
        )


    # -----------------------------------------------------
    # Narrative quote
    # -----------------------------------------------------

    if attribution_is_narrative(
        previous_row
    ):

        return (
            False,
            "narrative_quote"
        )


    # -----------------------------------------------------
    # If current candidate itself has explicit speaker
    # attribution, it starts a new evidence unit.
    # -----------------------------------------------------

    if (
        attribution_is_strong(
            current_row
        )
        or attribution_is_pronoun(
            current_row
        )
    ):

        return (
            False,
            "current_candidate_has_attribution"
        )


    # -----------------------------------------------------
    # Blank / tiny gap can sometimes indicate continuation,
    # but we do NOT merge automatically.
    #
    # Look for punctuation that strongly indicates an
    # unfinished quotation.
    # -----------------------------------------------------

    if prev_text.endswith(
        (
            ",",
            ";",
            ":",
            "—",
            "–",
            "..."
        )
    ):

        # A very small gap is stronger evidence.
        if len(gap) <= 80:

            return (
                True,
                "unfinished_quote_with_short_gap"
            )


    # -----------------------------------------------------
    # Current quote beginning with lower-case text is a
    # useful continuation signal.
    # -----------------------------------------------------

    if curr_text:

        first_char = curr_text[0]

        if first_char.islower():

            if len(gap) <= 100:

                return (
                    True,
                    "lowercase_continuation"
                )


    # -----------------------------------------------------
    # Default: do not merge.
    # -----------------------------------------------------

    return (
        False,
        "insufficient_continuation_evidence"
    )


# =========================================================
# RECONSTRUCT TURNS
# =========================================================

turns = []

current_candidates = []

current_speaker = "Unknown"

current_speaker_confidence = "review"

current_boundary_reason = ""

turn_number = 0


def finalize_current_turn():

    global current_candidates
    global current_speaker
    global current_speaker_confidence
    global current_boundary_reason
    global turn_number

    if not current_candidates:
        return

    turn_number += 1

    quoted_parts = []

    candidate_ids = []

    start_char = None

    end_char = None

    confidence_values = []

    for item in current_candidates:

        quoted_parts.append(
            str(item["quoted_text"])
        )

        candidate_ids.append(
            str(item["candidate_id"])
        )

        confidence_values.append(
            confidence_value(item)
        )

        if start_char is None:
            start_char = int(
                item["start_char"]
            )

        end_char = int(
            item["end_char"]
        )

    # -----------------------------------------------------
    # Determine aggregate confidence.
    #
    # High only when all evidence used for the turn
    # is high/direct.
    # -----------------------------------------------------

    if current_speaker == "Unknown":

        aggregate_confidence = "review"

    elif all(
        x == "high"
        for x in confidence_values
    ):

        aggregate_confidence = "high"

    elif any(
        x == "review"
        for x in confidence_values
    ):

        aggregate_confidence = "review"

    else:

        aggregate_confidence = "medium"


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
            current_speaker,

        "speaker_confidence":
            current_speaker_confidence,

        "extraction_confidence":
            aggregate_confidence,

        "boundary_reason":
            current_boundary_reason,

        "quoted_text":
            " ".join(
                quoted_parts
            )
    })


# =========================================================
# MAIN LOOP
# =========================================================

for i, row in df.iterrows():

    # -----------------------------------------------------
    # Skip known narrative quote
    # -----------------------------------------------------

    if attribution_is_narrative(
        row
    ):

        # Close any existing dialogue turn.
        finalize_current_turn()

        current_candidates = []

        current_speaker = "Unknown"

        current_speaker_confidence = "review"

        current_boundary_reason = (
            "narrative_quote_excluded"
        )

        continue


    row_speaker = explicit_speaker(
        row
    )

    row_is_pronoun = (
        attribution_is_pronoun(
            row
        )
    )

    row_has_explicit_speaker = (
        row_speaker is not None
    )


    # =====================================================
    # FIRST CANDIDATE
    # =====================================================

    if not current_candidates:

        current_candidates = [
            row
        ]

        if row_speaker is not None:

            current_speaker = (
                row_speaker
            )

            current_speaker_confidence = (
                confidence_value(row)
            )

        else:

            current_speaker = "Unknown"

            current_speaker_confidence = (
                "review"
            )

        current_boundary_reason = (
            "new_turn"
        )

        continue


    # =====================================================
    # CURRENT TURN EXISTS
    # =====================================================

    previous_row = current_candidates[-1]

    previous_speaker = current_speaker


    # -----------------------------------------------------
    # Current candidate has a known explicit speaker.
    #
    # It must not be merged with previous turn unless
    # the same speaker is explicitly established and
    # continuation evidence exists.
    # -----------------------------------------------------

    if row_has_explicit_speaker:

        if same_known_speaker(
            previous_speaker,
            row_speaker
        ):

            merge, reason = continuation_signal(
                previous_row,
                row
            )

            if merge:

                current_candidates.append(
                    row
                )

                current_boundary_reason = (
                    reason
                )

                continue


        # Different / independently attributed speaker.
        finalize_current_turn()

        current_candidates = [
            row
        ]

        current_speaker = (
            row_speaker
        )

        current_speaker_confidence = (
            confidence_value(row)
        )

        current_boundary_reason = (
            "new_explicit_speaker"
        )

        continue


    # -----------------------------------------------------
    # Current candidate has pronoun attribution.
    #
    # If Script 60 resolved it, use that speaker.
    # -----------------------------------------------------

    if row_is_pronoun:

        resolved = speaker_value(
            row
        )

        if resolved != "Unknown":

            if same_known_speaker(
                previous_speaker,
                resolved
            ):

                merge, reason = continuation_signal(
                    previous_row,
                    row
                )

                if merge:

                    current_candidates.append(
                        row
                    )

                    current_boundary_reason = (
                        reason
                    )

                    continue


            # Otherwise this is a new speaker turn.
            finalize_current_turn()

            current_candidates = [
                row
            ]

            current_speaker = (
                resolved
            )

            current_speaker_confidence = (
                confidence_value(row)
            )

            current_boundary_reason = (
                "new_context_resolved_speaker"
            )

            continue


        # -------------------------------------------------
        # Pronoun unresolved.
        #
        # Do NOT inherit previous speaker.
        # -------------------------------------------------

        finalize_current_turn()

        current_candidates = [
            row
        ]

        current_speaker = "Unknown"

        current_speaker_confidence = "review"

        current_boundary_reason = (
            "unresolved_pronoun"
        )

        continue


    # =====================================================
    # CURRENT CANDIDATE HAS NO ATTRIBUTION
    # =====================================================

    merge, reason = continuation_signal(
        previous_row,
        row
    )


    if merge:

        # Only merge when previous speaker is known.
        if current_speaker != "Unknown":

            current_candidates.append(
                row
            )

            current_boundary_reason = (
                reason
            )

            continue


    # -----------------------------------------------------
    # Otherwise create a new unresolved turn.
    #
    # IMPORTANT:
    # We do NOT inherit the previous speaker.
    # -----------------------------------------------------

    finalize_current_turn()

    current_candidates = [
        row
    ]

    current_speaker = "Unknown"

    current_speaker_confidence = "review"

    current_boundary_reason = (
        "unattributed_candidate_requires_review"
    )


# =========================================================
# FINALIZE
# =========================================================

finalize_current_turn()


# =========================================================
# SAVE
# =========================================================

out = pd.DataFrame(
    turns
)

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
    "BOUNDARY REASONS"
)

print(
    "----------------"
)

print(
    out[
        "boundary_reason"
    ]
    .value_counts()
    .to_string()
)

print()


# =========================================================
# FIRST 50 TURNS
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

    if len(text) > 180:

        text = (
            text[:180]
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
        f"  {text}"
    )


print()

print(
    "V6 reconstruction complete."
)

print(
    f"Output: {OUTPUT_FILE}"
)