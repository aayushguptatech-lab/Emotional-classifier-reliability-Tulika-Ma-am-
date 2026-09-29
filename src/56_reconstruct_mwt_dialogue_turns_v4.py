import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

CLEAN_FILE = Path(
    "data/cleaned/english/"
    "the_man_who_was_thursday_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v4.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_speaker_audit_v4.csv"
)


# =========================================================
# ATTRIBUTION VERBS
# =========================================================

VERBS = (
    "said|replied|answered|asked|cried|exclaimed|"
    "shouted|remarked|observed|continued|added|"
    "returned|called|inquired|demanded|retorted|"
    "whispered|muttered|resumed|assented"
)


# =========================================================
# KNOWN NAMES
# =========================================================

NAME_PATTERNS = [
    (r"\bMr\.?\s+Syme\b", "Syme"),
    (r"\bthe poet Syme\b", "Syme"),
    (r"\bpoet Syme\b", "Syme"),
    (r"\bSyme\b", "Syme"),

    (r"\bMr\.?\s+Gregory\b", "Gregory"),
    (r"\bComrade Gregory\b", "Gregory"),
    (r"\bGregory\b", "Gregory"),

    (r"\bMiss Gregory\b", "Rosamond Gregory"),
    (r"\bRosamond\b", "Rosamond Gregory"),
]


# =========================================================
# HELPERS
# =========================================================

def clean(value):
    if pd.isna(value):
        return ""
    return str(value)


def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()


def explicit_name(text):
    """
    Find an explicit named character in attribution text.
    """

    if not text:
        return None

    for pattern, name in NAME_PATTERNS:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return name

    return None


def has_attribution_verb(text):
    if not text:
        return False

    return bool(
        re.search(
            rf"\b(?:{VERBS})\b",
            text,
            flags=re.IGNORECASE
        )
    )


def attribution_after_candidate(gap):
    """
    Inspect only the text immediately after a quote.

    Returns:
        speaker
        attribution_type
        raw_attribution
    """

    if not gap:
        return None, "none", ""

    # Keep only the beginning of the gap.
    text = normalize_space(gap[:250])

    # -----------------------------------------------------
    # Named speaker
    # -----------------------------------------------------

    if has_attribution_verb(text):

        name = explicit_name(text)

        if name:

            return (
                name,
                "explicit_named",
                text[:250]
            )

    # -----------------------------------------------------
    # Pronoun attribution
    # -----------------------------------------------------

    pronoun_pattern = re.compile(
        rf"^(?:,?\s*)"
        rf"(?:{VERBS})"
        rf"\s+"
        rf"(he|she)\b",
        flags=re.IGNORECASE
    )

    match = pronoun_pattern.search(text)

    if match:

        return (
            match.group(1).lower(),
            "pronoun",
            text[:250]
        )

    # -----------------------------------------------------
    # Attribution exists but speaker not recovered
    # -----------------------------------------------------

    if has_attribution_verb(text):

        return (
            None,
            "unresolved_attribution",
            text[:250]
        )

    return None, "none", ""


def immediate_gap(clean_text, end_char, next_start):
    return clean_text[end_char:next_start]


# =========================================================
# LOAD
# =========================================================

print("MWT attribution-anchored reconstruction v4")
print("---------------------------------------------")
print()

candidates = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

candidates = candidates.sort_values(
    by=["start_char", "end_char"]
).reset_index(drop=True)

print(
    f"Candidate spans: {len(candidates):,}"
)

print()


# =========================================================
# PASS 1:
# DETERMINE DIRECT ATTRIBUTION AFTER EACH CANDIDATE
# =========================================================

audit_rows = []

last_explicit_speaker = None

