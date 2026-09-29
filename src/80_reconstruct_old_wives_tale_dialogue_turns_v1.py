from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v5.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_turns_v1.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_turn_audit_v1.csv"
)


print("Reconstructing dialogue turns")
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


# --------------------------------------------------
# BASIC PREPARATION
# --------------------------------------------------

df = df.sort_values(
    "candidate_id"
).reset_index(drop=True)


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_unknown(speaker):
    return (
        speaker == ""
        or speaker.lower() == "unknown"
        or speaker.lower() == "nan"
    )


def normalize_speaker(value):
    value = clean_text(value)

    if not value:
        return "Unknown"

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


df["speaker"] = (
    df["speaker_before"]
    .apply(normalize_speaker)
)


# --------------------------------------------------
# CANDIDATE FILTER
# --------------------------------------------------
#
# We deliberately use only candidates that survived
# the speaker-candidate preparation stage.
#
# Unknown/review candidates remain available for
# audit but are NOT silently assigned to a speaker.
# --------------------------------------------------

usable = df[
    df["candidate_status"].isin(
        [
            "ATTRIBUTED_DIALOGUE_CANDIDATE",
            "PRONOUN_DIALOGUE_REVIEW",
        ]
    )
].copy()


print("INPUT SUMMARY")
print("-------------")
print(
    f"All candidate rows: {len(df):,}"
)
print(
    f"Usable dialogue candidates: {len(usable):,}"
)
print()


# --------------------------------------------------
# TURN RECONSTRUCTION
# --------------------------------------------------
#
# Conservative policy:
#
# 1. Every named-speaker candidate can start a turn.
# 2. Unknown/pronoun candidates are retained as
#    review turns rather than guessing a speaker.
# 3. A candidate with an explicit named speaker is
#    never merged into a previous different speaker.
# 4. Consecutive candidates with the same speaker may
#    be merged only when there is no clear new speaker
#    boundary in the intervening text.
#
# Because the candidate layer does not yet contain a
# fully reliable paragraph-level continuation model,
# we prefer splitting rather than falsely merging.
# --------------------------------------------------


turn_rows = []
audit_rows = []


current_turn = None
turn_number = 0


def start_turn(row):
    global turn_number

    turn_number += 1

    speaker = normalize_speaker(
        row["speaker"]
    )

    if is_unknown(speaker):
        speaker = "Unknown"

    turn_id = (
        f"OWT_T{turn_number:05d}"
    )

    return {
        "turn_id": turn_id,
        "candidate_id": row["candidate_id"],
        "speaker": speaker,
        "quoted_text": clean_text(
            row["quoted_text"]
        ),
        "start_char": row["start_char"],
        "end_char": row["end_char"],
        "speaker_confidence": (
            "review"
            if speaker == "Unknown"
            else "high"
        ),
        "extraction_confidence": (
            "review"
        ),
        "candidate_status": (
            row["candidate_status"]
        ),
        "attribution_source": (
            row["attribution_source"]
        ),
        "candidate_count": 1,
        "turn_boundary_reason": (
            "NEW_EXPLICIT_CANDIDATE"
            if speaker != "Unknown"
            else "UNKNOWN_SPEAKER_REVIEW"
        ),
    }


def finalize_turn(turn):
    if turn is None:
        return

    turn_rows.append(turn)


