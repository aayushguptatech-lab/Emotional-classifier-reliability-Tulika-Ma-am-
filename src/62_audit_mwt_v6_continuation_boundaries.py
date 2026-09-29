import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

TURN_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v6.csv"
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
    "the_man_who_was_thursday_v6_continuation_boundary_audit.csv"
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

candidates = candidates.sort_values(
    "start_char"
).reset_index(
    drop=True
)

print(
    "MWT V6 continuation-boundary audit"
)

print(
    "=================================="
)

print()

print(
    f"V6 turns: {len(turns):,}"
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


def get_gap(row_a, row_b):

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


def candidate_map():

    return {
        str(row["candidate_id"]): row
        for _, row in candidates.iterrows()
    }


cand_map = candidate_map()


# =========================================================
# IDENTIFY ADJACENT V6 TURNS
# =========================================================

records = []

for i in range(
    len(turns) - 1
):

    current = turns.iloc[i]

    nxt = turns.iloc[i + 1]

    current_ids = str(
        current["candidate_ids"]
    ).split("|")

    next_ids = str(
        nxt["candidate_ids"]
    ).split("|")

    current_last_id = (
        current_ids[-1]
    )

    next_first_id = (
        next_ids[0]
    )

    if (
        current_last_id
        not in cand_map
        or next_first_id
        not in cand_map
    ):
        continue

    current_candidate = cand_map[
        current_last_id
    ]

    next_candidate = cand_map[
        next_first_id
    ]

    gap = get_gap(
        current_candidate,
        next_candidate
    )

    current_attribution = str(
        current_candidate[
            "attribution_type"
        ]
    )

    next_attribution = str(
        next_candidate[
            "attribution_type"
        ]
    )

    current_evidence = str(
        current_candidate[
            "speaker_evidence"
        ]
    )

    next_evidence = str(
        next_candidate[
            "speaker_evidence"
        ]
    )

    current_quote = normalize_space(
        current_candidate[
            "quoted_text"
        ]
    )

    next_quote = normalize_space(
        next_candidate[
            "quoted_text"
        ]
    )


    # -----------------------------------------------------
    # Strong continuation signals
    # -----------------------------------------------------

    reasons = []

    if current_attribution in {
        "named_speaker",
        "role_speaker",
        "pronoun_speaker",
        "pronoun_speaker_named_target",
        "unresolved_attribution"
    }:

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

            reasons.append(
                "explicit_continuation_language"
            )


    if current_quote.endswith(
        (
            ",",
            ";",
            ":",
            "—",
            "–",
            "..."
        )
    ):

        if len(gap) <= 100:

            reasons.append(
                "unfinished_quote_short_gap"
            )


    if next_quote and next_quote[0].islower():

        if len(gap) <= 150:

            reasons.append(
                "lowercase_next_fragment"
            )


    # -----------------------------------------------------
    # Same resolved speaker
    # -----------------------------------------------------

    current_speaker = str(
        current["speaker"]
    )

    next_speaker = str(
        nxt["speaker"]
    )

    same_known_speaker = (
        current_speaker != "Unknown"
        and next_speaker != "Unknown"
        and current_speaker == next_speaker
    )


    if same_known_speaker:

        reasons.append(
            "same_known_speaker"
        )


    # -----------------------------------------------------
    # Candidate count = one each
    # -----------------------------------------------------

    if (
        len(current_ids) == 1
        and len(next_ids) == 1
    ):

        reasons.append(
            "single_candidate_turns"
        )


    # -----------------------------------------------------
    # Score
    # -----------------------------------------------------

    score = 0

    if "explicit_continuation_language" in reasons:
        score += 4

    if "unfinished_quote_short_gap" in reasons:
        score += 3

    if "lowercase_next_fragment" in reasons:
        score += 2

    if "same_known_speaker" in reasons:
        score += 2

    if "single_candidate_turns" in reasons:
        score += 1


    if score >= 6:

        recommendation = (
            "STRONG_CONTINUATION"
        )

    elif score >= 4:

        recommendation = (
            "LIKELY_CONTINUATION"
        )

    elif score >= 2:

        recommendation = (
            "REVIEW"
        )

    else:

        recommendation = (
            "KEEP_SEPARATE"
        )


    records.append({

        "current_turn_id":
            current["turn_id"],

        "next_turn_id":
            nxt["turn_id"],

        "current_candidate_id":
            current_last_id,

        "next_candidate_id":
            next_first_id,

        "current_speaker":
            current_speaker,

        "next_speaker":
            next_speaker,

        "current_attribution":
            current_attribution,

        "next_attribution":
            next_attribution,

        "current_speaker_evidence":
            current_evidence,

        "next_speaker_evidence":
            next_evidence,

        "current_quote":
            current_quote,

        "next_quote":
            next_quote,

        "gap":
            gap,

        "signals":
            "|".join(reasons),

        "score":
            score,

        "recommendation":
            recommendation
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
    "BOUNDARY AUDIT SUMMARY"
)

print(
    "----------------------"
)

print(
    audit[
        "recommendation"
    ]
    .value_counts()
    .to_string()
)

print()

print(
    "SIGNAL COUNTS"
)

print(
    "-------------"
)

all_signals = []

for value in audit[
    "signals"
].fillna(""):

    if value:

        all_signals.extend(
            value.split("|")
        )

if all_signals:

    print(
        pd.Series(
            all_signals
        )
        .value_counts()
        .to_string()
    )

print()


# =========================================================
# SHOW STRONG / LIKELY CASES
# =========================================================

interesting = audit[
    audit[
        "recommendation"
    ].isin(
        [
            "STRONG_CONTINUATION",
            "LIKELY_CONTINUATION"
        ]
    )
]


print(
    "STRONG / LIKELY CONTINUATION CASES"
)

print(
    "----------------------------------"
)

for _, row in interesting.head(80).iterrows():

    print()

    print(
        f'{row["current_turn_id"]} -> '
        f'{row["next_turn_id"]}'
    )

    print(
        f'Candidates: '
        f'{row["current_candidate_id"]} -> '
        f'{row["next_candidate_id"]}'
    )

    print(
        f'Speakers: '
        f'{row["current_speaker"]} -> '
        f'{row["next_speaker"]}'
    )

    print(
        f'Recommendation: '
        f'{row["recommendation"]}'
    )

    print(
        f'Score: {row["score"]}'
    )

    print(
        f'Signals: {row["signals"]}'
    )

    print(
        f'Current: {row["current_quote"][:180]}'
    )

    print(
        f'Next: {row["next_quote"][:180]}'
    )

    print(
        f'Gap: {row["gap"][:220]}'
    )


print()

print(
    f"Audit saved to: {OUTPUT_FILE}"
)

print(
    "V6 continuation-boundary audit complete."
)