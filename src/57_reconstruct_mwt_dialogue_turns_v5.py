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
    "the_man_who_was_thursday_dialogue_turns_v5.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_speaker_audit_v5.csv"
)


# =========================================================
# ATTRIBUTION VERBS
# =========================================================

VERBS = (
    "said|replied|answered|asked|cried|exclaimed|"
    "shouted|remarked|observed|continued|added|"
    "returned|called|inquired|demanded|retorted|"
    "whispered|muttered|resumed|assented|"
    "continued|suggested|declared|protested|"
    "urged|murmured|ejaculated"
)


# =========================================================
# SPEAKER NAME NORMALIZATION
# =========================================================

NAME_PATTERNS = [
    (r"\bthe poet Syme\b", "Syme"),
    (r"\bpoet Syme\b", "Syme"),
    (r"\bMr\.?\s+Syme\b", "Syme"),
    (r"\bSyme\b", "Syme"),

    (r"\bMr\.?\s+Gregory\b", "Gregory"),
    (r"\bComrade Gregory\b", "Gregory"),
    (r"\bGregory\b", "Gregory"),

    (r"\bMiss Gregory\b", "Rosamond Gregory"),
    (r"\bRosamond\b", "Rosamond Gregory"),
]


def normalize_space(text):
    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def explicit_name(text):

    for pattern, name in NAME_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return name

    return None


def contains_verb(text):

    return bool(
        re.search(
            rf"\b(?:{VERBS})\b",
            text,
            flags=re.IGNORECASE
        )
    )


def extract_attribution(gap):

    """
    Examine the beginning of the text after a quote.

    Recognizes:

        said Syme
        replied Syme
        he said
        she asked
        cried Gregory
        he cried
        etc.

    """

    text = normalize_space(
        gap[:350]
    )

    if not text:
        return {
            "type": "none",
            "speaker": None,
            "text": ""
        }

    # -----------------------------------------------------
    # Named attribution
    # -----------------------------------------------------

    if contains_verb(text):

        name = explicit_name(text)

        if name:

            return {
                "type":
                    "named_attribution",

                "speaker":
                    name,

                "text":
                    text
            }

    # -----------------------------------------------------
    # Pronoun attribution:
    #
    # "he said"
    # "she asked"
    # "he cried"
    # -----------------------------------------------------

    pronoun_first = re.match(
        rf"^(?:,?\s*)"
        rf"(he|she)\s+"
        rf"(?:{VERBS})\b",
        text,
        flags=re.IGNORECASE
    )

    if pronoun_first:

        return {
            "type":
                "pronoun_attribution",

            "speaker":
                pronoun_first.group(1).lower(),

            "text":
                text
        }

    # -----------------------------------------------------
    # Attribution exists but speaker cannot be resolved
    # -----------------------------------------------------

    if contains_verb(text):

        # Avoid treating ordinary narrative prose as
        # attribution unless the verb occurs immediately
        # near the quotation boundary.

        first_part = text[:120]

        if re.search(
            rf"^(?:,?\s*)"
            rf"(?:{VERBS})\b",
            first_part,
            flags=re.IGNORECASE
        ):

            return {
                "type":
                    "unresolved_attribution",

                "speaker":
                    None,

                "text":
                    text
            }

        if re.search(
            rf"^(?:,?\s*)"
            rf"(?:he|she)\s+"
            rf"(?:{VERBS})\b",
            first_part,
            flags=re.IGNORECASE
        ):

            return {
                "type":
                    "pronoun_attribution",

                "speaker":
                    None,

                "text":
                    text
            }

    return {
        "type": "none",
        "speaker": None,
        "text": ""
    }


# =========================================================
# LOAD
# =========================================================

print(
    "MWT dialogue reconstruction V5"
)

print(
    "=============================="
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
).reset_index(drop=True)

print(
    f"Candidate spans: "
    f"{len(candidates):,}"
)

print()


# =========================================================
# BUILD BOUNDARY INFORMATION
# =========================================================

audit_rows = []

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

    if i < len(candidates) - 1:

        next_start = int(
            candidates.iloc[i + 1]["start_char"]
        )

        gap = clean_text[
            end_char:next_start
        ]

    else:

        gap = clean_text[
            end_char:
        ]

    attr = extract_attribution(
        gap
    )

    # Narrative false positive already observed
    is_narrative_quote = (
        quoted_text.strip()
        == "artists,"
    )

    audit_rows.append({

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

        "gap_text":
            normalize_space(
                gap[:500]
            ),

        "attribution_type":
            attr["type"],

        "attribution_text":
            attr["text"],

        "explicit_speaker":
            attr["speaker"]
            if attr["speaker"]
            else "Unknown",

        "is_narrative_quote":
            is_narrative_quote

    })


audit = pd.DataFrame(
    audit_rows
)


# =========================================================
# RESOLVE PRONOUN ATTRIBUTIONS
# =========================================================

last_known_speaker = None

resolved = []

