import re
import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

ATTRIBUTION_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_attribution_map.csv"
)

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
    "the_man_who_was_thursday_candidate_attribution_context_resolved.csv"
)


# =========================================================
# CHARACTER ALIASES
# =========================================================

ALIASES = {
    "syme": "Syme",
    "mr. syme": "Syme",
    "the poet syme": "Syme",
    "poet syme": "Syme",

    "gregory": "Gregory",
    "mr. gregory": "Gregory",
    "comrade gregory": "Gregory",

    "miss gregory": "Rosamond Gregory",
    "rosamond": "Rosamond Gregory",

    "the professor": "the Professor",
    "professor": "the Professor",

    "the secretary": "the Secretary",
    "secretary": "the Secretary",

    "the colonel": "the Colonel",
    "colonel": "the Colonel",

    "the president": "the President",
    "president": "the President",

    "the marquis": "the Marquis",
    "marquis": "the Marquis",

    "the policeman": "the policeman",

    "the man": "the man",

    "the other": "the other",

    "the girl": "the girl",
}


# =========================================================
# HELPERS
# =========================================================

def normalize_space(text):
    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def normalize_name(name):

    if not name:
        return ""

    key = normalize_space(
        name
    ).lower()

    return ALIASES.get(
        key,
        normalize_space(name)
    )


def find_character_mentions(text):

    """
    Find recognizable character references in text.

    This is evidence only. It does NOT automatically
    mean the mentioned character is the speaker.
    """

    found = []

    patterns = [
        (r"\bthe poet Syme\b", "Syme"),
        (r"\bpoet Syme\b", "Syme"),
        (r"\bMr\.?\s+Syme\b", "Syme"),
        (r"\bSyme\b", "Syme"),

        (r"\bMr\.?\s+Gregory\b", "Gregory"),
        (r"\bComrade Gregory\b", "Gregory"),
        (r"\bGregory\b", "Gregory"),

        (r"\bMiss Gregory\b", "Rosamond Gregory"),
        (r"\bRosamond\b", "Rosamond Gregory"),

        (r"\bthe Professor\b", "the Professor"),
        (r"\bthe Secretary\b", "the Secretary"),
        (r"\bthe Colonel\b", "the Colonel"),
        (r"\bthe President\b", "the President"),
        (r"\bthe Marquis\b", "the Marquis"),
        (r"\bthe policeman\b", "the policeman"),
        (r"\bthe girl\b", "the girl"),
        (r"\bthe man\b", "the man"),
        (r"\bthe other\b", "the other"),
    ]

    for pattern, name in patterns:

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            found.append({
                "name": name,
                "position": match.start()
            })

    found.sort(
        key=lambda x: x["position"]
    )

    return found


def detect_gender_pronoun(text):

    """
    Detect explicit he/she references.
    """

    if re.search(
        r"\bhe\b",
        text,
        flags=re.IGNORECASE
    ):
        return "he"

    if re.search(
        r"\bshe\b",
        text,
        flags=re.IGNORECASE
    ):
        return "she"

    return ""


def gender_of_character(name):

    """
    Conservative gender mapping used ONLY for resolving
    explicit he/she references.
    """

    male = {
        "Syme",
        "Gregory",
        "the Professor",
        "the Secretary",
        "the Colonel",
        "the President",
        "the Marquis",
        "the policeman",
        "the man",
        "the other",
    }

    female = {
        "Rosamond Gregory",
        "the girl",
    }

    if name in male:
        return "he"

    if name in female:
        return "she"

    return ""


def gender_compatible(
    pronoun,
    name
):

    gender = gender_of_character(
        name
    )

    if not gender:
        return False

    return gender == pronoun


# =========================================================
# LOAD FILES
# =========================================================

print(
    "MWT context-based attribution resolution"
)

print(
    "========================================"
)

print()

attr = pd.read_csv(
    ATTRIBUTION_FILE
)

candidates = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

attr = attr.sort_values(
    ["start_char", "end_char"]
).reset_index(
    drop=True
)

candidates = candidates.sort_values(
    ["start_char", "end_char"]
).reset_index(
    drop=True
)

print(
    f"Attribution rows: {len(attr):,}"
)

print(
    f"Candidate rows: {len(candidates):,}"
)

print()


# =========================================================
# BUILD LOOKUP
# =========================================================

candidate_lookup = {}

for _, row in candidates.iterrows():

    candidate_lookup[
        row["candidate_id"]
    ] = row


# =========================================================
# PROCESS
# =========================================================

results = []


