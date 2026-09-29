import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v1.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v1_audit.csv"
)


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

print("Auditing MWT dialogue turns v1...")
print()

df = pd.read_csv(INPUT_FILE)

print(f"Turn rows loaded: {len(df):,}")
print()


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def text_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def has_bad_speaker(speaker):
    s = text_value(speaker)

    if not s:
        return True

    bad_patterns = [
        s.startswith("”"),
        s.startswith('"'),
        s.startswith("'"),

        s.lower() in {
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
            "girl",
            "th",
        },

        s.lower().startswith("out "),

        " in a " in f" {s.lower()} ",
        " in an " in f" {s.lower()} ",
        " with " in f" {s.lower()} ",
        "voice" in s.lower(),
        "manner" in s.lower(),
        "tone" in s.lower(),

        "said " in s.lower(),
        "replied " in s.lower(),
        "asked " in s.lower(),
        "cried " in s.lower(),
        "shouted " in s.lower(),
        "exclaimed " in s.lower(),
        "inquired " in s.lower(),
        "answered " in s.lower(),
        "remarked " in s.lower(),
    ]

    return any(bad_patterns)


def has_possible_multi_speaker_turn(text):
    s = text_value(text).lower()

    attribution_verbs = [
        " said ",
        " replied ",
        " asked ",
        " cried ",
        " shouted ",
        " exclaimed ",
        " inquired ",
        " answered ",
        " remarked ",
        " observed ",
        " whispered ",
        " muttered ",
        " demanded ",
        " retorted ",
    ]

    count = sum(s.count(v) for v in attribution_verbs)

    return count >= 2


def looks_like_embedded_or_narrative_quote(text):
    s = text_value(text).strip().lower()

    suspicious = [
        s == "artists,",
        s.startswith("the whole was"),
        s.startswith("the word "),
        "called" in s and len(s) < 150,
    ]

    return any(suspicious)


# ---------------------------------------------------------
# AUDIT
# ---------------------------------------------------------

audit_rows = []

for _, row in df.iterrows():

    speaker = text_value(row.get("speaker"))
    text = text_value(row.get("quoted_text"))

    flags = []

    # -----------------------------------------------------
    # 1. BAD / MALFORMED SPEAKER
    # -----------------------------------------------------

    if has_bad_speaker(speaker):
        flags.append("bad_speaker")

    # -----------------------------------------------------
    # 2. SHORT / UNVERIFIED SPEAKER
    # -----------------------------------------------------

    if speaker and len(speaker.split()) <= 1:

        known_single_names = {
            "Gregory",
            "Syme",
            "Rosamond",
            "Lucian",
            "Professor",
            "Colonel",
            "Secretary",
            "President",
        }

        if speaker not in known_single_names:
            flags.append("short_or_unverified_speaker")

    # -----------------------------------------------------
    # 3. POSSIBLE MULTIPLE SPEAKERS
    # -----------------------------------------------------

    if has_possible_multi_speaker_turn(text):
        flags.append("possible_multiple_speakers")

    # -----------------------------------------------------
    # 4. POSSIBLE NARRATIVE / EMBEDDED QUOTE
    # -----------------------------------------------------

    if looks_like_embedded_or_narrative_quote(text):
        flags.append("possible_narrative_quote")

    # -----------------------------------------------------
    # 5. EMPTY TEXT
    # -----------------------------------------------------

    if not text:
        flags.append("empty_text")

    audit_rows.append({
        "turn_id": text_value(row.get("turn_id")),
        "start_line": text_value(row.get("start_line")),
        "end_line": text_value(row.get("end_line")),
        "speaker": speaker,
        "speaker_evidence": text_value(
            row.get("speaker_evidence")
        ),
        "source_candidate_ids": text_value(
            row.get("source_candidate_ids")
        ),
        "quoted_text": text,
        "extraction_confidence": text_value(
            row.get("extraction_confidence")
        ),
        "audit_flags": ";".join(flags),
        "needs_review": bool(flags),
    })


audit_df = pd.DataFrame(audit_rows)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

audit_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

print("MWT TURN AUDIT SUMMARY")
print("-----------------------")

print(f"Total reconstructed turns: {len(audit_df):,}")

flagged = int(audit_df["needs_review"].sum())

print(f"Turns requiring review:    {flagged:,}")
print(
    f"Turns with no audit flag:  "
    f"{len(audit_df) - flagged:,}"
)
print()

print("AUDIT FLAG COUNTS")
print("-----------------")

flag_counts = {}

for flags in audit_df["audit_flags"]:

    if not flags:
        continue

    for flag in flags.split(";"):
        flag_counts[flag] = (
            flag_counts.get(flag, 0) + 1
        )

for flag, count in sorted(
    flag_counts.items(),
    key=lambda x: (-x[1], x[0])
):
    print(f"{flag}: {count:,}")

print()
print("FIRST 50 FLAGGED TURNS")
print("----------------------")

flagged_df = audit_df[
    audit_df["needs_review"]
].head(50)

for _, row in flagged_df.iterrows():

    preview = row["quoted_text"][:220]

    print(
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['audit_flags']} | "
        f"{preview}"
    )

print()
print("Audit complete.")
print(f"Saved to: {OUTPUT_FILE}")