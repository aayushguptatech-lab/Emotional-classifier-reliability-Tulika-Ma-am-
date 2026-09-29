import re
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v2.csv"
)


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

print("Reconstructing MWT dialogue turns v2...")
print()

df = pd.read_csv(INPUT_FILE)

print(f"Candidate rows: {len(df):,}")
print()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_space(text):
    return re.sub(r"\s+", " ", text).strip()


def clean_speaker(raw):
    """
    Convert attribution fragments into a conservative
    speaker name.
    """

    s = clean_text(raw)

    if not s:
        return None

    s = s.strip(" ,;:.-–—")

    # Remove leading quotation artifacts.
    s = re.sub(r'^[”"“‘’\']+\s*', '', s)

    # Remove common attribution verbs.
    s = re.sub(
        r"^(said|replied|answered|asked|cried|"
        r"exclaimed|shouted|remarked|observed|"
        r"continued|added|returned|called|"
        r"inquired|demanded|retorted|whispered|"
        r"muttered)\s+",
        "",
        s,
        flags=re.IGNORECASE,
    )

    # Remove attribution manner phrases.
    s = re.sub(
        r"\s+(?:sarcastically|superciliously|"
        r"irritably|grimly|gently|passionately|"
        r"angrily|quietly|sadly|abruptly|"
        r"patiently|simply|heartily|seriously|"
        r"politely|calmly|with gravity|"
        r"with simplicity|with animation|"
        r"with a beaming smile|with perfect calm|"
        r"with a simple eagerness|"
        r"in a dangerous voice|"
        r"with passion|with knotted fists)\b.*$",
        "",
        s,
        flags=re.IGNORECASE,
    )

    s = normalize_space(s)

    # Remove obvious broken fragments.
    if s.lower() in {
        "mr",
        "mrs",
        "miss",
        "ms",
        "he",
        "she",
        "him",
        "her",
        "it",
        "they",
        "them",
        "th",
        "and",
        "out",
    }:
        return None

    if s.startswith("out "):
        return None

    if s.startswith("”"):
        return None

    # If the result contains obvious prose rather than a name,
    # do not force an attribution.
    bad_phrases = [
        " in a ",
        " in an ",
        " with ",
        "voice",
        "manner",
        "tone",
        "after a pause",
        "only",
        "motionless",
        "staring",
    ]

    lower = s.lower()

    if any(x in lower for x in bad_phrases):
        return None

    return s


# ---------------------------------------------------------
# ATTRIBUTION EXTRACTION
# ---------------------------------------------------------

ATTRIBUTION_VERBS = (
    r"said|replied|answered|asked|cried|exclaimed|"
    r"shouted|remarked|observed|continued|added|"
    r"returned|called|inquired|demanded|retorted|"
    r"whispered|muttered"
)


def extract_after_quote(context):
    """
    Search immediately after a quoted span for attribution.
    """

    if not context:
        return None, "none"

    pattern = re.compile(
        rf"[”\"]\s*,?\s*(?:{ATTRIBUTION_VERBS})\s+"
        r"([^.!?]{1,100}?)(?:[.!?]|,|\s+“|$)",
        re.IGNORECASE,
    )

    match = pattern.search(context)

    if not match:
        return None, "none"

    raw = match.group(1).strip()

    speaker = clean_speaker(raw)

    if speaker:
        return speaker, "after_quote"

    return None, "after_quote_unresolved"


def extract_before_quote(context):
    """
    Search immediately before a quote for:
        NAME said, “...”
    """

    if not context:
        return None, "none"

    pattern = re.compile(
        rf"\b([^“”\"]{{1,80}}?)\s+"
        rf"(?:{ATTRIBUTION_VERBS})\s*,?\s*[“\"]",
        re.IGNORECASE,
    )

    matches = list(pattern.finditer(context))

    if not matches:
        return None, "none"

    raw = matches[-1].group(1).strip()

    speaker = clean_speaker(raw)

    if speaker:
        return speaker, "before_quote"

    return None, "before_quote_unresolved"


# ---------------------------------------------------------
# PROCESS CANDIDATES
# ---------------------------------------------------------

candidate_rows = []

for _, row in df.iterrows():

    candidate_id = clean_text(row.get("candidate_id"))
    quoted_text = clean_text(row.get("quoted_text"))
    context = clean_text(row.get("surrounding_context"))

    speaker = None
    evidence = "unknown"

    # Try attribution after quotation.
    speaker, evidence = extract_after_quote(context)

    # Try attribution before quotation if necessary.
    if speaker is None:
        speaker, evidence = extract_before_quote(context)

    # Narrative / obvious non-dialogue candidate.
    is_narrative = False

    if quoted_text.strip().lower() == "artists,":
        is_narrative = True

    if quoted_text.strip().lower() == "mr. joseph chamberlain.":
        is_narrative = True

    if is_narrative:
        speaker = None
        evidence = "narrative_quote"

    candidate_rows.append({
        "candidate_id": candidate_id,
        "start_line": row.get("start_line"),
        "end_line": row.get("end_line"),
        "quoted_text": quoted_text,
        "surrounding_context": context,
        "candidate_speaker": speaker if speaker else "Unknown",
        "speaker_evidence": evidence,
        "is_narrative": is_narrative,
    })


cand = pd.DataFrame(candidate_rows)


# ---------------------------------------------------------
# CONSERVATIVE SPEAKER NORMALIZATION
# ---------------------------------------------------------

# Known character aliases encountered in this section.
# These are only normalization rules, not guesses.