for _, row in usable.iterrows():

    speaker = normalize_speaker(
        row["speaker"]
    )

    if is_unknown(speaker):

        # Unknown/pronoun attribution gets its own
        # review turn. We do not guess the identity.
        finalize_turn(current_turn)

        current_turn = start_turn(row)

        audit_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "turn_id": current_turn["turn_id"],
                "decision": "SEPARATE_REVIEW_TURN",
                "reason": "UNKNOWN_OR_PRONOUN_ATTRIBUTION",
                "speaker": "Unknown",
            }
        )

        continue


    # --------------------------------------------------
    # Named speaker
    # --------------------------------------------------

    if current_turn is None:

        current_turn = start_turn(row)

        audit_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "turn_id": current_turn["turn_id"],
                "decision": "START_NEW_TURN",
                "reason": "FIRST_NAMED_SPEAKER",
                "speaker": speaker,
            }
        )

        continue


    previous_speaker = (
        current_turn["speaker"]
    )


    # --------------------------------------------------
    # Same speaker
    # --------------------------------------------------

    if (
        previous_speaker == speaker
        and previous_speaker != "Unknown"
    ):

        # Conservative rule:
        # keep separate candidate turns rather than
        # automatically concatenating quoted spans.
        finalize_turn(current_turn)

        current_turn = start_turn(row)

        current_turn[
            "turn_boundary_reason"
        ] = "SAME_SPEAKER_NEW_QUOTED_CANDIDATE"

        audit_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "turn_id": current_turn["turn_id"],
                "decision": "SEPARATE_SAME_SPEAKER",
                "reason": (
                    "CONSERVATIVE_NO_AUTOMATIC_MERGE"
                ),
                "speaker": speaker,
            }
        )

        continue


    # --------------------------------------------------
    # Different speaker
    # --------------------------------------------------

    finalize_turn(current_turn)

    current_turn = start_turn(row)

    current_turn[
        "turn_boundary_reason"
    ] = "NEW_EXPLICIT_SPEAKER"

    audit_rows.append(
        {
            "candidate_id": row["candidate_id"],
            "turn_id": current_turn["turn_id"],
            "decision": "START_NEW_TURN",
            "reason": "NEW_EXPLICIT_SPEAKER",
            "speaker": speaker,
        }
    )


# finalize last turn
finalize_turn(current_turn)


# --------------------------------------------------
# BUILD DATAFRAME
# --------------------------------------------------

turns = pd.DataFrame(
    turn_rows
)

audit = pd.DataFrame(
    audit_rows
)


# --------------------------------------------------
# STABLE TURN ORDER
# --------------------------------------------------

if not turns.empty:

    turns = turns.reset_index(
        drop=True
    )

    turns["turn_index"] = (
        turns.index + 1
    )


# --------------------------------------------------
# STRUCTURAL AUDIT
# --------------------------------------------------

print("TURN RECONSTRUCTION SUMMARY")
print("---------------------------")

print(
    f"Dialogue turns: {len(turns):,}"
)

print(
    f"Unique speakers: "
    f"{turns['speaker'].nunique():,}"
)

print()

print("SPEAKER COUNTS")
print("--------------")

print(
    turns["speaker"]
    .value_counts()
    .head(50)
)

print()


print("TURN SIZE COUNTS")
print("----------------")

print(
    turns["candidate_count"]
    .value_counts()
    .sort_index()
)

print()


# --------------------------------------------------
# UNKNOWN COUNT
# --------------------------------------------------

unknown_count = (
    turns["speaker"]
    .eq("Unknown")
    .sum()
)

print(
    f"Unknown/review turns: "
    f"{unknown_count:,}"
)

print()


# --------------------------------------------------
# DUPLICATE TURN IDS
# --------------------------------------------------

duplicate_turn_ids = (
    turns["turn_id"]
    .duplicated()
    .sum()
)

print(
    "Duplicate turn IDs:",
    duplicate_turn_ids
)


# --------------------------------------------------
# DUPLICATE CANDIDATE IDS
# --------------------------------------------------

duplicate_candidate_ids = (
    turns["candidate_id"]
    .duplicated()
    .sum()
)

print(
    "Duplicate candidate IDs:",
    duplicate_candidate_ids
)


# --------------------------------------------------
# MISSING SPEAKERS
# --------------------------------------------------

missing_speakers = (
    turns["speaker"]
    .isna()
    .sum()
)

print(
    "Missing speaker values:",
    missing_speakers
)


# --------------------------------------------------
# SOURCE ORDER CHECK
# --------------------------------------------------

source_order_ok = True

if len(turns) > 1:

    starts = pd.to_numeric(
        turns["start_char"],
        errors="coerce"
    )

    source_order_ok = (
        starts.diff()
        .dropna()
        .ge(0)
        .all()
    )

print(
    "Source-order preserved:",
    source_order_ok
)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

turns.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

audit.to_csv(
    AUDIT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("OUTPUT")
print("------")
print(
    OUTPUT_FILE
)
print(
    AUDIT_FILE
)
print()

print(
    "DIALOGUE TURN RECONSTRUCTION COMPLETE."
)