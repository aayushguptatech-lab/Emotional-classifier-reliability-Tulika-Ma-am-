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
    "the_man_who_was_thursday_dialogue_turns_v3.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_turn_boundary_audit_v3.csv"
)


# =========================================================
# CONFIGURATION
# =========================================================

ATTRIBUTION_VERBS = [
    "said",
    "replied",
    "answered",
    "asked",
    "cried",
    "exclaimed",
    "shouted",
    "remarked",
    "observed",
    "continued",
    "added",
    "returned",
    "called",
    "inquired",
    "demanded",
    "retorted",
    "whispered",
    "muttered",
]


# Known character-name forms encountered in MWT.
# These are normalization rules, not speaker guesses.

NAME_MAP = {
    "mr. syme": "Syme",
    "mr syme": "Syme",
    "the poet syme": "Syme",
    "poet syme": "Syme",
    "syme": "Syme",

    "mr. gregory": "Gregory",
    "mr gregory": "Gregory",
    "comrade gregory": "Gregory",
    "gregory": "Gregory",

    "miss gregory": "Rosamond Gregory",
    "rosamond": "Rosamond Gregory",
}


# =========================================================
# HELPERS
# =========================================================

def clean(value):
    if pd.isna(value):
        return ""
    return str(value)


def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()


def normalize_name(raw):
    """
    Normalize only explicit, recognizable names.
    Never convert a bare pronoun into a person.
    """

    if not raw:
        return None

    s = normalize_space(raw)

    # Remove punctuation around the attribution.
    s = s.strip(" ,;:.-–—")

    # Remove leading attribution verbs.
    verb_pattern = "|".join(
        re.escape(v) for v in ATTRIBUTION_VERBS
    )

    s = re.sub(
        rf"^(?:{verb_pattern})\s+",
        "",
        s,
        flags=re.IGNORECASE,
    )

    s = normalize_space(s)

    lower = s.lower()

    # Exact known names.
    if lower in NAME_MAP:
        return NAME_MAP[lower]

    # Remove common titles when followed by a known name.
    if lower.startswith("mr. syme"):
        return "Syme"

    if lower.startswith("mr syme"):
        return "Syme"

    if lower.startswith("the poet syme"):
        return "Syme"

    if lower.startswith("poet syme"):
        return "Syme"

    if lower.startswith("mr. gregory"):
        return "Gregory"

    if lower.startswith("mr gregory"):
        return "Gregory"

    if lower.startswith("comrade gregory"):
        return "Gregory"

    if lower.startswith("miss gregory"):
        return "Rosamond Gregory"

    # Bare pronouns are deliberately NOT resolved here.
    if lower in {
        "he",
        "she",
        "him",
        "her",
        "they",
        "them",
        "his",
        "their",
    }:
        return None

    # Reject obvious descriptive fragments.
    bad_words = [
        "with ",
        "in a ",
        "in an ",
        "after ",
        "before ",
        "voice",
        "manner",
        "tone",
        "pause",
        "gravity",
        "smile",
        "calm",
        "simply",
        "patiently",
        "firmly",
        "thoughtfully",
        "sardonically",
        "slowly",
        "sternly",
        "politely",
        "heartily",
    ]

    if any(word in lower for word in bad_words):
        return None

    # If it is a long prose fragment, don't force it.
    if len(s.split()) > 5:
        return None

    return None


