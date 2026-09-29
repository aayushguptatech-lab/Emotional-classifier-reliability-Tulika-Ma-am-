from pathlib import Path
import pandas as pd
import re


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_dialogue_turns_v1.csv"
)

AUDIT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_v1_turn_audit.csv"
)

print("Final structural and critical speaker audit")
print("============================================")
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
# BASIC STRUCTURE
# --------------------------------------------------

print("BASIC STRUCTURAL CHECKS")
print("------------------------")

checks = []


# Duplicate turn IDs
duplicate_turn_ids = int(
    df["turn_id"].duplicated().sum()
)

print(
    "Duplicate turn IDs:",
    duplicate_turn_ids
)

checks.append({
    "audit": "DUPLICATE_TURN_IDS",
    "count": duplicate_turn_ids,
    "status": "PASS" if duplicate_turn_ids == 0 else "FAIL"
})


# Duplicate candidate IDs
duplicate_candidate_ids = int(
    df["candidate_id"].duplicated().sum()
)

print(
    "Duplicate candidate IDs:",
    duplicate_candidate_ids
)

checks.append({
    "audit": "DUPLICATE_CANDIDATE_IDS",
    "count": duplicate_candidate_ids,
    "status": "PASS" if duplicate_candidate_ids == 0 else "FAIL"
})


# Missing speakers
missing_speakers = int(
    df["speaker"].isna().sum()
)

print(
    "Missing speaker values:",
    missing_speakers
)

checks.append({
    "audit": "MISSING_SPEAKERS",
    "count": missing_speakers,
    "status": "PASS" if missing_speakers == 0 else "FAIL"
})


# Empty quoted text
empty_text = int(
    df["quoted_text"]
    .fillna("")
    .astype(str)
    .str.strip()
    .eq("")
    .sum()
)

print(
    "Empty dialogue text:",
    empty_text
)

checks.append({
    "audit": "EMPTY_DIALOGUE_TEXT",
    "count": empty_text,
    "status": "PASS" if empty_text == 0 else "FAIL"
})


# --------------------------------------------------
# SOURCE ORDER
# --------------------------------------------------

print()
print("SOURCE ORDER CHECK")
print("-------------------")

source_order_ok = True
source_order_violations = []

previous_start = None

for _, row in df.iterrows():

    current_start = row["start_char"]

    if pd.isna(current_start):
        source_order_ok = False

        source_order_violations.append({
            "turn_id": row["turn_id"],
            "reason": "MISSING_START_CHAR"
        })

        continue

    if (
        previous_start is not None
        and current_start < previous_start
    ):
        source_order_ok = False

        source_order_violations.append({
            "turn_id": row["turn_id"],
            "reason": "SOURCE_ORDER_REVERSED"
        })

    previous_start = current_start


print(
    "Source-order preserved:",
    source_order_ok
)

checks.append({
    "audit": "SOURCE_ORDER",
    "count": len(source_order_violations),
    "status": "PASS" if source_order_ok else "FAIL"
})


# --------------------------------------------------
# TURN ID SEQUENCE
# --------------------------------------------------

print()
print("TURN ID SEQUENCE CHECK")
print("----------------------")

turn_numbers = []

for value in df["turn_id"]:

    match = re.search(
        r"_T(\d+)$",
        str(value)
    )

    if match:
        turn_numbers.append(
            int(match.group(1))
        )


sequence_violations = 0

if turn_numbers:

    expected = list(
        range(
            min(turn_numbers),
            max(turn_numbers) + 1
        )
    )

    actual = sorted(set(turn_numbers))

    missing_turn_numbers = sorted(
        set(expected) - set(actual)
    )

    sequence_violations = len(
        missing_turn_numbers
    )

else:

    missing_turn_numbers = []


print(
    "Missing turn numbers:",
    sequence_violations
)

if sequence_violations:
    print(
        "Examples:",
        missing_turn_numbers[:20]
    )

checks.append({
    "audit": "TURN_NUMBER_SEQUENCE",
    "count": sequence_violations,
    "status": (
        "PASS"
        if sequence_violations == 0
        else "REVIEW"
    )
})


# --------------------------------------------------
# SPEAKER VALUES
# --------------------------------------------------

print()
print("SPEAKER DISTRIBUTION")
print("--------------------")

print(
    df["speaker"]
    .value_counts()
    .head(60)
)

print()

