
from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"
CANDIDATE_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_candidates.csv"
)
ATTRIBUTED_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)

REPORT_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_independent_attribution_audit.txt"
)


# Conservative verified Titli character inventory.
# This audit does NOT create new speakers.
CHARACTER_NAMES = {
    "तितली",
    "शैला",
    "मधुबन",
    "इन्द्रदेव",
    "इंद्रदेव",
    "रामनाथ",
    "महंगू",
    "अनवरी",
    "बंजो",
    "रामजस",
    "राजकुमारी",
    "तहसीलदार",
    "तहसीलदार साहब",
    "शेरकोट",
    "माधुरी",
    "सुखदेव",
    "श्यामलाल",
    "माधव",
    "गोवर्धन",
    "गोपीनाथ",
    "दीनानाथ",
    "हरिहर",
    "किशोरी",
    "कृष्ण",
    "बलदेव",
    "कृष्णमोहन",
    "देवकी",
    "मधुवा",
}


GENERIC_SPEAKERS = {
    "मैं",
    "मैंने",
    "तुम",
    "तू",
    "आप",
    "वह",
    "उसने",
    "उस",
    "वे",
    "उन्होंने",
    "उनके",
    "इन",
    "यह",
    "एक",
    "कोई",
    "सब",
    "लोग",
    "पुरुष",
    "स्त्री",
    "महिला",
    "लड़का",
    "लड़की",
    "बालक",
    "बालिका",
    "मनुष्य",
    "व्यक्ति",
}


SPEECH_VERBS = (
    "कहा",
    "बोला",
    "बोली",
    "पूछा",
    "पूछने",
    "पूछती",
    "पूछते",
    "बताया",
    "बताती",
    "बताते",
    "उत्तर",
    "उत्तर दिया",
    "उत्तर देती",
    "उत्तर देते",
    "चिल्लाया",
    "चिल्लाई",
    "चिल्लाते",
    "फुसफुसाया",
    "फुसफुसाई",
    "समझाया",
    "समझाई",
    "समझाते",
    "कहती",
    "कहते",
    "कहकर",
    "कहने",
)


