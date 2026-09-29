from pathlib import Path
import re
import pandas as pd


INPUT_FILE = Path(
    "data/cleaned/english/the_old_wives_tale_clean.txt"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_candidates.csv"
)


print("Extracting dialogue candidates from The Old Wives' Tale")
print("========================================================")
print()


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


text = INPUT_FILE.read_text(
    encoding="utf-8"
)


# --------------------------------------------------
# STEP 1: FIND ALL STRAIGHT DOUBLE-QUOTED SPANS
# --------------------------------------------------

pattern = re.compile(
    r'"([^"\n]{1,2000})"'
)

matches = list(
    pattern.finditer(text)
)


print("TOTAL QUOTED SPANS")
print("------------------")
print(f"Quoted spans found: {len(matches):,}")
print()


# --------------------------------------------------
# STEP 2: BUILD CANDIDATE RECORDS
# --------------------------------------------------

records = []

speech_verbs = [
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "shouted",
    "whispered",
    "murmured",
    "remarked",
    "observed",
    "continued",
    "added",
    "declared",
    "suggested",
    "began",
    "interrupted",
    "called",
    "demanded",
    "urged",
    "begged",
    "protested",
    "criticized",
]

speech_verbs_pattern = "|".join(
    re.escape(v)
    for v in speech_verbs
)


for index, match in enumerate(
    matches,
    start=1
):

    quoted_text = match.group(1).strip()

    start_char = match.start()
    end_char = match.end()

    # ----------------------------------------------
    # CONTEXT BEFORE
    # ----------------------------------------------

    context_before_start = max(
        0,
        start_char - 250
    )

    context_before = text[
        context_before_start:start_char
    ].replace("\n", " ")

    # ----------------------------------------------
    # CONTEXT AFTER
    # ----------------------------------------------

    context_after_end = min(
        len(text),
        end_char + 250
    )

    context_after = text[
        end_char:context_after_end
    ].replace("\n", " ")

    # ----------------------------------------------
    # ATTRIBUTION AFTER QUOTE
    # ----------------------------------------------

    after_pattern = re.compile(
        rf"^\s*(?:,|\s)*"
        rf"(?P<verb>{speech_verbs_pattern})\b"
        rf"(?P<rest>.{{0,120}})",
        flags=re.IGNORECASE
    )

    after_match = after_pattern.search(
        context_after
    )

    attribution_after = (
        after_match.group(0).strip()
        if after_match
        else ""
    )

    # ----------------------------------------------
    # ATTRIBUTION BEFORE QUOTE
    # ----------------------------------------------

    before_pattern = re.compile(
        rf"(?P<prefix>.{{0,150}}?)"
        rf"\b(?P<verb>{speech_verbs_pattern})"
        rf"\s*(?:said|asked|replied)?"
        rf"\s*[,;:]?\s*$",
        flags=re.IGNORECASE
    )

    before_match = before_pattern.search(
        context_before
    )

    attribution_before = (
        before_match.group(0).strip()
        if before_match
        else ""
    )

    # ----------------------------------------------
    # SIMPLE HEURISTICS
    # ----------------------------------------------

    has_speech_verb_after = bool(
        after_match
    )

    has_speech_verb_before = bool(
        before_match
    )

    # A likely direct-speech candidate if:
    # 1. a speech verb follows the quote, OR
    # 2. a speech verb appears immediately before it.

    likely_dialogue = (
        has_speech_verb_after
        or has_speech_verb_before
    )

    records.append(
        {
            "candidate_id": f"OWT_C{index:05d}",
            "quoted_text": quoted_text,
            "start_char": start_char,
            "end_char": end_char,
            "has_speech_verb_after": (
                has_speech_verb_after
            ),
            "has_speech_verb_before": (
                has_speech_verb_before
            ),
            "likely_dialogue": (
                likely_dialogue
            ),
            "attribution_after": (
                attribution_after
            ),
            "attribution_before": (
                attribution_before
            ),
            "context_before": (
                context_before.strip()
            ),
            "context_after": (
                context_after.strip()
            ),
        }
    )


# --------------------------------------------------
# STEP 3: SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df = pd.DataFrame(records)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# STEP 4: SUMMARY
# --------------------------------------------------

print("CANDIDATE SUMMARY")
print("-----------------")

print(
    f"Total quoted spans: "
    f"{len(df):,}"
)

print(
    f"Likely dialogue candidates: "
    f"{df['likely_dialogue'].sum():,}"
)

print(
    f"Candidates with speech verb after: "
    f"{df['has_speech_verb_after'].sum():,}"
)

print(
    f"Candidates with speech verb before: "
    f"{df['has_speech_verb_before'].sum():,}"
)

print()

print("OUTPUT")
print("------")
print(OUTPUT_FILE)

print()

# --------------------------------------------------
# STEP 5: PRINT SAMPLE CANDIDATES
# --------------------------------------------------

print("SAMPLE LIKELY DIALOGUE CANDIDATES")
print("---------------------------------")

sample_df = df[
    df["likely_dialogue"]
].head(30)

for _, row in sample_df.iterrows():

    preview = " ".join(
        row["quoted_text"].split()
    )

    if len(preview) > 250:
        preview = (
            preview[:250]
            + "..."
        )

    print(
        f"{row['candidate_id']}: "
        f'"{preview}"'
    )

    if row["attribution_after"]:
        print(
            f"  AFTER: "
            f"{row['attribution_after']}"
        )

    if row["attribution_before"]:
        print(
            f"  BEFORE: "
            f"{row['attribution_before']}"
        )

    print()


print(
    "DIALOGUE CANDIDATE EXTRACTION COMPLETE."
)