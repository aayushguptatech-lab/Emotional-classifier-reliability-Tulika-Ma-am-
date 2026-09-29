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
    "the_man_who_was_thursday_candidate_attribution_map.csv"
)


# =========================================================
# ATTRIBUTION VERBS
# =========================================================

VERBS = (
    "said|replied|answered|asked|cried|exclaimed|"
    "shouted|remarked|observed|continued|added|"
    "returned|called|inquired|demanded|retorted|"
    "whispered|muttered|resumed|assented|"
    "suggested|declared|protested|urged|murmured|"
    "ejaculated|interrupted|continued"
)


# =========================================================
# CHARACTER NAME PATTERNS
#
# These identify the person named in an attribution.
# This is NOT the complete speaker dictionary.
# =========================================================

NAME_PATTERNS = [

    # Syme
    (r"\bthe poet Syme\b", "Syme"),
    (r"\bpoet Syme\b", "Syme"),
    (r"\bMr\.?\s+Syme\b", "Syme"),
    (r"\bSyme\b", "Syme"),

    # Gregory
    (r"\bMr\.?\s+Gregory\b", "Gregory"),
    (r"\bComrade Gregory\b", "Gregory"),
    (r"\bGregory\b", "Gregory"),

    # Rosamond
    (r"\bMiss Gregory\b", "Rosamond Gregory"),
    (r"\bRosamond\b", "Rosamond Gregory"),
]


# =========================================================
# ROLE / DESCRIPTION PATTERNS
# =========================================================

ROLE_PATTERNS = [

    (r"\bthe girl\b", "the girl"),
    (r"\bthe man\b", "the man"),
    (r"\bthe policeman\b", "the policeman"),
    (r"\bthe Professor\b", "the Professor"),
    (r"\bthe Secretary\b", "the Secretary"),
    (r"\bthe Colonel\b", "the Colonel"),
    (r"\bthe President\b", "the President"),
    (r"\bthe Marquis\b", "the Marquis"),
    (r"\bthe other\b", "the other"),
    (r"\bthe man in spectacles\b", "the man in spectacles"),
]


# =========================================================
# HELPERS
# =========================================================

def normalize_space(text):

    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def find_named_speaker(text):

    """
    Return the first recognizable character name
    occurring in the attribution text.
    """

    for pattern, name in NAME_PATTERNS:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            return name

    return None


def find_role_speaker(text):

    """
    Return a recognizable role/description if one
    occurs in the attribution text.
    """

    for pattern, role in ROLE_PATTERNS:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            return role

    return None


def find_verb(text):

    match = re.search(
        rf"\b({VERBS})\b",
        text,
        flags=re.IGNORECASE
    )

    if match:

        return match.group(1).lower()

    return None


