from pathlib import Path
import csv
import re


CANDIDATE_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_candidates.csv"
)

OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v1.csv"
)


print("Reconstructing MWT dialogue turns...")


if not CANDIDATE_FILE.exists():
    raise FileNotFoundError(
        f"Candidate file not found: {CANDIDATE_FILE}"
    )


with CANDIDATE_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:

    candidates = list(
        csv.DictReader(f)
    )


print()
print("Candidate rows:", len(candidates))


# ---------------------------------------------------------
# Speaker attribution patterns
# ---------------------------------------------------------

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
    "went on",
]

verb_pattern = "|".join(
    re.escape(v)
    for v in speech_verbs
)


# Example:
# “So it is,” said Mr. Syme.
#
# We deliberately capture a larger phrase and
# clean it later rather than assuming the first
# token is the speaker.

after_quote_pattern = re.compile(
    rf'[”]\s*,?\s*'
    rf'(?P<verb>{verb_pattern})\s+'
    rf'(?P<speaker>[^,.;!?:\n]+)',
    re.IGNORECASE
)


before_quote_pattern = re.compile(
    rf'(?P<speaker>[^,.;!?:\n]+?)\s+'
    rf'(?P<verb>{verb_pattern})\s*,?\s*[“]',
    re.IGNORECASE
)


# ---------------------------------------------------------
# Speaker cleanup
# ---------------------------------------------------------

def clean_speaker(raw):
    """
    Convert attribution phrase into a probable speaker name.

    This is intentionally conservative.
    """

    if not raw:
        return ""

    speaker = raw.strip()

    # Remove common descriptive tails.
    speaker = re.split(
        r"\s+(?:sarcastically|superciliously|"
        r"irritably|grimly|gently|"
        r"passionately|angrily|quietly|"
        r"sadly|abruptly|"
        r"in a dangerous voice|"
        r"with passion|"
        r"with knotted fists)\b",
        speaker,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0].strip()

    # Remove leading attribution words.
    speaker = re.sub(
        r"^(the|a)\s+",
        "",
        speaker,
        flags=re.IGNORECASE
    )

    return speaker


# ---------------------------------------------------------
# Determine speaker evidence
# ---------------------------------------------------------

def find_speaker(text):

    match = after_quote_pattern.search(text)

    if match:
        speaker = clean_speaker(
            match.group("speaker")
        )

        # Reject obvious non-speaker phrases.
        rejected = [
            "in a dangerous voice",
            "in a low voice",
            "with passion",
            "with a smile",
            "with knotted fists",
            "sarcastically",
            "superciliously",
            "irritably",
            "grimly",
        ]

        if speaker.lower() not in rejected:
            return (
                speaker,
                "explicit_attribution"
            )

    match = before_quote_pattern.search(text)

    if match:
        speaker = clean_speaker(
            match.group("speaker")
        )

        if speaker:
            return (
                speaker,
                "explicit_attribution"
            )

    return (
        "Unknown",
        "review"
    )


# ---------------------------------------------------------
# Group candidates
# ---------------------------------------------------------

turns = []

current = None


for candidate in candidates:

    quoted = candidate["quoted_text"].strip()

    start_line = int(
        candidate["start_line"]
    )

    end_line = int(
        candidate["end_line"]
    )

    speaker, evidence = find_speaker(
        candidate["surrounding_context"]
    )


    # Candidate immediately continues the
    # previous quoted material when its
    # surrounding context shows that the
    # previous quotation was interrupted by
    # attribution.
    #
    # We detect the common pattern:
    #
    # “first part,” said X, “second part”
    #
    # by checking whether the candidate starts
    # close to the previous candidate.

    continuation = False

    if current is not None:

        previous_end_line = current["end_line"]

        line_gap = start_line - previous_end_line

        if line_gap <= 4:

            # If this candidate has no independent
            # explicit speaker attribution, it is
            # a strong continuation candidate.

            if evidence == "review":

                continuation = True

            # If it has the same explicit speaker,
            # it can also be continuation material.

            elif speaker == current["speaker"]:

                continuation = True


    if continuation:

        current["quoted_text"] += " " + quoted

        current["end_line"] = end_line

        current["source_candidate_ids"].append(
            candidate["candidate_id"]
        )

        if (
            current["speaker"] == "Unknown"
            and speaker != "Unknown"
        ):
            current["speaker"] = speaker
            current["speaker_evidence"] = evidence

    else:

        if current is not None:
            turns.append(current)

        current = {
            "turn_id": f"MWT_T{len(turns)+1:05d}",
            "start_line": start_line,
            "end_line": end_line,
            "speaker": speaker,
            "speaker_evidence": evidence,
            "source_candidate_ids": [
                candidate["candidate_id"]
            ],
            "quoted_text": quoted,
            "extraction_confidence": (
                "high"
                if evidence == "explicit_attribution"
                else "review"
            ),
        }


if current is not None:
    turns.append(current)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

fieldnames = [
    "turn_id",
    "start_line",
    "end_line",
    "speaker",
    "speaker_evidence",
    "source_candidate_ids",
    "quoted_text",
    "extraction_confidence",
]


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


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

    for turn in turns:

        output_row = turn.copy()

        output_row[
            "source_candidate_ids"
        ] = "|".join(
            turn["source_candidate_ids"]
        )

        writer.writerow(
            output_row
        )


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

high = sum(
    1
    for turn in turns
    if turn["extraction_confidence"] == "high"
)

review = sum(
    1
    for turn in turns
    if turn["extraction_confidence"] == "review"
)

known = sum(
    1
    for turn in turns
    if turn["speaker"] != "Unknown"
)


print()
print("TURN RECONSTRUCTION SUMMARY")
print("---------------------------")
print(f"Candidate spans: {len(candidates):,}")
print(f"Reconstructed turns: {len(turns):,}")
print(f"Known speakers: {known:,}")
print(f"Unknown speakers: {len(turns)-known:,}")
print(f"High confidence: {high:,}")
print(f"Review: {review:,}")


print()
print("FIRST 30 RECONSTRUCTED TURNS")
print("-----------------------------")


for turn in turns[:30]:

    preview = turn["quoted_text"].replace(
        "\n",
        " "
    )

    if len(preview) > 180:
        preview = preview[:180] + "..."

    print(
        f'{turn["turn_id"]} | '
        f'{turn["speaker"]} | '
        f'{turn["speaker_evidence"]} | '
        f'{turn["extraction_confidence"]} | '
        f'{preview}'
    )


print()
print("MWT turn reconstruction complete.")
print(f"Saved to: {OUTPUT_FILE}")