for i, row in attr.iterrows():

    candidate_id = str(
        row["candidate_id"]
    )

    attr_type = str(
        row["attribution_type"]
    )

    speaker_name = str(
        row["speaker_name"]
    )

    quoted_text = str(
        row["quoted_text"]
    )

    start_char = int(
        row["start_char"]
    )

    end_char = int(
        row["end_char"]
    )


    # -----------------------------------------------------
    # Default: preserve Script 59 evidence
    # -----------------------------------------------------

    resolved_speaker = (
        speaker_name
        if speaker_name != "Unknown"
        else "Unknown"
    )

    resolution_method = (
        "direct_attribution"
        if speaker_name != "Unknown"
        else "unresolved"
    )

    resolution_confidence = (
        "high"
        if speaker_name != "Unknown"
        else "review"
    )

    context_evidence = ""


    # -----------------------------------------------------
    # Only attempt pronoun resolution when Script 59
    # explicitly identified a pronoun speaker.
    # -----------------------------------------------------

    is_pronoun = (
        attr_type
        in {
            "pronoun_speaker",
            "pronoun_speaker_named_target"
        }
    )

    if not is_pronoun:

        results.append({
            **row.to_dict(),

            "resolved_speaker":
                resolved_speaker,

            "resolution_method":
                resolution_method,

            "resolution_confidence":
                resolution_confidence,

            "context_evidence":
                context_evidence
        })

        continue


    pronoun = detect_gender_pronoun(
        str(
            row["attribution_text"]
        )
    )

    target = str(
        row["attribution_target"]
    )


    # -----------------------------------------------------
    # Context window
    #
    # We deliberately use a moderate local window.
    # The goal is dialogue context, not arbitrary
    # document-wide name matching.
    # -----------------------------------------------------

    window_before = clean_text[
        max(
            0,
            start_char - 1800
        ):start_char
    ]

    window_after = clean_text[
        end_char:
        min(
            len(clean_text),
            end_char + 1200
        )
    ]

    before_text = normalize_space(
        window_before
    )

    after_text = normalize_space(
        window_after
    )


    # =====================================================
    # RULE 1
    #
    # Explicit target:
    #
    # "he said to Gregory"
    #
    # Target is NOT speaker.
    #
    # We do NOT resolve the "he" merely from Gregory.
    # =====================================================

    if (
        attr_type
        == "pronoun_speaker_named_target"
    ):

        context_evidence = (
            f"Explicit addressee target: {target}"
        )

        resolution_method = (
            "pronoun_with_known_addressee"
        )

        resolution_confidence = (
            "review"
        )

        results.append({
            **row.to_dict(),

            "resolved_speaker":
                "Unknown",

            "resolution_method":
                resolution_method,

            "resolution_confidence":
                resolution_confidence,

            "context_evidence":
                context_evidence
        })

        continue


    # =====================================================
    # RULE 2
    #
    # Look for immediate preceding attribution
    # that establishes a currently active speaker.
    #
    # Example:
    #
    # "said Syme. 'Good Lord, no!' he said,"
    #
    # The preceding speaker is useful evidence.
    #
    # But it is NOT automatically accepted because the
    # new "he" may refer to another participant.
    # =====================================================

    preceding_candidates = []

    # Search the preceding 1200 characters for
    # explicit attribution constructions.

    attribution_patterns = [

        (
            r"(?:said|replied|answered|asked|"
            r"cried|exclaimed|remarked|observed|"
            r"continued|added|returned|inquired|"
            r"declared|protested|resumed|assented)"
            r"\s+"
            r"(Mr\.\s+Syme|the poet Syme|poet Syme|Syme|"
            r"Mr\.\s+Gregory|Comrade Gregory|Gregory|"
            r"Miss Gregory|Rosamond|"
            r"the Professor|the Secretary|the Colonel|"
            r"the President|the Marquis|the policeman|"
            r"the girl|the man|the other)",
            re.IGNORECASE
        ),

        (
            r"(Mr\.\s+Syme|the poet Syme|poet Syme|Syme|"
            r"Mr\.\s+Gregory|Comrade Gregory|Gregory|"
            r"Miss Gregory|Rosamond|"
            r"the Professor|the Secretary|the Colonel|"
            r"the President|the Marquis|the policeman|"
            r"the girl|the man|the other)"
            r"\s+"
            r"(?:said|replied|answered|asked|"
            r"cried|exclaimed|remarked|observed|"
            r"continued|added|returned|inquired|"
            r"declared|protested|resumed|assented)",
            re.IGNORECASE
        ),
    ]


    for pattern, flags in attribution_patterns:

        matches = list(
            re.finditer(
                pattern,
                before_text,
                flags
            )
        )

        for match in matches:

            mentioned = match.group(1)

            normalized = normalize_name(
                mentioned
            )

            if gender_compatible(
                pronoun,
                normalized
            ):

                preceding_candidates.append({
                    "name":
                        normalized,

                    "position":
                        match.start()
                })


    # -----------------------------------------------------
    # Only the most recent compatible explicit attribution
    # is considered.
    # -----------------------------------------------------

    if preceding_candidates:

        preceding_candidates.sort(
            key=lambda x: x["position"]
        )

        nearest = (
            preceding_candidates[-1]
        )

        resolved_speaker = (
            nearest["name"]
        )

        resolution_method = (
            "nearest_gender_compatible_attribution"
        )

        resolution_confidence = (
            "medium"
        )

        context_evidence = (
            f"Nearest compatible prior "
            f"speaker reference: "
            f"{resolved_speaker}"
        )

    else:

        # =================================================
        # RULE 3
        #
        # Search immediate following narrative for a
        # direct identification of "he/she".
        #
        # Example patterns:
        #
        # "he said ... Syme"
        # "he, Syme, ..."
        #
        # Only very direct forms are accepted.
        # =================================================

        direct_following = re.search(
            r"\b"
            + re.escape(pronoun)
            + r"\b"
            r"[^.]{0,120}?"
            r"\b"
            r"(Syme|Gregory|Rosamond|"
            r"the Professor|the Secretary|"
            r"the Colonel|the President|"
            r"the Marquis|the policeman|"
            r"the girl|the man|the other)"
            r"\b",
            after_text,
            flags=re.IGNORECASE
        )

        if direct_following:

            candidate_name = normalize_name(
                direct_following.group(1)
            )

            if gender_compatible(
                pronoun,
                candidate_name
            ):

                resolved_speaker = (
                    candidate_name
                )

                resolution_method = (
                    "direct_following_identification"
                )

                resolution_confidence = (
                    "medium"
                )

                context_evidence = (
                    f"Direct following identification: "
                    f"{candidate_name}"
                )


    # -----------------------------------------------------
    # Save result
    # -----------------------------------------------------

    results.append({
        **row.to_dict(),

        "resolved_speaker":
            resolved_speaker,

        "resolution_method":
            resolution_method,

        "resolution_confidence":
            resolution_confidence,

        "context_evidence":
            context_evidence
    })