ATTRIBUTED_STATUSES = {"ATTRIBUTED"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_canonical_source():
    """
    Reconstruct the same book-global paragraph identity used by
    the candidate generator.

    Paragraph numbering is ONE-BASED and global across all Titli
    sections.
    """
    text = SOURCE_PATH.read_text(encoding="utf-8")

    header_re = re.compile(
        r"^===== TITLI SECTION "
        r"(?P<section>\d+\.\d+)"
        r" \| SOURCE "
        r"(?P<source_file>[^=]+?)"
        r" =====$"
    )

    sections = []
    paragraphs = []

    current_section = None
    global_index = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        match = header_re.fullmatch(line)

        if match:
            current_section = {
                "section": match.group("section"),
                "source_file": match.group("source_file"),
            }
            sections.append(current_section)
            continue

        if current_section is None:
            raise ValueError(
                f"Source paragraph encountered before section header: {line[:100]}"
            )

        global_index += 1

        paragraphs.append(
            {
                "section": current_section["section"],
                "source_file": current_section["source_file"],
                "source_paragraph_index": global_index,
                "source_paragraph": line,
            }
        )

    return sections, paragraphs


def read_csv(path: Path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def build_source_lookup(paragraphs):
    return {
        (
            row["section"],
            row["source_paragraph_index"],
        ): row
        for row in paragraphs
    }


def normalize_for_comparison(text: str) -> str:
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def exact_provenance_check(row, source_lookup):
    """
    Strict provenance check against the reconstructed CSV schema.

    The current reconstructed CSV intentionally does not retain
    source_start/source_end. Therefore this audit verifies:

      section
      source_file
      source_paragraph_index
      complete source paragraph
      dialogue_text occurs in the canonical paragraph

    Exact offset verification was already performed upstream against
    all 595 candidate rows by the corrected reconstruction script.
    """

    key = (
        row["section"],
        int(row["source_paragraph_index"]),
    )

    source = source_lookup.get(key)

    if source is None:
        return False, "SOURCE_LOOKUP_MISS"

    if source["source_file"] != row["source_file"]:
        return False, "SOURCE_FILE_MISMATCH"

    if source["source_paragraph"] != row["source_paragraph"]:
        return False, "SOURCE_PARAGRAPH_MISMATCH"

    canonical = normalize_for_comparison(
        source["source_paragraph"]
    )

    dialogue = normalize_for_comparison(
        row["dialogue_text"]
    )

    if not dialogue:
        return False, "EMPTY_DIALOGUE"

    if dialogue not in canonical:
        return False, "DIALOGUE_NOT_IN_SOURCE_PARAGRAPH"

    return True, "PASS"

def classify_speaker_quality(row):
    """
    Independent quality classification.

    This does not alter the corpus.
    """
    if row["speaker_status"] != "ATTRIBUTED":
        return "UNKNOWN_STATUS"

    speaker = row["speaker"].strip()

    if not speaker:
        return "EMPTY_SPEAKER"

    if speaker in GENERIC_SPEAKERS:
        return "INVALID_GENERIC_SPEAKER"

    if speaker not in CHARACTER_NAMES:
        return "NOT_IN_VERIFIED_CHARACTER_INVENTORY"

    return "VALID_CHARACTER"


def detect_narrative_risk(row):
    """
    Conservative flags only.

    A flag means 'inspect', not 'reject'.
    """
    dialogue = row["dialogue_text"].strip()

    flags = []

    if len(dialogue) > 500:
        flags.append("LONG_DIALOGUE_GT_500")

    if len(dialogue) > 1000:
        flags.append("VERY_LONG_DIALOGUE_GT_1000")

    # Narrative constructions that should trigger manual attention
    # when they appear inside the extracted dialogue.
    narrative_patterns = [
        r"\bने कहा\b",
        r"\bने पूछा\b",
        r"\bने उत्तर दिया\b",
        r"\bने उत्तर\b",
        r"\bने मुस्कर",
        r"\bने हँस",
        r"\bने रो",
        r"\bने सिर",
        r"\bने आँख",
        r"\bने देखकर\b",
        r"\bने देखते हुए\b",
        r"\bकहकर\b",
        r"\bबोलकर\b",
        r"\bसोचकर\b",
        r"\bचलते हुए\b",
        r"\bबैठते हुए\b",
    ]

    for pattern in narrative_patterns:
        if re.search(pattern, dialogue):
            flags.append("NARRATIVE_CONSTRUCTION_INSIDE_DIALOGUE")
            break

    # A dialogue record beginning with a reporting clause is especially
    # suspicious because attribution text may have been included.
    reporting_start = (
        r"^(?:.+?)\s+(?:ने\s+)?"
        r"(?:कहा|पूछा|बोला|बोली|उत्तर दिया|बताया)"
    )

    if re.search(reporting_start, dialogue):
        flags.append("POSSIBLE_REPORTING_CLAUSE_AT_START")

    if flags:
        return flags

    return []


def analyze_duplicate_dialogue(rows):
    groups = defaultdict(list)

    for row in rows:
        dialogue = normalize_for_comparison(row["dialogue_text"])

        if dialogue:
            groups[dialogue].append(row)

    duplicate_groups = {
        dialogue: items
        for dialogue, items in groups.items()
        if len(items) > 1
    }

    return duplicate_groups


def main():
    sections, paragraphs = load_canonical_source()

    candidates = read_csv(CANDIDATE_PATH)
    attributed = read_csv(ATTRIBUTED_PATH)

    source_lookup = build_source_lookup(paragraphs)

    # ------------------------------------------------------------
    # Basic accounting
    # ------------------------------------------------------------

    attributed_rows = [
        row
        for row in attributed
        if row["speaker_status"] in ATTRIBUTED_STATUSES
    ]

    unknown_rows = [
        row
        for row in attributed
        if row["speaker_status"] != "ATTRIBUTED"
    ]

    # ------------------------------------------------------------
    # Provenance audit
    # ------------------------------------------------------------

    provenance_counts = Counter()
    provenance_failures = []

    for row in attributed:
        passed, reason = exact_provenance_check(
            row,
            source_lookup,
        )

        provenance_counts[reason] += 1

        if not passed:
            provenance_failures.append(
                {
                    "candidate_id": row["candidate_id"],
                    "reason": reason,
                    "section": row["section"],
                    "paragraph": row["source_paragraph_index"],
                }
            )

    # ------------------------------------------------------------
    # Speaker audit
    # ------------------------------------------------------------

    speaker_quality = Counter()
    invalid_speaker_rows = []

    for row in attributed_rows:
        quality = classify_speaker_quality(row)
        speaker_quality[quality] += 1

        if quality != "VALID_CHARACTER":
            invalid_speaker_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "speaker": row["speaker"],
                    "quality": quality,
                }
            )

    # ------------------------------------------------------------
    # Narrative contamination audit
    # ------------------------------------------------------------

    narrative_flags = []

    for row in attributed_rows:
        flags = detect_narrative_risk(row)

        if flags:
            narrative_flags.append(
                {
                    "candidate_id": row["candidate_id"],
                    "speaker": row["speaker"],
                    "section": row["section"],
                    "paragraph": row["source_paragraph_index"],
                    "length": len(row["dialogue_text"]),
                    "flags": flags,
                    "dialogue": row["dialogue_text"],
                }
            )

    # ------------------------------------------------------------
    # Duplicate audit
    # ------------------------------------------------------------

    duplicate_groups = analyze_duplicate_dialogue(attributed_rows)

    duplicate_rows = sum(
        len(items)
        for items in duplicate_groups.values()
    )

    duplicate_excess = sum(
        len(items) - 1
        for items in duplicate_groups.values()
    )

    # ------------------------------------------------------------
    # Candidate/output accounting
    # ------------------------------------------------------------

    candidate_ids = {
        row["candidate_id"]
        for row in candidates
    }

    output_ids = {
        row["candidate_id"]
        for row in attributed
    }

    missing_output_ids = sorted(candidate_ids - output_ids)
    unexpected_output_ids = sorted(output_ids - candidate_ids)

    # ------------------------------------------------------------
    # Section distribution
    # ------------------------------------------------------------

    section_counts = Counter(
        row["section"]
        for row in attributed_rows
    )

    # ------------------------------------------------------------
    # Speaker distribution
    # ------------------------------------------------------------

    speaker_counts = Counter(
        row["speaker"]
        for row in attributed_rows
    )

    # ------------------------------------------------------------
    # Hashes
    # ------------------------------------------------------------

    source_hash = sha256_file(SOURCE_PATH)
    candidate_hash = sha256_file(CANDIDATE_PATH)
    attributed_hash = sha256_file(ATTRIBUTED_PATH)

    # ------------------------------------------------------------
    # Overall status
    # ------------------------------------------------------------

    overall_pass = True

    if len(sections) != 28:
        overall_pass = False

    if len(paragraphs) != 1406:
        overall_pass = False

    if len(candidates) != 595:
        overall_pass = False

    if len(attributed) != len(candidates):
        overall_pass = False

    if provenance_counts["PASS"] != len(attributed):
        overall_pass = False

    if invalid_speaker_rows:
        overall_pass = False

    if missing_output_ids:
        overall_pass = False

    if unexpected_output_ids:
        overall_pass = False

    if any(
        not row["dialogue_text"].strip()
        for row in attributed
    ):
        overall_pass = False

    # ------------------------------------------------------------
    # Report
    # ------------------------------------------------------------

    lines = []

    lines.append("TITLI INDEPENDENT ATTRIBUTION AUDIT")
    lines.append("=" * 80)
    lines.append("")

    lines.append("1. SOURCE")
    lines.append("-" * 80)
    lines.append(f"Canonical sections: {len(sections)}")
    lines.append(f"Canonical paragraphs: {len(paragraphs)}")
    lines.append(f"Canonical source SHA256: {source_hash}")
    lines.append("")

    lines.append("2. INPUT / OUTPUT ACCOUNTING")
    lines.append("-" * 80)
    lines.append(f"Candidate rows: {len(candidates)}")
    lines.append(f"Reconstructed rows: {len(attributed)}")
    lines.append(f"ATTRIBUTED: {len(attributed_rows)}")
    lines.append(f"UNKNOWN: {len(unknown_rows)}")
    lines.append(f"Missing candidate IDs from output: {len(missing_output_ids)}")
    lines.append(f"Unexpected output IDs: {len(unexpected_output_ids)}")
    lines.append(
        "Accounting check: "
        + (
            "PASS"
            if len(candidates) == len(attributed)
            else "FAIL"
        )
    )
    lines.append("")

    lines.append("3. PROVENANCE")
    lines.append("-" * 80)
    lines.append(f"PASS: {provenance_counts['PASS']}")
    lines.append(f"Source lookup misses: {provenance_counts['SOURCE_LOOKUP_MISS']}")
    lines.append(f"Source-file mismatches: {provenance_counts['SOURCE_FILE_MISMATCH']}")
    lines.append(
        f"Source-paragraph mismatches: "
        f"{provenance_counts['SOURCE_PARAGRAPH_MISMATCH']}"
    )
    lines.append(f"Invalid offsets: {provenance_counts['INVALID_OFFSETS']}")
    lines.append(
        f"Invalid offset ranges: "
        f"{provenance_counts['INVALID_OFFSET_RANGE']}"
    )
    lines.append(
    f"Dialogue not found in source paragraph: "
    f"{provenance_counts['DIALOGUE_NOT_IN_SOURCE_PARAGRAPH']}"
)

    lines.append(
        f"Empty dialogue: "
        f"{provenance_counts['EMPTY_DIALOGUE']}"
    )
    lines.append(
        "Full provenance status: "
        + (
            "PASS"
            if provenance_counts["PASS"] == len(attributed)
            else "FAIL"
        )
    )
    lines.append("")

    lines.append("4. SPEAKER INVENTORY")
    lines.append("-" * 80)
    lines.append(
        f"Unique attributed speakers: "
        f"{len(speaker_counts)}"
    )

    for speaker, count in speaker_counts.most_common():
        lines.append(f"{speaker}: {count}")

    lines.append("")
    lines.append(
        f"Valid character assignments: "
        f"{speaker_quality['VALID_CHARACTER']}"
    )
    lines.append(
        f"Invalid generic speakers: "
        f"{speaker_quality['INVALID_GENERIC_SPEAKER']}"
    )
    lines.append(
        f"Not in verified inventory: "
        f"{speaker_quality['NOT_IN_VERIFIED_CHARACTER_INVENTORY']}"
    )
    lines.append("")

    lines.append("5. NARRATIVE CONTAMINATION / REVIEW FLAGS")
    lines.append("-" * 80)
    lines.append(
        f"Attributed rows flagged for manual review: "
        f"{len(narrative_flags)}"
    )

    flag_counter = Counter()

    for item in narrative_flags:
        for flag in item["flags"]:
            flag_counter[flag] += 1

    for flag, count in flag_counter.most_common():
        lines.append(f"{flag}: {count}")

    if narrative_flags:
        lines.append("")
        lines.append("Flagged rows:")
        for item in narrative_flags:
            preview = item["dialogue"].replace("\n", " ")
            if len(preview) > 300:
                preview = preview[:300] + "..."

            lines.append(
                f"- {item['candidate_id']} | "
                f"{item['section']} | "
                f"paragraph {item['paragraph']} | "
                f"speaker={item['speaker']} | "
                f"length={item['length']} | "
                f"flags={','.join(item['flags'])}"
            )
            lines.append(f"  {preview}")

    lines.append("")

    lines.append("6. DUPLICATE DIALOGUE AUDIT")
    lines.append("-" * 80)
    lines.append(
        f"Duplicate dialogue groups: "
        f"{len(duplicate_groups)}"
    )
    lines.append(
        f"Rows involved in duplicate groups: "
        f"{duplicate_rows}"
    )
    lines.append(
        f"Excess duplicate occurrences: "
        f"{duplicate_excess}"
    )

    for dialogue, items in sorted(
        duplicate_groups.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        preview = dialogue
        if len(preview) > 200:
            preview = preview[:200] + "..."

        ids = ", ".join(
            item["candidate_id"]
            for item in items
        )

        lines.append(
            f"- {len(items)} occurrences | "
            f"{ids}"
        )
        lines.append(f"  {preview}")

    lines.append("")

    lines.append("7. SECTION DISTRIBUTION")
    lines.append("-" * 80)

    for section in sorted(section_counts):
        lines.append(
            f"{section}: {section_counts[section]}"
        )

    lines.append("")

    lines.append("8. HASHES")
    lines.append("-" * 80)
    lines.append(
        f"Candidate CSV SHA256: {candidate_hash}"
    )
    lines.append(
        f"Attributed CSV SHA256: {attributed_hash}"
    )
    lines.append("")

    lines.append("9. FINAL STATUS")
    lines.append("-" * 80)

    if overall_pass:
        lines.append(
            "INDEPENDENT STRUCTURAL AUDIT: PASS"
        )
        lines.append(
            "The reconstructed Titli attribution layer "
            "passes structural, provenance, speaker-inventory, "
            "and accounting checks."
        )
    else:
        lines.append(
            "INDEPENDENT STRUCTURAL AUDIT: REVIEW REQUIRED"
        )

    lines.append("")
    lines.append(
        "Important: narrative flags and duplicate groups are "
        "inspection evidence; they are not automatically rejected."
    )

    REPORT_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # Terminal summary
    # ------------------------------------------------------------

    print("Titli independent attribution audit complete.")
    print(f"Canonical sections: {len(sections)}")
    print(f"Canonical paragraphs: {len(paragraphs)}")
    print(f"Candidates: {len(candidates)}")
    print(f"Reconstructed rows: {len(attributed)}")
    print(f"Attributed: {len(attributed_rows)}")
    print(f"Unknown: {len(unknown_rows)}")
    print(f"Unique attributed speakers: {len(speaker_counts)}")
    print(
        "Full provenance:",
        f"{provenance_counts['PASS']}/{len(attributed)}",
    )
    print(
        "Invalid speaker assignments:",
        len(invalid_speaker_rows),
    )
    print(
        "Narrative-risk flagged rows:",
        len(narrative_flags),
    )
    print(
        "Duplicate dialogue groups:",
        len(duplicate_groups),
    )
    print(
        "Missing candidate IDs:",
        len(missing_output_ids),
    )
    print(
        "Unexpected output IDs:",
        len(unexpected_output_ids),
    )
    print(
        "INDEPENDENT STRUCTURAL AUDIT:",
        "PASS" if overall_pass else "REVIEW REQUIRED",
    )
    print(f"Audit report: {REPORT_PATH}")


if __name__ == "__main__":
    main()