def extract_explicit_speaker(text):
    """
    Look for an explicit named speaker in an attribution.
    """

    if not text:
        return None

    verb_pattern = "|".join(
        re.escape(v) for v in ATTRIBUTION_VERBS
    )

    # Examples:
    # said Mr. Syme
    # replied Gregory
    # cried the poet Syme
    # asked Miss Gregory

    patterns = [
        rf"(?:{verb_pattern})\s+"
        r"(?:the\s+poet\s+Syme|poet\s+Syme|"
        r"Mr\.\s+Syme|Mr\s+Syme|Syme|"
        r"Mr\.\s+Gregory|Mr\s+Gregory|"
        r"Comrade\s+Gregory|Gregory|"
        r"Miss\s+Gregory|Rosamond)",

        rf"(?:{verb_pattern})\s+"
        r"([^,;:.!?“”]{1,60})",
    ]

    for pattern in patterns:

        matches = list(
            re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

        for match in reversed(matches):

            raw = match.group(0)

            # Remove the verb.
            raw = re.sub(
                rf"^(?:{verb_pattern})\s+",
                "",
                raw,
                flags=re.IGNORECASE,
            )

            speaker = normalize_name(raw)

            if speaker:
                return speaker

    return None


def attribution_present(text):
    if not text:
        return False

    lower = text.lower()

    return any(
        re.search(
            rf"\b{re.escape(v)}\b",
            lower
        )
        for v in ATTRIBUTION_VERBS
    )


def has_quote_start(text):
    return "“" in text or '"' in text


def has_sentence_boundary_before_next_quote(text):
    """
    A full stop followed by an attribution and another
    quotation usually means the preceding quotation has
    ended and the next quotation is a new explicit unit.

    This function is intentionally conservative.
    """

    if not text:
        return False

    # Paragraph break is strong structural evidence.
    if "\n\n" in text:
        return True

    # Sentence-ending punctuation before the next quote.
    if re.search(r"[.!?]\s*(?:[A-Z]|“|$)", text):
        return True

    return False


# =========================================================
# LOAD SOURCE
# =========================================================

print("MWT conservative turn reconstruction v3")
print("---------------------------------------")
print()

candidates = pd.read_csv(
    CANDIDATE_FILE
)

clean_text = CLEAN_FILE.read_text(
    encoding="utf-8"
)

print(
    f"Candidate spans loaded: "
    f"{len(candidates):,}"
)

print(
    f"Clean source characters: "
    f"{len(clean_text):,}"
)

print()


# =========================================================
# SORT CANDIDATES
# =========================================================

candidates = candidates.sort_values(
    by=["start_char", "end_char"]
).reset_index(drop=True)


# =========================================================
# ANALYZE EACH CANDIDATE
# =========================================================

records = []

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
    # Text immediately BEFORE candidate
    # -----------------------------------------------------

    before_start = max(
        0,
        start_char - 500
    )

    before_text = clean_text[
        before_start:start_char
    ]

    # -----------------------------------------------------
    # Text immediately AFTER candidate
    # -----------------------------------------------------

    after_end = min(
        len(clean_text),
        end_char + 500
    )

    after_text = clean_text[
        end_char:after_end
    ]

    # -----------------------------------------------------
    # Gap before next candidate
    # -----------------------------------------------------

    if i < len(candidates) - 1:

        next_start = int(
            candidates.iloc[i + 1]["start_char"]
        )

        gap = clean_text[
            end_char:next_start
        ]

    else:
        gap = ""

    # -----------------------------------------------------
    # Explicit speaker after candidate
    # -----------------------------------------------------

    after_speaker = extract_explicit_speaker(
        after_text
    )

    # -----------------------------------------------------
    # Explicit speaker before candidate
    # -----------------------------------------------------

    before_speaker = extract_explicit_speaker(
        before_text
    )

    # -----------------------------------------------------
    # Is there an attribution in the gap?
    # -----------------------------------------------------

    gap_has_attribution = attribution_present(
        gap
    )

    gap_speaker = extract_explicit_speaker(
        gap
    )

    # -----------------------------------------------------
    # Determine continuation relationship
    # -----------------------------------------------------

    same_speaker_continuation = False

    if (
        gap_has_attribution
        and gap_speaker
        and has_quote_start(gap)
    ):
        same_speaker_continuation = True

    # Example structure:

    # “It may well be,” he said, “it may well...

    # The attribution is between two quotation spans and
    # another quote immediately follows. This is strong
    # evidence that the same speaker continues.

    # -----------------------------------------------------
    # Determine boundary strength
    # -----------------------------------------------------

    if same_speaker_continuation:

        boundary_type = (
            "same_speaker_interrupted_continuation"
        )

        boundary_strength = "strong"

    elif gap_has_attribution:

        boundary_type = (
            "attribution_without_continuation_evidence"
        )

        boundary_strength = "review"

    elif has_sentence_boundary_before_next_quote(gap):

        boundary_type = (
            "possible_new_turn"
        )

        boundary_strength = "review"

    else:

        boundary_type = (
            "no_explicit_boundary_evidence"
        )

        boundary_strength = "review"

    # -----------------------------------------------------
    # Candidate speaker
    # -----------------------------------------------------

    candidate_speaker = (
        after_speaker
        or before_speaker
        or "Unknown"
    )

    # -----------------------------------------------------
    # Narrative candidate
    # -----------------------------------------------------

    narrative = False

    if quoted_text.strip().lower() == "artists,":
        narrative = True

    # -----------------------------------------------------
    # Save diagnostic record
    # -----------------------------------------------------

    records.append({

        "candidate_id": candidate_id,

        "start_char": start_char,

        "end_char": end_char,

        "start_line": row["start_line"],

        "end_line": row["end_line"],

        "quoted_text": quoted_text,

        "candidate_speaker": candidate_speaker,

        "speaker_source": (
            "after_quote"
            if after_speaker
            else (
                "before_quote"
                if before_speaker
                else "none"
            )
        ),

        "gap_text": normalize_space(
            gap[:1000]
        ),

        "gap_speaker": (
            gap_speaker
            if gap_speaker
            else "Unknown"
        ),

        "gap_has_attribution": (
            gap_has_attribution
        ),

        "same_speaker_continuation": (
            same_speaker_continuation
        ),

        "boundary_type": boundary_type,

        "boundary_strength": boundary_strength,

        "is_narrative": narrative,

    })


audit = pd.DataFrame(records)


# =========================================================
# BUILD TURNS
# =========================================================

turns = []

current = []
current_speaker = None
current_evidence = []


def flush_turn():

    global current
    global current_speaker
    global current_evidence

    if not current:
        return

    valid = [
        x for x in current
        if not x["is_narrative"]
    ]

    if not valid:
        current = []
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

    # High confidence only if every merged component has
    # strong same-speaker evidence or explicit attribution.

    if (
        current_speaker
        and all(
            ev in {
                "explicit_attribution",
                "same_speaker_continuation",
            }
            for ev in current_evidence
        )
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

    current = []
    current_speaker = None
    current_evidence = []


for i, row in audit.iterrows():

    if row["is_narrative"]:
        flush_turn()
        continue

    candidate_speaker = row[
        "candidate_speaker"
    ]

    if candidate_speaker == "Unknown":
        candidate_speaker = None

    # -----------------------------------------------------
    # First candidate of a turn
    # -----------------------------------------------------

    if not current:

        current = [
            row.to_dict()
        ]

        if candidate_speaker:
            current_speaker = (
                candidate_speaker
            )

            current_evidence.append(
                "explicit_attribution"
            )

        continue

    # -----------------------------------------------------
    # Should this candidate continue the current turn?
    # -----------------------------------------------------

    previous = audit.iloc[i - 1]

    continuation = bool(
        previous[
            "same_speaker_continuation"
        ]
    )

    if continuation:

        # Strong evidence of interrupted speech.
        current.append(
            row.to_dict()
        )

        # If the gap identified a speaker, use it.
        gap_speaker = previous[
            "gap_speaker"
        ]

        if (
            gap_speaker != "Unknown"
            and current_speaker is None
        ):
            current_speaker = (
                gap_speaker
            )

        current_evidence.append(
            "same_speaker_continuation"
        )

        continue

    # -----------------------------------------------------
    # Otherwise: START A NEW TURN
    # -----------------------------------------------------

    flush_turn()

    current = [
        row.to_dict()
    ]

    if candidate_speaker:

        current_speaker = (
            candidate_speaker
        )

        current_evidence.append(
            "explicit_attribution"
        )


flush_turn()


out = pd.DataFrame(turns)


# =========================================================
# RENUMBER IDS
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

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

audit.to_csv(
    AUDIT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# =========================================================
# SUMMARY
# =========================================================

print()
print("V3 RECONSTRUCTION SUMMARY")
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

print("BOUNDARY TYPES")
print("--------------")

print(
    audit["boundary_type"]
    .value_counts()
    .to_string()
)

print()

print("STRONG SAME-SPEAKER CONTINUATIONS")
print("----------------------------------")

print(
    audit[
        "same_speaker_continuation"
    ].sum()
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

print("FIRST 40 V3 TURNS")
print("------------------")

for _, row in out.head(40).iterrows():

    preview = (
        str(row["quoted_text"])
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
    "V3 reconstruction complete."
)

print(
    f"Turn file: {OUTPUT_FILE}"
)

print(
    f"Boundary audit: {AUDIT_FILE}"
)
