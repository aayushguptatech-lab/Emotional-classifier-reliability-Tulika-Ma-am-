from pathlib import Path
import csv
import re

CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_candidate_speaker_analysis.csv"
)

print("Analyzing candidate speaker evidence...")

if not CANDIDATE_FILE.exists():
    raise FileNotFoundError(
        f"Candidate file not found: {CANDIDATE_FILE}"
    )

rows = []

with CANDIDATE_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print()
print("Candidate rows loaded:", len(rows))

# Common attribution verbs observed in MWT.
speech_verbs = [
    "said",
    "asked",
    "replied",
    "answered",
    "cried",
    "exclaimed",
    "whispered",
    "shouted",
    "murmured",
    "remarked",
    "observed",
    "continued",
    "declared",
    "added",
    "began",
    "called",
    "inquired",
    "demanded",
    "protested",
    "returned",
    "urged",
    "suggested",
    "interrupted",
    "explained",
]

verb_pattern = "|".join(speech_verbs)

# ---------------------------------------------------------
# Evidence patterns
# ---------------------------------------------------------

after_pattern = re.compile(
    rf"[”]\s*,?\s*"
    rf"(?P<verb>{verb_pattern})\s+"
    rf"(?P<speaker>[^,.!?;\n]+)",
    re.IGNORECASE,
)

before_pattern = re.compile(
    rf"(?P<verb>{verb_pattern})\s+"
    rf"(?P<speaker>[^,:\n]+)"
    rf",\s*[“]",
    re.IGNORECASE,
)

pronoun_pattern = re.compile(
    rf"[”]\s*,?\s*"
    rf"(?P<verb>{verb_pattern})\s+"
    rf"(?P<speaker>he|she|they|I|we|you)\b",
    re.IGNORECASE,
)

analysis_rows = []

for row in rows:
    context = row["surrounding_context"]

    evidence_type = "none"
    speaker_evidence = ""
    confidence = "review"

    match = after_pattern.search(context)

    if match:
        evidence_type = "verb_after_quote"
        speaker_evidence = match.group("speaker").strip()
        confidence = "review"

    else:
        match = before_pattern.search(context)

        if match:
            evidence_type = "verb_before_quote"
            speaker_evidence = match.group("speaker").strip()
            confidence = "review"

        else:
            match = pronoun_pattern.search(context)

            if match:
                evidence_type = "pronoun_after_quote"
                speaker_evidence = match.group("speaker").strip()
                confidence = "review"

    analysis_rows.append(
        {
            "candidate_id": row["candidate_id"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "quoted_text": row["quoted_text"],
            "evidence_type": evidence_type,
            "speaker_evidence": speaker_evidence,
            "speaker_confidence": confidence,
        }
    )

# ---------------------------------------------------------
# Save analysis
# ---------------------------------------------------------

fieldnames = [
    "candidate_id",
    "start_line",
    "end_line",
    "quoted_text",
    "evidence_type",
    "speaker_evidence",
    "speaker_confidence",
]

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(analysis_rows)

# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

counts = {}

for row in analysis_rows:
    key = row["evidence_type"]
    counts[key] = counts.get(key, 0) + 1

print()
print("SPEAKER-EVIDENCE SUMMARY")
print("------------------------")

for key, value in sorted(
    counts.items(),
    key=lambda x: (-x[1], x[0])
):
    print(f"{key}: {value:,}")

# ---------------------------------------------------------
# Examples
# ---------------------------------------------------------

print()
print("FIRST 30 CANDIDATES WITH SPEAKER EVIDENCE")
print("------------------------------------------")

shown = 0

for row in analysis_rows:

    if row["evidence_type"] == "none":
        continue

    preview = row["quoted_text"].replace(
        "\n",
        " "
    )

    if len(preview) > 150:
        preview = preview[:150] + "..."

    print(
        f'{row["candidate_id"]} | '
        f'{row["evidence_type"]} | '
        f'{row["speaker_evidence"]} | '
        f'{preview}'
    )

    shown += 1

    if shown >= 30:
        break

print()
print("Candidate speaker analysis complete.")
print(f"Saved to: {OUTPUT_FILE}")