for i, row in candidates.iterrows():

    candidate_id = clean(
        row["candidate_id"]
    )

    start_char = int(
        row["start_char"]
    )

    end_char = int(
        row["end_char"]
    )

    quoted_text = clean(
        row["quoted_text"]
    )

    # -----------------------------------------------------
    # Text between this candidate and the next candidate.
    # -----------------------------------------------------

    if i < len(candidates) - 1:

        next_start = int(
            candidates.iloc[i + 1]["start_char"]
        )

        gap = immediate_gap(
            clean_text,
            end_char,
            next_start
        )

    else:

        gap = clean_text[
            end_char:
        ]

    # -----------------------------------------------------
    # Direct attribution
    # -----------------------------------------------------

    speaker, attr_type, raw_attr = (
        attribution_after_candidate(gap)
    )

    # -----------------------------------------------------
    # Resolve pronouns conservatively.
    #
    # We only use the most recently established explicit
    # speaker. This is deliberately conservative.
    # -----------------------------------------------------

    resolved_from_pronoun = False

    if attr_type == "pronoun":

        if last_explicit_speaker:

            speaker = (
                last_explicit_speaker
            )

            resolved_from_pronoun = True

        else:

            speaker = None

    # -----------------------------------------------------
    # Update explicit-speaker memory.
    # -----------------------------------------------------

    if (
        speaker
        and attr_type == "explicit_named"
    ):

        last_explicit_speaker = (
            speaker
        )

    # -----------------------------------------------------
    # Narrative quote
    # -----------------------------------------------------

    is_narrative = (
        quoted_text.strip().lower()
        == "artists,"
    )

    audit_rows.append({

        "candidate_id":
            candidate_id,

        "start_char":
            start_char,

        "end_char":
            end_char,

        "start_line":
            row["start_line"],

        "end_line":
            row["end_line"],

        "quoted_text":
            quoted_text,

        "gap_text":
            normalize_space(
                gap[:500]
            ),

        "attribution_type":
            attr_type,

        "raw_attribution":
            raw_attr,

        "direct_speaker":
            speaker
            if speaker
            else "Unknown",

        "resolved_from_pronoun":
            resolved_from_pronoun,

        "is_narrative":
            is_narrative,

    })


audit = pd.DataFrame(
    audit_rows
)


# =========================================================
# PASS 2:
# RESOLVE UNATTRIBUTED CONTINUATIONS
# =========================================================

resolved_speakers = []

current_speaker = None
current_turn_evidence = None

for i, row in audit.iterrows():

    direct = row["direct_speaker"]

    attr_type = row[
        "attribution_type"
    ]

    speaker = None

    # -----------------------------------------------------
    # Explicit named speaker
    # -----------------------------------------------------

    if (
        direct != "Unknown"
        and attr_type == "explicit_named"
    ):

        speaker = direct
        current_speaker = direct
        current_turn_evidence = (
            "explicit_attribution"
        )

    # -----------------------------------------------------
    # Pronoun resolved to current known speaker
    # -----------------------------------------------------

    elif (
        direct != "Unknown"
        and attr_type == "pronoun"
    ):

        speaker = direct

        if current_speaker is None:
            current_speaker = direct

        current_turn_evidence = (
            "pronoun_resolved"
        )

    # -----------------------------------------------------
    # No attribution:
    #
    # Don't immediately invent a speaker.
    # If this is immediately following an established
    # speaker and there is no new attribution, treat it
    # as a possible continuation.
    # -----------------------------------------------------

    elif attr_type == "none":

        if current_speaker:

            speaker = current_speaker

        else:

            speaker = None

    # -----------------------------------------------------
    # Attribution exists but unresolved
    # -----------------------------------------------------

    else:

        speaker = None

    resolved_speakers.append(
        speaker
        if speaker
        else "Unknown"
    )


audit["resolved_speaker"] = (
    resolved_speakers
)


# =========================================================
# PASS 3:
# BUILD TURNS
# =========================================================

turns = []

current_candidates = []
current_speaker = None
current_evidence = []


def flush():

    global current_candidates
    global current_speaker
    global current_evidence

    if not current_candidates:
        return

    valid = [
        x for x in current_candidates
        if not x["is_narrative"]
    ]

    if not valid:

        current_candidates = []
        current_speaker = None
        current_evidence = []

        return

    text = " ".join(
        x["quoted_text"]
        for x in valid
    )

    candidate_ids = "|".join(
        x["candidate_id"]
        for x in valid
    )

    start_line = min(
        int(x["start_line"])
        for x in valid
    )

    end_line = max(
        int(x["end_line"])
        for x in valid
    )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    if (
        current_speaker
        and current_speaker != "Unknown"
        and "explicit_attribution"
        in current_evidence
    ):

        confidence = "high"

    else:

        confidence = "review"

    turns.append({

        "turn_id":
            f"MWT_T{len(turns)+1:05d}",

        "start_line":
            start_line,

        "end_line":
            end_line,

        "speaker":
            current_speaker
            if current_speaker
            else "Unknown",

        "speaker_evidence":
            "|".join(
                sorted(
                    set(
                        current_evidence
                    )
                )
            ),

        "source_candidate_ids":
            candidate_ids,

        "quoted_text":
            text,

        "extraction_confidence":
            confidence,

    })

    current_candidates = []
    current_speaker = None
    current_evidence = []