# =========================================================
# SAVE
# =========================================================

out = pd.DataFrame(
    results
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
    "RESOLUTION METHOD COUNTS"
)

print(
    "------------------------"
)

print(
    out[
        "resolution_method"
    ]
    .value_counts()
    .to_string()
)

print()

print(
    "RESOLUTION CONFIDENCE COUNTS"
)

print(
    "----------------------------"
)

print(
    out[
        "resolution_confidence"
    ]
    .value_counts()
    .to_string()
)

print()

print(
    "RESOLVED SPEAKER COUNTS"
)

print(
    "-----------------------"
)

print(
    out[
        "resolved_speaker"
    ]
    .value_counts()
    .head(30)
    .to_string()
)

print()


# =========================================================
# PRONOUN CASES
# =========================================================

pronoun_rows = out[
    out["attribution_type"].isin(
        [
            "pronoun_speaker",
            "pronoun_speaker_named_target"
        ]
    )
]

print(
    "PRONOUN CASES"
)

print(
    "-------------"
)

print(
    f"Total pronoun cases: "
    f"{len(pronoun_rows):,}"
)

print(
    f"Resolved: "
    f"{(pronoun_rows['resolved_speaker'] != 'Unknown').sum():,}"
)

print(
    f"Still review: "
    f"{(pronoun_rows['resolved_speaker'] == 'Unknown').sum():,}"
)

print()


# =========================================================
# KEY EXAMPLES
# =========================================================

example_ids = [
    "MWT_C00043",
    "MWT_C00048",
    "MWT_C00091",
]

print(
    "KEY PRONOUN EXAMPLES"
)

print(
    "--------------------"
)

for cid in example_ids:

    matches = out[
        out["candidate_id"]
        == cid
    ]

    if matches.empty:
        continue

    row = matches.iloc[0]

    print()

    print(
        cid
    )

    print(
        "  QUOTE:",
        row["quoted_text"]
    )

    print(
        "  ORIGINAL:",
        row["speaker_name"]
    )

    print(
        "  RESOLVED:",
        row["resolved_speaker"]
    )

    print(
        "  METHOD:",
        row["resolution_method"]
    )

    print(
        "  CONFIDENCE:",
        row["resolution_confidence"]
    )

    print(
        "  EVIDENCE:",
        row["context_evidence"]
    )


print()

print(
    "Context resolution complete."
)

print(
    f"Output: {OUTPUT_FILE}"
)