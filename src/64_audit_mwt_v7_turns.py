import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

TURN_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v7.csv"
)

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
    "the_man_who_was_thursday_v7_turn_audit.csv"
)


# =========================================================
# LOAD
# =========================================================

turns = pd.read_csv(
    TURN_FILE
)

candidates = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

candidate_map = {
    str(row["candidate_id"]): row
    for _, row in candidates.iterrows()
}


print(
    "MWT V7 turn audit"
)

print(
    "================="
)

print()

print(
    f"V7 turns: {len(turns):,}"
)

print(
    f"Candidate rows: {len(candidates):,}"
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


def known_speaker(value):

    value = str(value).strip()

    if (
        not value
        or value.lower() == "unknown"
    ):

        return None

    return value


def gap_between(a, b):

    end_a = int(
        a["end_char"]
    )

    start_b = int(
        b["start_char"]
    )

    if start_b <= end_a:

        return ""

    return normalize_space(
        clean_text[
            end_a:start_b
        ]
    )


# =========================================================
# AUDIT EACH TURN
# =========================================================

records = []


for _, turn in turns.iterrows():

    ids = str(
        turn["candidate_ids"]
    ).split("|")

    speaker = known_speaker(
        turn["speaker"]
    )

    direct_speakers = []

    pronoun_speakers = []

    attribution_types = []

    candidate_texts = []

    internal_gaps = []

    for cid in ids:

        if cid not in candidate_map:

            continue

        row = candidate_map[cid]

        candidate_texts.append(
            normalize_space(
                row["quoted_text"]
            )
        )

        attribution_types.append(
            str(
                row["attribution_type"]
            )
        )

        resolved = known_speaker(
            row["resolved_speaker"]
        )

        evidence = str(
            row["speaker_evidence"]
        )

        if resolved is not None:

            if evidence in {
                "named_speaker",
                "role_speaker"
            }:

                direct_speakers.append(
                    resolved
                )

            elif evidence in {
                "pronoun_speaker",
                "pronoun_speaker_named_target"
            }:

                pronoun_speakers.append(
                    resolved
                )


    # -----------------------------------------------------
    # Detect conflicting direct speakers
    # -----------------------------------------------------

    unique_direct = sorted(
        set(direct_speakers)
    )

    unique_pronoun = sorted(
        set(pronoun_speakers)
    )


    if len(unique_direct) > 1:

        status = (
            "CRITICAL_SPEAKER_CONFLICT"
        )

    elif (
        unique_direct
        and unique_pronoun
        and any(
            p != unique_direct[0]
            for p in unique_pronoun
        )
    ):

        status = (
            "REVIEW_SPEAKER_CONFLICT"
        )

    elif speaker is None:

        status = (
            "UNKNOWN_SPEAKER"
        )

    elif unique_direct:

        status = (
            "DIRECT_SPEAKER_SUPPORTED"
        )

    elif unique_pronoun:

        status = (
            "PRONOUN_SPEAKER_SUPPORTED"
        )

    else:

        status = (
            "CONTEXT_ONLY_OR_UNKNOWN"
        )


    # -----------------------------------------------------
    # Internal candidate gaps
    # -----------------------------------------------------

    for i in range(
        len(ids) - 1
    ):

        a_id = ids[i]

        b_id = ids[i + 1]

        if (
            a_id not in candidate_map
            or b_id not in candidate_map
        ):

            continue

        gap = gap_between(
            candidate_map[a_id],
            candidate_map[b_id]
        )

        internal_gaps.append(
            gap
        )


    records.append({

        "turn_id":
            turn["turn_id"],

        "candidate_ids":
            turn["candidate_ids"],

        "speaker":
            turn["speaker"],

        "speaker_confidence":
            turn["speaker_confidence"],

        "extraction_confidence":
            turn["extraction_confidence"],

        "boundary_confidence":
            turn["boundary_confidence"],

        "turn_size":
            len(ids),

        "direct_speakers":
            "|".join(unique_direct),

        "pronoun_speakers":
            "|".join(unique_pronoun),

        "attribution_types":
            "|".join(
                sorted(
                    set(
                        attribution_types
                    )
                )
            ),

        "status":
            status,

        "quoted_text":
            " ".join(
                candidate_texts
            ),

        "internal_gaps":
            " || ".join(
                internal_gaps
            )
    })


audit = pd.DataFrame(
    records
)


# =========================================================
# SAVE
# =========================================================

audit.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# SUMMARY
# =========================================================

print(
    "AUDIT STATUS COUNTS"
)

print(
    "-------------------"
)

print(
    audit[
        "status"
    ]
    .value_counts()
    .to_string()
)

print()


print(
    "TURN SIZE COUNTS"
)

print(
    "----------------"
)

print(
    audit[
        "turn_size"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)

print()


# =========================================================
# CRITICAL CONFLICTS
# =========================================================

critical = audit[
    audit[
        "status"
    ] == "CRITICAL_SPEAKER_CONFLICT"
]


print(
    "CRITICAL SPEAKER CONFLICTS"
)

print(
    "--------------------------"
)

print(
    f"Count: {len(critical):,}"
)

for _, row in critical.head(50).iterrows():

    print()

    print(
        f'{row["turn_id"]} | '
        f'{row["candidate_ids"]}'
    )

    print(
        f'Direct speakers: '
        f'{row["direct_speakers"]}'
    )

    print(
        f'Pronoun speakers: '
        f'{row["pronoun_speakers"]}'
    )

    print(
        f'Text: '
        f'{row["quoted_text"][:250]}'
    )


print()


# =========================================================
# UNKNOWN SPEAKER EXAMPLES
# =========================================================

unknown = audit[
    audit[
        "status"
    ] == "UNKNOWN_SPEAKER"
]


print(
    "UNKNOWN SPEAKER TURNS"
)

print(
    "---------------------"
)

print(
    f"Count: {len(unknown):,}"
)

for _, row in unknown.head(40).iterrows():

    print()

    print(
        f'{row["turn_id"]} | '
        f'{row["candidate_ids"]}'
    )

    print(
        f'Attribution types: '
        f'{row["attribution_types"]}'
    )

    print(
        f'Text: '
        f'{row["quoted_text"][:250]}'
    )


print()


# =========================================================
# PRONOUN-SUPPORTED SPEAKERS
# =========================================================

pronoun = audit[
    audit[
        "status"
    ] == "PRONOUN_SPEAKER_SUPPORTED"
]


print(
    "PRONOUN-SUPPORTED TURNS"
)

print(
    "-----------------------"
)

print(
    f"Count: {len(pronoun):,}"
)

for _, row in pronoun.head(40).iterrows():

    print()

    print(
        f'{row["turn_id"]} | '
        f'{row["candidate_ids"]}'
    )

    print(
        f'Speaker: {row["speaker"]}'
    )

    print(
        f'Pronoun evidence: '
        f'{row["pronoun_speakers"]}'
    )

    print(
        f'Text: '
        f'{row["quoted_text"][:250]}'
    )


print()


print(
    f"Audit saved to: {OUTPUT_FILE}"
)

print(
    "V7 turn audit complete."
)