for _, row in audit.iterrows():

    speaker = row[
        "explicit_speaker"
    ]

    attr_type = row[
        "attribution_type"
    ]

    if (
        attr_type
        == "named_attribution"
    ):

        last_known_speaker = speaker

    elif (
        attr_type
        == "pronoun_attribution"
    ):

        pronoun = (
            row["attribution_text"]
        )

        if re.match(
            r"^he\b",
            pronoun,
            flags=re.IGNORECASE
        ):

            speaker = (
                last_known_speaker
                if last_known_speaker
                else "Unknown"
            )

        elif re.match(
            r"^she\b",
            pronoun,
            flags=re.IGNORECASE
        ):

            # Do not automatically assume a female
            # character. Keep unresolved unless local
            # evidence establishes identity.
            speaker = "Unknown"

    resolved.append(
        speaker
        if speaker != "Unknown"
        else "Unknown"
    )


audit["resolved_speaker"] = (
    resolved
)


# =========================================================
# TURN CONSTRUCTION
#
# Core rule:
#
# A candidate and the immediately following candidate
# belong to the same turn when the gap between them
# contains an attribution identifying the speaker AND
# the following candidate is a continuation rather than
# a new explicitly attributed utterance.
#
# We use the source order and avoid broad speaker
# inheritance.
# =========================================================

turns = []

i = 0

while i < len(audit):

    row = audit.iloc[i]

    # -----------------------------------------------------
    # Ignore known narrative quotation
    # -----------------------------------------------------

    if row["is_narrative_quote"]:

        i += 1
        continue

    group = [
        row
    ]

    speaker = (
        row["resolved_speaker"]
        if row["resolved_speaker"]
        != "Unknown"
        else "Unknown"
    )

    evidence = []

    if (
        row["attribution_type"]
        == "named_attribution"
    ):

        evidence.append(
            "explicit_attribution"
        )

    elif (
        row["attribution_type"]
        == "pronoun_attribution"
    ):

        if speaker != "Unknown":

            evidence.append(
                "pronoun_attribution"
            )

        else:

            evidence.append(
                "unresolved_pronoun"
            )

    # -----------------------------------------------------
    # Look forward through continuation fragments.
    # -----------------------------------------------------

    j = i + 1

    while j < len(audit):

        current = audit.iloc[j - 1]
        nxt = audit.iloc[j]

        if nxt["is_narrative_quote"]:

            break

        gap_type = current[
            "attribution_type"
        ]

        current_speaker = (
            current["resolved_speaker"]
        )

        next_attr = nxt[
            "attribution_type"
        ]

        next_speaker = (
            nxt["resolved_speaker"]
        )

        # -------------------------------------------------
        # If current quote has explicit attribution,
        # the next quoted fragment can be a continuation
        # of that speaker.
        #
        # Example:
        #
        # "Good Lord, no!" he said,
        # "that has to be done anonymously."
        # -------------------------------------------------

        if (
            gap_type
            in (
                "named_attribution",
                "pronoun_attribution"
            )
        ):

            if (
                speaker == "Unknown"
                and current_speaker
                != "Unknown"
            ):

                speaker = current_speaker

            # If next candidate itself has a NEW named
            # attribution, it starts a new turn.
            if (
                next_attr
                == "named_attribution"
                and next_speaker
                != speaker
            ):

                break

            # Otherwise it is treated as continuation.
            group.append(nxt)

            if next_attr == "none":

                evidence.append(
                    "continuation"
                )

            elif (
                next_attr
                == "named_attribution"
            ):

                # Same speaker explicitly attributed
                evidence.append(
                    "repeated_attribution"
                )

            j += 1

            continue

        # -------------------------------------------------
        # If there is no attribution after the current
        # candidate, do NOT blindly merge.
        #
        # This prevents:
        #
        # Syme's quote
        # +
        # Gregory's next quote
        #
        # from being merged merely because the second
        # quote lacks attribution.
        # -------------------------------------------------

        break

    # -----------------------------------------------------
    # Build turn
    # -----------------------------------------------------

    quoted_text = " ".join(
        str(x["quoted_text"])
        for x in group
    )

    candidate_ids = "|".join(
        str(x["candidate_id"])
        for x in group
    )

    turns.append({

        "turn_id":
            f"MWT_T{len(turns)+1:05d}",

        "start_line":
            min(
                int(x["start_line"])
                for x in group
            ),

        "end_line":
            max(
                int(x["end_line"])
                for x in group
            ),

        "speaker":
            speaker,

        "speaker_evidence":
            "|".join(
                sorted(
                    set(evidence)
                )
            ),

        "source_candidate_ids":
            candidate_ids,

        "quoted_text":
            quoted_text,

        "extraction_confidence":
            (
                "high"
                if (
                    speaker != "Unknown"
                    and
                    "explicit_attribution"
                    in evidence
                )
                else "review"
            )

    })

    i = max(
        i + 1,
        j
    )


# =========================================================
# SAVE
# =========================================================

out = pd.DataFrame(
    turns
)

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
print(
    "V5 RECONSTRUCTION SUMMARY"
)

print(
    "--------------------------"
)

print(
    f"Candidate spans: "
    f"{len(audit):,}"
)

print(
    f"Reconstructed turns: "
    f"{len(out):,}"
)

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

print(
    "ATTRIBUTION TYPES"
)

print(
    "------------------"
)

print(
    audit[
        "attribution_type"
    ]
    .value_counts()
    .to_string()
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
    .head(25)
    .to_string()
)

print()

print(
    "FIRST 50 V5 TURNS"
)

print(
    "------------------"
)

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
    "V5 reconstruction complete."
)

print(
    f"Turn file: {OUTPUT_FILE}"
)

print(
    f"Audit file: {AUDIT_FILE}"
)