unknown_count = int(
    (
        df["speaker"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "unknown"
    ).sum()
)

print(
    "Unknown/review turns:",
    unknown_count
)


# --------------------------------------------------
# CRITICAL SPEAKER CONFLICT DETECTION
# --------------------------------------------------

print()
print("CRITICAL SPEAKER CONFLICT AUDIT")
print("--------------------------------")

critical_conflicts = []


# --------------------------------------------------
# RULE 1:
# A single candidate must not have conflicting
# speaker assignments.
# --------------------------------------------------

candidate_groups = (
    df.groupby("candidate_id")["speaker"]
    .apply(
        lambda x:
        sorted(
            set(
                str(v).strip()
                for v in x
                if str(v).strip()
            )
        )
    )
)


for candidate_id, speakers in candidate_groups.items():

    if len(speakers) > 1:

        critical_conflicts.append({
            "type": "CANDIDATE_MULTIPLE_SPEAKERS",
            "candidate_id": candidate_id,
            "speakers": " | ".join(speakers)
        })


# --------------------------------------------------
# RULE 2:
# Same source span must not occur twice.
# --------------------------------------------------

span_groups = (
    df.groupby(
        ["start_char", "end_char"]
    )
    .size()
)

duplicate_spans = (
    span_groups[
        span_groups > 1
    ]
)


for span, count in duplicate_spans.items():

    critical_conflicts.append({
        "type": "DUPLICATE_SOURCE_SPAN",
        "candidate_id": "",
        "speakers": (
            f"{span} occurs {count} times"
        )
    })


# --------------------------------------------------
# RULE 3:
# Dialogue text must not be empty.
# --------------------------------------------------

for _, row in df.iterrows():

    text = str(
        row["quoted_text"]
    ).strip()

    if not text:

        critical_conflicts.append({
            "type": "EMPTY_DIALOGUE",
            "candidate_id": row["candidate_id"],
            "speakers": str(
                row["speaker"]
            )
        })


# --------------------------------------------------
# RULE 4:
# Speaker should never be a raw structural artifact.
# --------------------------------------------------

artifact_patterns = [
    r"^between$",
    r"^and$",
    r"^but$",
    r"^then$",
    r"^after$",
    r"^before$",
    r"^the$",
    r"^a$",
    r"^an$",
    r"^of$",
    r"^to$",
    r"^from$",
    r"^with$",
    r"^in$",
    r"^on$",
    r"^at$",
    r"^for$",
    r"^as$",
    r"^that$",
    r"^which$",
    r"^who$",
    r"^she$",
    r"^he$",
]


for _, row in df.iterrows():

    speaker = str(
        row["speaker"]
    ).strip()

    speaker_lower = speaker.lower()

    for pattern in artifact_patterns:

        if re.fullmatch(
            pattern,
            speaker_lower
        ):

            # Unknown is already allowed.
            # Only flag a named artifact.
            if speaker_lower != "unknown":

                critical_conflicts.append({
                    "type": "STRUCTURAL_SPEAKER_ARTIFACT",
                    "candidate_id": row["candidate_id"],
                    "speakers": speaker
                })

            break


# --------------------------------------------------
# RULE 5:
# Impossible character-span ordering
# --------------------------------------------------

for _, row in df.iterrows():

    start = row["start_char"]
    end = row["end_char"]

    if (
        pd.notna(start)
        and pd.notna(end)
        and end < start
    ):

        critical_conflicts.append({
            "type": "INVALID_CHARACTER_SPAN",
            "candidate_id": row["candidate_id"],
            "speakers": str(
                row["speaker"]
            )
        })


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print(
    "CRITICAL SPEAKER CONFLICTS:",
    len(critical_conflicts)
)

if critical_conflicts:

    print()
    print(
        "FIRST CONFLICTS"
    )
    print(
        "----------------"
    )

    for conflict in critical_conflicts[:30]:

        print(
            conflict
        )

else:

    print(
        "No critical speaker conflicts detected."
    )


# --------------------------------------------------
# TURN STATISTICS
# --------------------------------------------------

print()
print("FINAL TURN STATISTICS")
print("---------------------")

print(
    "Dialogue turns:",
    len(df)
)

print(
    "Unique speakers:",
    df["speaker"].nunique()
)

print(
    "Unknown/review turns:",
    unknown_count
)

print(
    "Duplicate turn IDs:",
    duplicate_turn_ids
)

print(
    "Duplicate candidate IDs:",
    duplicate_candidate_ids
)

print(
    "Missing speaker values:",
    missing_speakers
)

print(
    "Source-order preserved:",
    source_order_ok
)


# --------------------------------------------------
# AUDIT CSV
# --------------------------------------------------

audit_rows = []

for check in checks:

    audit_rows.append({
        "audit_type": check["audit"],
        "count": check["count"],
        "status": check["status"]
    })


audit_rows.append({
    "audit_type": "CRITICAL_SPEAKER_CONFLICTS",
    "count": len(critical_conflicts),
    "status": (
        "PASS"
        if len(critical_conflicts) == 0
        else "FAIL"
    )
})


audit_df = pd.DataFrame(
    audit_rows
)


AUDIT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


audit_df.to_csv(
    AUDIT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("OUTPUT")
print("------")

print(
    AUDIT_FILE
)

print()

if len(critical_conflicts) == 0:

    print(
        "FINAL STRUCTURAL + SPEAKER AUDIT PASSED."
    )

else:

    print(
        "AUDIT REQUIRES REVIEW."
    )