from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v1.csv"
)


print("Auditing proposed speakers in The Old Wives' Tale")
print("=================================================")
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
# ONLY ATTRIBUTED CANDIDATES
# --------------------------------------------------

attributed = df[
    df["candidate_status"]
    ==
    "ATTRIBUTED_DIALOGUE_CANDIDATE"
].copy()


print("ATTRIBUTED CANDIDATES")
print("---------------------")
print(
    f"Count: {len(attributed):,}"
)
print()


# --------------------------------------------------
# SUSPICIOUS LABEL RULES
# --------------------------------------------------

def suspicious_label(label):

    if not label or pd.isna(label):
        return False

    label = str(label).strip()

    # Speaker label should not contain sentence-like
    # continuation words.
    suspicious_words = [
        "then",
        "and",
        "but",
        "with",
        "from",
        "who",
        "when",
        "while",
        "because",
        "as",
        "the next",
        "there",
        "up",
        "down",
        "again",
    ]

    lower = label.lower()

    for word in suspicious_words:

        if re.search(
            rf"\b{re.escape(word)}\b",
            lower
        ):
            return True

    # Speaker label should not contain excessive length.
    if len(label.split()) > 4:
        return True

    # Speaker label should not look like a complete
    # sentence fragment.
    if len(label) > 60:
        return True

    return False


attributed["suspicious"] = (
    attributed["proposed_speaker"]
    .apply(suspicious_label)
)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("SPEAKER LABEL AUDIT")
print("-------------------")

print(
    f"Suspicious proposed speakers: "
    f"{attributed['suspicious'].sum():,}"
)

print(
    f"Apparently clean proposed speakers: "
    f"{(~attributed['suspicious']).sum():,}"
)

print()


# --------------------------------------------------
# PRINT SUSPICIOUS CASES
# --------------------------------------------------

print("SUSPICIOUS PROPOSED SPEAKER CASES")
print("----------------------------------")

suspicious = attributed[
    attributed["suspicious"]
]

for _, row in suspicious.head(100).iterrows():

    preview = " ".join(
        str(
            row["quoted_text"]
        ).split()
    )

    if len(preview) > 220:
        preview = (
            preview[:220]
            + "..."
        )

    print(
        f"{row['candidate_id']}: "
        f'"{preview}"'
    )

    print(
        f"  Proposed speaker: "
        f"{row['proposed_speaker']}"
    )

    print(
        f"  Attribution source: "
        f"{row['attribution_source']}"
    )

    print(
        f"  Raw after attribution: "
        f"{row['speaker_after_raw']}"
    )

    print()


# --------------------------------------------------
# DESCRIPTIVE SPEAKERS
# --------------------------------------------------

print("DESCRIPTIVE SPEAKER LABELS")
print("--------------------------")

descriptive = attributed[
    attributed["proposed_speaker"]
    .astype(str)
    .str.lower()
    .str.startswith("the ")
]

print(
    f"Descriptive labels: "
    f"{len(descriptive):,}"
)

print()

print(
    descriptive[
        "proposed_speaker"
    ].value_counts()
)

print()


# --------------------------------------------------
# TOP CLEAN SPEAKERS
# --------------------------------------------------

clean = attributed[
    ~attributed["suspicious"]
]

print("TOP CLEAN PROPOSED SPEAKERS")
print("---------------------------")

print(
    clean[
        "proposed_speaker"
    ].value_counts()
    .head(50)
)

print()


# --------------------------------------------------
# SAVE AUDIT
# --------------------------------------------------

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_audit_v1.csv"
)

attributed.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("OUTPUT")
print("------")
print(OUTPUT_FILE)
print()

print(
    "PROPOSED SPEAKER AUDIT COMPLETE."
)