NAME_NORMALIZATION = {
    "Mr. Syme": "Syme",
    "the poet Syme": "Syme",
    "poet Syme": "Syme",
    "Mr Syme": "Syme",
    "Gregory": "Gregory",
    "Comrade Gregory": "Gregory",
    "Syme": "Syme",
    "Rosamond": "Rosamond",
    "Miss Gregory": "Rosamond",
}


def normalize_known_name(name):
    if not name or name == "Unknown":
        return "Unknown"

    cleaned = normalize_space(name)

    if cleaned in NAME_NORMALIZATION:
        return NAME_NORMALIZATION[cleaned]

    return cleaned


cand["candidate_speaker"] = cand[
    "candidate_speaker"
].apply(normalize_known_name)


# ---------------------------------------------------------
# PROPAGATE ONLY VERY SAFE CONTINUATIONS
# ---------------------------------------------------------

# A continuation candidate without attribution can inherit the
# previous speaker only when:
#
# 1. it immediately follows another candidate,
# 2. there is no new attribution,
# 3. the previous candidate has a reliable named speaker.
#
# This is deliberately conservative.

last_reliable_speaker = None

for i in range(len(cand)):

    speaker = cand.loc[i, "candidate_speaker"]
    evidence = cand.loc[i, "speaker_evidence"]

    if speaker != "Unknown":
        last_reliable_speaker = speaker
        continue

    if cand.loc[i, "is_narrative"]:
        continue

    if last_reliable_speaker is not None:
        # Mark as inherited evidence rather than pretending
        # it was explicitly attributed.
        cand.loc[i, "candidate_speaker"] = last_reliable_speaker
        cand.loc[i, "speaker_evidence"] = (
            "safe_continuation"
        )


# ---------------------------------------------------------
# BUILD CONSERVATIVE TURNS
# ---------------------------------------------------------

turns = []

current_candidates = []
current_speaker = None
current_evidence = None


def flush_turn():

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
        current_evidence = None
        return

    text_parts = [
        x["quoted_text"]
        for x in valid
        if x["quoted_text"]
    ]

    text = " ".join(text_parts)

    candidate_ids = "|".join(
        x["candidate_id"]
        for x in valid
    )

    start_line = min(
        int(x["start_line"])
        for x in valid
        if str(x["start_line"]).isdigit()
    )

    end_line = max(
        int(x["end_line"])
        for x in valid
        if str(x["end_line"]).isdigit()
    )

    # High confidence only when speaker came from explicit
    # attribution and is a normalized known name.
    if (
        current_speaker
        and current_speaker != "Unknown"
        and current_evidence
        in {"after_quote", "before_quote"}
    ):
        confidence = "high"
    else:
        confidence = "review"

    turns.append({
        "turn_id": f"MWT_T{len(turns)+1:05d}",
        "start_line": start_line,
        "end_line": end_line,
        "speaker": (
            current_speaker
            if current_speaker
            else "Unknown"
        ),
        "speaker_evidence": (
            current_evidence
            if current_evidence
            else "unknown"
        ),
        "source_candidate_ids": candidate_ids,
        "quoted_text": text,
        "extraction_confidence": confidence,
    })

    current_candidates = []
    current_speaker = None
    current_evidence = None


for i in range(len(cand)):

    row = cand.iloc[i]

    if row["is_narrative"]:
        flush_turn()
        continue

    speaker = row["candidate_speaker"]
    evidence = row["speaker_evidence"]

    if not current_candidates:

        current_candidates = [row.to_dict()]

        if speaker != "Unknown":
            current_speaker = speaker
            current_evidence = evidence

        continue

    # Explicit attribution to a different speaker means
    # we must start a new turn.
    if (
        speaker != "Unknown"
        and current_speaker is not None
        and speaker != current_speaker
        and evidence in {
            "after_quote",
            "before_quote",
        }
    ):
        flush_turn()

        current_candidates = [row.to_dict()]
        current_speaker = speaker
        current_evidence = evidence
        continue

    # Explicit speaker when current turn has no speaker.
    if (
        speaker != "Unknown"
        and current_speaker is None
    ):
        current_speaker = speaker
        current_evidence = evidence

    current_candidates.append(row.to_dict())


flush_turn()


# ---------------------------------------------------------
# FINAL DATAFRAME
# ---------------------------------------------------------

out = pd.DataFrame(turns)


# ---------------------------------------------------------
# RE-NUMBER IDS
# ---------------------------------------------------------

out["turn_id"] = [
    f"MWT_T{i:05d}"
    for i in range(1, len(out) + 1)
]


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

print()
print("MWT TURN RECONSTRUCTION V2 SUMMARY")
print("----------------------------------")

print(f"Candidate spans: {len(cand):,}")
print(f"Reconstructed turns: {len(out):,}")

known = (
    out["speaker"].notna()
    & (out["speaker"] != "Unknown")
)

print(f"Known speakers: {known.sum():,}")
print(f"Unknown speakers: {(~known).sum():,}")

print()

print("SPEAKER COUNTS")
print("--------------")

print(
    out["speaker"]
    .value_counts()
    .head(20)
    .to_string()
)

print()

print("FIRST 30 V2 TURNS")
print("-----------------")

for _, row in out.head(30).iterrows():

    preview = (
        str(row["quoted_text"])
        .replace("\n", " ")
    )

    print(
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['speaker_evidence']} | "
        f"{row['extraction_confidence']} | "
        f"{preview[:220]}"
    )

print()
print("MWT v2 reconstruction complete.")
print(f"Saved to: {OUTPUT_FILE}")