def analyze_gap(gap):

    """
    Analyze ONLY the material immediately following
    the quotation.

    No turn reconstruction is performed here.
    """

    text = normalize_space(
        gap
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Only inspect the immediate beginning of the gap.
    #
    # A speaker name appearing later in narrative prose
    # must NOT be treated as attribution for the quotation.
    #
    # Example:
    #
    # "that has to be done anonymously."
    #
    # gap:
    # "And at that ... Syme ... continued ..."
    #
    # "Syme" is narrative mention, not attribution.
    # -----------------------------------------------------

    local = text[:160]

    if not local:

        return {
            "attribution_type":
                "none",

            "speaker_evidence":
                "none",

            "speaker_name":
                "Unknown",

            "attribution_verb":
                "",

            "attribution_target":
                "",

            "attribution_text":
                ""
        }


    # -----------------------------------------------------
    # Named speaker
    # -----------------------------------------------------

        # -----------------------------------------------------
    # Immediate attribution only
    #
    # Valid examples:
    #
    # "said Gregory."
    # "replied Syme;"
    # "asked Mr. Syme."
    # "cried the Professor."
    #
    # Invalid:
    #
    # "And at that ... Syme ... continued ..."
    #
    # because the speaker name occurs later in narrative.
    # -----------------------------------------------------

    immediate = local[:120]

    # -----------------------------------------------------
    # Named speaker directly attached to attribution verb
    # -----------------------------------------------------

    named_patterns = [

        # Verb + named speaker
        rf"\b(?:{VERBS})\s+"
        rf"(Mr\.\s+Syme|the poet Syme|poet Syme|Syme)",

        rf"\b(?:{VERBS})\s+"
        rf"(Mr\.\s+Gregory|Comrade Gregory|Gregory)",

        rf"\b(?:{VERBS})\s+"
        rf"(Miss Gregory|Rosamond)",

        # Named speaker + verb
        rf"\b(Mr\.\s+Syme|the poet Syme|poet Syme|Syme)"
        rf"\s+(?:{VERBS})\b",

        rf"\b(Mr\.\s+Gregory|Comrade Gregory|Gregory)"
        rf"\s+(?:{VERBS})\b",

        rf"\b(Miss Gregory|Rosamond)"
        rf"\s+(?:{VERBS})\b",
    ]

    named_match = None

    for pattern in named_patterns:

        match = re.search(
            pattern,
            immediate,
            flags=re.IGNORECASE
        )

        if match:
            named_match = match
            break

    verb = find_verb(immediate)

    if named_match is not None:

        matched_text = named_match.group(0)

        speaker_name = None

        lower_match = matched_text.lower()

        if (
            "syme" in lower_match
        ):
            speaker_name = "Syme"

        elif (
            "gregory" in lower_match
        ):
            if "miss gregory" in lower_match:
                speaker_name = "Rosamond Gregory"
            else:
                speaker_name = "Gregory"

        elif (
            "rosamond" in lower_match
        ):
            speaker_name = "Rosamond Gregory"

        # -------------------------------------------------
        # Check whether this is actually:
        #
        # "he said to Gregory"
        #
        # rather than:
        #
        # "said Gregory"
        # -------------------------------------------------

        target_match = re.search(
            r"\bto\s+"
            r"(Mr\.\s+Syme|the poet Syme|Syme|"
            r"Mr\.\s+Gregory|Comrade Gregory|Gregory|"
            r"Miss Gregory|Rosamond)\b",
            immediate,
            flags=re.IGNORECASE
        )

        if target_match:

            target_text = (
                target_match.group(1)
            )

            target_lower = (
                target_text.lower()
            )

            if "syme" in target_lower:
                target = "Syme"

            elif (
                "miss gregory" in target_lower
                or "rosamond" in target_lower
            ):
                target = "Rosamond Gregory"

            else:
                target = "Gregory"

            return {
                "attribution_type":
                    "pronoun_speaker_named_target",

                "speaker_evidence":
                    "pronoun_speaker",

                "speaker_name":
                    "Unknown",

                "attribution_verb":
                    verb or "",

                "attribution_target":
                    target,

                "attribution_text":
                    immediate
            }

        return {
            "attribution_type":
                "named_speaker",

            "speaker_evidence":
                "named_speaker",

            "speaker_name":
                speaker_name or "Unknown",

            "attribution_verb":
                verb or "",

            "attribution_target":
                "",

            "attribution_text":
                immediate
        }


    # -----------------------------------------------------
    # Role-based speaker
    #
    # IMPORTANT:
    # Role must be directly attached to the attribution
    # verb. A later narrative mention is not enough.
    # -----------------------------------------------------

    role_patterns = [

        rf"\b(?:{VERBS})\s+"
        rf"(the girl|the man|the policeman|"
        rf"the Professor|the Secretary|the Colonel|"
        rf"the President|the Marquis|the other)",

        rf"\b(the girl|the man|the policeman|"
        rf"the Professor|the Secretary|the Colonel|"
        rf"the President|the Marquis|the other)"
        rf"\s+(?:{VERBS})\b",
    ]

    role_match = None

    for pattern in role_patterns:

        match = re.search(
            pattern,
            immediate,
            flags=re.IGNORECASE
        )

        if match:
            role_match = match
            break

    if role_match is not None:

        role = role_match.group(1)

        return {
            "attribution_type":
                "role_speaker",

            "speaker_evidence":
                "role_speaker",

            "speaker_name":
                role,

            "attribution_verb":
                verb or "",

            "attribution_target":
                "",

            "attribution_text":
                immediate
        }


    # -----------------------------------------------------
    # Pronoun speaker
    #
    # Examples:
    #
    # "he said,"
    # "she asked."
    # "he cried;"
    # -----------------------------------------------------

    pronoun_match = re.match(
        rf"^(?:[,;:\s]*)"
        rf"(he|she)\s+"
        rf"(?:{VERBS})\b",
        immediate,
        flags=re.IGNORECASE
    )

    if pronoun_match:

        pronoun = (
            pronoun_match
            .group(1)
            .lower()
        )

        target = ""

        target_match = re.search(
            r"\bto\s+"
            r"(Mr\.\s+Syme|the poet Syme|Syme|"
            r"Mr\.\s+Gregory|Comrade Gregory|Gregory|"
            r"Miss Gregory|Rosamond)\b",
            immediate,
            flags=re.IGNORECASE
        )

        if target_match:

            target_text = (
                target_match.group(1)
            )

            target_lower = (
                target_text.lower()
            )

            if "syme" in target_lower:
                target = "Syme"

            elif (
                "miss gregory" in target_lower
                or "rosamond" in target_lower
            ):
                target = "Rosamond Gregory"

            else:
                target = "Gregory"

        return {
            "attribution_type":
                (
                    "pronoun_speaker_named_target"
                    if target
                    else "pronoun_speaker"
                ),

            "speaker_evidence":
                "pronoun_speaker",

            "speaker_name":
                "Unknown",

            "attribution_verb":
                verb or "",

            "attribution_target":
                target,

            "attribution_text":
                immediate
        }


    # -----------------------------------------------------
    # Verb-only attribution
    # -----------------------------------------------------

    verb_only_match = re.match(
        rf"^(?:[,;:\s]*)"
        rf"(?:{VERBS})\b",
        immediate,
        flags=re.IGNORECASE
    )

    if verb_only_match:

        return {
            "attribution_type":
                "unresolved_attribution",

            "speaker_evidence":
                "verb_only",

            "speaker_name":
                "Unknown",

            "attribution_verb":
                verb or "",

            "attribution_target":
                "",

            "attribution_text":
                immediate
        }


    # -----------------------------------------------------
    # No immediate attribution
    # -----------------------------------------------------

    return {
        "attribution_type":
            "none",

        "speaker_evidence":
            "none",

        "speaker_name":
            "Unknown",

        "attribution_verb":
            "",

        "attribution_target":
            "",

        "attribution_text":
            ""
    }

    if (
        named is not None
        and verb is not None
    ):

        # Detect whether the named person is the
        # listener rather than the speaker.
        #
        # Example:
        # "he said to Gregory"
        #
        # In that construction Gregory is the target,
        # not the speaker.
        to_target = re.search(
            rf"\bto\s+{re.escape(named)}\b",
            local,
            flags=re.IGNORECASE
        )

        return {
            "attribution_type":
                (
                    "named_speaker_with_target"
                    if not to_target
                    else "pronoun_speaker_named_target"
                ),

            "speaker_evidence":
                (
                    "named_speaker"
                    if not to_target
                    else "pronoun_speaker"
                ),

            "speaker_name":
                (
                    named
                    if not to_target
                    else "Unknown"
                ),

            "attribution_verb":
                verb,

            "attribution_target":
                (
                    named
                    if to_target
                    else ""
                ),

            "attribution_text":
                local
        }


    # -----------------------------------------------------
    # Role-based speaker
    # -----------------------------------------------------

    role = find_role_speaker(
        local
    )

    if (
        role is not None
        and verb is not None
    ):

        return {
            "attribution_type":
                "role_speaker",

            "speaker_evidence":
                "role_speaker",

            "speaker_name":
                role,

            "attribution_verb":
                verb,

            "attribution_target":
                "",

            "attribution_text":
                local
        }


    # -----------------------------------------------------
    # Pronoun speaker
    #
    # Examples:
    #
    # he said
    # he cried
    # she asked
    # -----------------------------------------------------

    pronoun_match = re.match(
        rf"^(?:[,;:\s]*)"
        rf"(he|she)\s+"
        rf"(?:{VERBS})\b",
        local,
        flags=re.IGNORECASE
    )

    if pronoun_match:

        pronoun = (
            pronoun_match
            .group(1)
            .lower()
        )

        # Look for "to NAME" in the same local
        # attribution.
        target_name = find_named_speaker(
            local
        )

        target_match = re.search(
            r"\bto\s+"
            r"([A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*)",
            local
        )

        target = ""

        if target_match:

            target = normalize_space(
                target_match.group(1)
            )

        return {
            "attribution_type":
                (
                    "pronoun_speaker_with_target"
                    if target
                    else "pronoun_speaker"
                ),

            "speaker_evidence":
                "pronoun_speaker",

            "speaker_name":
                "Unknown",

            "attribution_verb":
                find_verb(local),

            "attribution_target":
                target,

            "attribution_text":
                local
        }


    # -----------------------------------------------------
    # Attribution verb exists but speaker cannot
    # be identified.
    # -----------------------------------------------------

    if verb is not None:

        # Only classify as attribution if the verb
        # occurs very close to the beginning of the gap.
        beginning = local[:100]

        if re.match(
            rf"^(?:[,;:\s]*)"
            rf"(?:{VERBS})\b",
            beginning,
            flags=re.IGNORECASE
        ):

            return {
                "attribution_type":
                    "unresolved_attribution",

                "speaker_evidence":
                    "verb_only",

                "speaker_name":
                    "Unknown",

                "attribution_verb":
                    verb,

                "attribution_target":
                    "",

                "attribution_text":
                    local
            }


    # -----------------------------------------------------
    # No local attribution
    # -----------------------------------------------------

    return {
        "attribution_type":
            "none",

        "speaker_evidence":
            "none",

        "speaker_name":
            "Unknown",

        "attribution_verb":
            "",

        "attribution_target":
            "",

        "attribution_text":
            ""
    }


# =========================================================
# LOAD SOURCE
# =========================================================

print(
    "MWT candidate attribution map"
)

print(
    "============================"
)

print()

candidates = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

candidates = candidates.sort_values(
    ["start_char", "end_char"]
).reset_index(
    drop=True
)

print(
    f"Candidate spans: "
    f"{len(candidates):,}"
)

print()


# =========================================================
# ANALYZE EVERY CANDIDATE
# =========================================================

rows = []

for i, row in candidates.iterrows():

    candidate_id = str(
        row["candidate_id"]
    )

    start_char = int(
        row["start_char"]
    )

    end_char = int(
        row["end_char"]
    )

    quoted_text = str(
        row["quoted_text"]
    )

    # -----------------------------------------------------
    # Text between this candidate and the next candidate
    # -----------------------------------------------------

    if i < len(candidates) - 1:

        next_start = int(
            candidates.iloc[
                i + 1
            ]["start_char"]
        )

        gap = clean_text[
            end_char:next_start
        ]

    else:

        gap = clean_text[
            end_char:
        ]

    analysis = analyze_gap(
        gap
    )


    # -----------------------------------------------------
    # Known narrative false positive
    # -----------------------------------------------------

    is_narrative_quote = (
        quoted_text.strip()
        == "artists,"
    )


    if is_narrative_quote:

        analysis[
            "attribution_type"
        ] = "narrative_quote"

        analysis[
            "speaker_evidence"
        ] = "not_dialogue"

        analysis[
            "speaker_name"
        ] = "Unknown"


    rows.append({

        "candidate_id":
            candidate_id,

        "start_line":
            row["start_line"],

        "end_line":
            row["end_line"],

        "start_char":
            start_char,

        "end_char":
            end_char,

        "quoted_text":
            quoted_text,

        "attribution_type":
            analysis[
                "attribution_type"
            ],

        "speaker_evidence":
            analysis[
                "speaker_evidence"
            ],

        "speaker_name":
            analysis[
                "speaker_name"
            ],

        "attribution_verb":
            analysis[
                "attribution_verb"
            ],

        "attribution_target":
            analysis[
                "attribution_target"
            ],

        "attribution_text":
            analysis[
                "attribution_text"
            ],

        "gap_text":
            normalize_space(
                gap[:500]
            ),

        "is_narrative_quote":
            is_narrative_quote
    })


# =========================================================
# SAVE
# =========================================================

out = pd.DataFrame(
    rows
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
    "ATTRIBUTION TYPE COUNTS"
)

print(
    "-----------------------"
)

print(
    out[
        "attribution_type"
    ]
    .value_counts()
    .to_string()
)

print()

print(
    "SPEAKER EVIDENCE COUNTS"
)

print(
    "----------------------"
)

print(
    out[
        "speaker_evidence"
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
        "speaker_name"
    ]
    .value_counts()
    .head(30)
    .to_string()
)

print()


# =========================================================
# IMPORTANT EXAMPLES
# =========================================================

example_ids = [
    "MWT_C00040",
    "MWT_C00041",
    "MWT_C00043",
    "MWT_C00044",
    "MWT_C00045",
    "MWT_C00046",
    "MWT_C00047",
    "MWT_C00048",
    "MWT_C00049",
    "MWT_C00084",
    "MWT_C00085",
    "MWT_C00091",
    "MWT_C00092",
]


print(
    "KEY EXAMPLES"
)

print(
    "------------"
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
        f"{cid}"
    )

    print(
        "  QUOTE:",
        row["quoted_text"]
    )

    print(
        "  TYPE:",
        row["attribution_type"]
    )

    print(
        "  SPEAKER:",
        row["speaker_name"]
    )

    print(
        "  VERB:",
        row["attribution_verb"]
    )

    print(
        "  TARGET:",
        row["attribution_target"]
    )

    print(
        "  GAP:",
        row["gap_text"][:300]
    )


print()

print(
    "Attribution map complete."
)

print(
    f"Output: {OUTPUT_FILE}"
)