# ---------------------------------------------------------
# Turn construction
# ---------------------------------------------------------

for i, row in audit.iterrows():

    if row["is_narrative"]:

        flush()

        continue

    speaker = row[
        "resolved_speaker"
    ]

    attr_type = row[
        "attribution_type"
    ]

    # -----------------------------------------------------
    # FIRST CANDIDATE
    # -----------------------------------------------------

    if not current_candidates:

        current_candidates = [
            row.to_dict()
        ]

        if speaker != "Unknown":

            current_speaker = speaker

            if attr_type == "explicit_named":

                current_evidence.append(
                    "explicit_attribution"
                )

            elif attr_type == "pronoun":

                current_evidence.append(
                    "pronoun_resolved"
                )

            elif attr_type == "none":

                current_evidence.append(
                    "continuation"
                )

        continue

    # -----------------------------------------------------
    # EXPLICIT NEW SPEAKER
    # -----------------------------------------------------

    if (
        attr_type == "explicit_named"
        and speaker != "Unknown"
        and current_speaker
        and speaker != current_speaker
    ):

        flush()

        current_candidates = [
            row.to_dict()
        ]

        current_speaker = speaker

        current_evidence = [
            "explicit_attribution"
        ]

        continue

    # -----------------------------------------------------
    # UNRESOLVED ATTRIBUTION
    # -----------------------------------------------------

    if attr_type == "unresolved_attribution":

        flush()

        current_candidates = [
            row.to_dict()
        ]

        current_speaker = "Unknown"

        current_evidence = [
            "unresolved_attribution"
        ]

        continue

    # -----------------------------------------------------
    # SAME SPEAKER / CONTINUATION
    # -----------------------------------------------------

    if (
        speaker == current_speaker
        or (
            attr_type == "none"
            and current_speaker
        )
    ):

        current_candidates.append(
            row.to_dict()
        )

        if attr_type == "none":

            current_evidence.append(
                "continuation"
            )

        elif attr_type == "pronoun":

            current_evidence.append(
                "pronoun_resolved"
            )

        elif attr_type == "explicit_named":

            current_evidence.append(
                "explicit_attribution"
            )

        continue

    # -----------------------------------------------------
    # EVERYTHING ELSE:
    # CONSERVATIVE NEW TURN
    # -----------------------------------------------------

    flush()

    current_candidates = [
        row.to_dict()
    ]

    current_speaker = (
        speaker
        if speaker != "Unknown"
        else None
    )

    current_evidence = []

    if speaker != "Unknown":

        if attr_type == "explicit_named":

            current_evidence.append(
                "explicit_attribution"
            )

        elif attr_type == "pronoun":

            current_evidence.append(
                "pronoun_resolved"
            )


flush()


out = pd.DataFrame(
    turns
)


# =========================================================
# RENUMBER
# =========================================================

out["turn_id"] = [
    f"MWT_T{i:05d}"
    for i in range(
        1,
        len(out) + 1
    )
]


# =========================================================
# SAVE
# =========================================================

audit.to_csv(
    AUDIT_FILE,
    index=False,
    encoding="utf-8-sig"
)

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# SUMMARY
# =========================================================

print()
print("V4 RECONSTRUCTION SUMMARY")
print("--------------------------")

print(
    f"Candidate spans: "
    f"{len(audit):,}"
)

print(
    f"Reconstructed turns: "
    f"{len(out):,}"
)

print()

known = (
    out["speaker"]
    != "Unknown"
)

print(
    f"Known speakers: "
    f"{known.sum():,}"
)

print(
    f"Unknown speakers: "
    f"{(~known).sum():,}"
)

print()

print("ATTRIBUTION TYPES")
print("------------------")

print(
    audit[
        "attribution_type"
    ]
    .value_counts()
    .to_string()
)

print()

print("SPEAKER COUNTS")
print("--------------")

print(
    out["speaker"]
    .value_counts()
    .head(25)
    .to_string()
)

print()

print("FIRST 50 V4 TURNS")
print("------------------")

for _, row in out.head(50).iterrows():

    preview = (
        str(
            row["quoted_text"]
        )
        .replace("\n", " ")
    )

    print(
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['extraction_confidence']} | "
        f"{row['source_candidate_ids']} | "
        f"{preview[:180]}"
    )

print()

print(
    "V4 reconstruction complete."
)

print(
    f"Turn file: {OUTPUT_FILE}"
)

print(
    f"Audit file: {AUDIT_FILE}"
)