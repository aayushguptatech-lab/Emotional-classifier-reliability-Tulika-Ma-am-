from __future__ import annotations

import csv
import hashlib
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


# ============================================================================
# WINDOWS UTF-8 OUTPUT
# ============================================================================

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ============================================================================
# PATHS
# ============================================================================

ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_FILE = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_candidates.csv"
)

SOURCE_FILE = (
    ROOT
    / "data"
    / "cleaned"
    / "hindi"
    / "titli_clean.txt"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "titli_dialogue_turns_attributed.csv"
)

REPAIR_VALIDATION_FILE = (
    OUTPUT_DIR
    / "titli_reconstruction_repair_validation.txt"
)

VALIDATION_FILE = (
    OUTPUT_DIR
    / "titli_attribution_validation.txt"
)


# ============================================================================
# TITLI CHARACTER INVENTORY
#
# Conservative inventory. A speaker is attributed only when the name is
# explicitly present in the candidate/source context AND belongs to this
# verified inventory.
# ============================================================================

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


# ============================================================================
# GENERIC / NON-SPEAKER TOKENS
# ============================================================================

GENERIC_SPEAKERS = {
    "वह",
    "उसने",
    "उन्होंने",
    "वे",
    "मैं",
    "हम",
    "तुम",
    "आप",
    "उस",
    "इन",
    "उन",
    "यह",
    "ये",
    "जिसने",
    "जिस",
    "किसी",
    "सब",
    "कोई",
}

KNOWN_PROBLEMATIC_CANDIDATE_IDS = {
    "TITLI-CAND-000026",
    "TITLI-CAND-000047",
    "TITLI-CAND-000048",
    "TITLI-CAND-000049",
    "TITLI-CAND-000069",
    "TITLI-CAND-000078",
    "TITLI-CAND-000092",
    "TITLI-CAND-000099",
    "TITLI-CAND-000100",
    "TITLI-CAND-000101",
    "TITLI-CAND-000103",
    "TITLI-CAND-000186",
    "TITLI-CAND-000191",
    "TITLI-CAND-000198",
    "TITLI-CAND-000202",
    "TITLI-CAND-000388",
    "TITLI-CAND-000468",
}


# ============================================================================
# SPEECH VERBS
# ============================================================================

SPEECH_VERBS = (
    "कहा",
    "कही",
    "कहे",
    "पूछा",
    "पूछी",
    "पूछे",
    "बोला",
    "बोली",
    "बोले",
    "उत्तर दिया",
    "उत्तर देती",
    "उत्तर देते",
    "उत्तर बोला",
    "उत्तर बोली",
    "उत्तर बोले",
    "बताया",
    "बतायी",
    "बताई",
    "बताये",
    "बताए",
    "समझाया",
    "समझायी",
    "समझाई",
    "चिल्लाया",
    "चिल्लायी",
    "चिल्लाई",
    "पुकारा",
    "पुकारते",
    "पुकारती",
    "पुकारते हुए",
)


# ============================================================================
# HELPERS
# ============================================================================

def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_name(name: str) -> str:
    name = normalize_space(name)

    name = re.sub(
        r"^(?:श्री|श्रीमती|कुमारी|सुश्री)\s+",
        "",
        name,
    )

    name = name.strip(
        "—–-,:;।!?\"'“”‘’()[]{} "
    )

    return name


def is_valid_character(name: str) -> bool:
    if not name:
        return False

    if name in GENERIC_SPEAKERS:
        return False

    return name in CHARACTER_NAMES


def find_character_in_text(text: str) -> list[str]:
    found = []

    for name in CHARACTER_NAMES:
        if name in text:
            found.append(name)

    return sorted(
        set(found),
        key=lambda value: (-len(value), value),
    )


# ============================================================================
# CANONICAL TITLI SOURCE LOADER
#
# Current canonical format:
#
# ===== TITLI SECTION 1.1 | SOURCE titli_01.html =====
# paragraph
# paragraph
#
# ===== TITLI SECTION 1.2 | SOURCE titli_02.html =====
# paragraph
# ...
#
# Each non-empty line after a section header is one canonical paragraph.
# ============================================================================

def load_source_paragraphs() -> dict[str, list[dict]]:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Canonical Titli source not found: {SOURCE_FILE}"
        )

    header_re = re.compile(
        r"^===== TITLI SECTION "
        r"(?P<section>\d+\.\d+)"
        r" \| SOURCE "
        r"(?P<source_file>[^=]+?)"
        r" =====$"
    )

    sections: dict[str, list[dict]] = defaultdict(list)

    current_section = None
    current_source_file = None
    paragraph_index = 0

    with SOURCE_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        for raw_line in handle:
            line = raw_line.strip()

            header_match = header_re.match(line)

            if header_match:
                current_section = (
                    header_match.group("section").strip()
                )

                current_source_file = (
                    header_match.group("source_file").strip()
                )

                continue

            if not line.strip():
                continue

            if current_section is None:
                continue

            paragraph_index += 1

            sections[current_section].append(
                {
                    "paragraph_index": paragraph_index,
                    "source_file": current_source_file,
                    "text": line,
                }
            )

    if not sections:
        raise RuntimeError(
            "No Titli sections were parsed from the canonical clean source."
        )

    return dict(sections)


# ============================================================================
# SOURCE LOOKUP
# ============================================================================

def build_source_lookup(
    sections: dict[str, list[dict]]
) -> dict[tuple[str, int], dict]:

    lookup = {}

    for section, paragraphs in sections.items():
        for paragraph in paragraphs:
            lookup[
                (
                    section,
                    paragraph["paragraph_index"],
                )
            ] = paragraph

    return lookup


# ============================================================================
# EXPLICIT ATTRIBUTION PATTERNS
# ============================================================================

def find_explicit_attribution(
    text: str,
):
    """
    Find an explicit named speaker in the source paragraph.

    Accepted examples:

        बंजो ने कहा—
        बंजो ने पूछा—
        बंजो बोली—
        बंजो बोला—

    Only names in CHARACTER_NAMES are accepted.
    """

    verbs = "|".join(
        re.escape(value)
        for value in sorted(
            SPEECH_VERBS,
            key=len,
            reverse=True,
        )
    )

    patterns = [

        # X ने कहा—
        re.compile(
            r"(?P<name>[ऀ-ॿA-Za-z][ऀ-ॿA-Za-z .'-]{0,40}?)"
            r"\s+ने\s+"
            rf"(?P<verb>{verbs})"
            r"\s*(?:—|–|-|:)"
        ),

        # X बोला—
        re.compile(
            r"(?P<name>[ऀ-ॿA-Za-z][ऀ-ॿA-Za-z .'-]{0,40}?)"
            r"\s+"
            rf"(?P<verb>{verbs})"
            r"\s*(?:—|–|-|:)"
        ),

        # —X ने कहा
        re.compile(
            r"(?:—|–|-)\s*"
            r"(?P<name>[ऀ-ॿA-Za-z][ऀ-ॿA-Za-z .'-]{0,40}?)"
            r"\s+ने\s+"
            rf"(?P<verb>{verbs})"
        ),
    ]

    for pattern in patterns:

        for match in pattern.finditer(text):

            raw_name = clean_name(
                match.group("name")
            )

            if not is_valid_character(raw_name):
                continue

            return (
                raw_name,
                match.group(0),
                match.start(),
                "HIGH",
            )

    return None


# ============================================================================
# LOCAL CONTEXT ATTRIBUTION
# ============================================================================

def infer_from_local_context(
    source_paragraph: str,
    candidate_text: str,
    candidate_start: int,
):
    """
    Conservative local attribution.

    Priority:

    1. Explicit named speaker near the candidate.
    2. Explicit named speaker in candidate-local context.
    3. Single verified character immediately before dash dialogue.

    Generic pronouns are never accepted.
    """

    attribution = find_explicit_attribution(
        source_paragraph
    )

    if attribution:

        speaker, evidence, evidence_pos, confidence = (
            attribution
        )

        distance = abs(
            candidate_start - evidence_pos
        )

        if distance <= 500:
            return (
                speaker,
                "explicit_named_attribution",
                evidence,
                confidence,
                "",
            )

    # -----------------------------------------------------------------------
    # Candidate-local context
    # -----------------------------------------------------------------------

    local_start = max(
        0,
        candidate_start - 150,
    )

    local_end = min(
        len(source_paragraph),
        candidate_start + len(candidate_text) + 150,
    )

    local_context = source_paragraph[
        local_start:local_end
    ]

    local_attribution = find_explicit_attribution(
        local_context
    )

    if local_attribution:

        speaker, evidence, _, confidence = (
            local_attribution
        )

        return (
            speaker,
            "local_explicit_named_attribution",
            evidence,
            confidence,
            "",
        )

    # -----------------------------------------------------------------------
    # Named character immediately before dash dialogue
    # -----------------------------------------------------------------------

    if candidate_text.startswith(
        ("—", "-", "–")
    ):

        prefix = source_paragraph[
            max(0, candidate_start - 120):
            candidate_start
        ]

        names = find_character_in_text(
            prefix
        )

        if len(names) == 1:

            return (
                names[0],
                "named_dash_local_context",
                names[0],
                "MEDIUM",
                "Single verified character immediately precedes dash dialogue.",
            )

    return None


# ============================================================================
# STRUCTURAL CONTAMINATION CHECK
# ============================================================================

def structural_contamination_reason(
    row: dict,
    dialogue_text: str,
    source_paragraph: str,
    candidate_start: int,
    proposed_speaker: str,
) -> str:
    detection_method = (row.get("detection_method") or "").strip()

    if detection_method == "multi_turn_paragraph":
        return "candidate_extracted_from_multi_turn_paragraph"

    if re.search(r"_{3,}", dialogue_text):
        return "candidate_contains_extraction_boundary_placeholder"

    names = "|".join(
        re.escape(name)
        for name in sorted(CHARACTER_NAMES, key=len, reverse=True)
    )
    reporting_verbs = (
        r"कहा|कही|कहे|पूछा|पूछी|पूछे|बोला|बोली|बोले|"
        r"उत्तर\s+दिया|उत्तर\s+देती|उत्तर\s+देते|बताया|"
        r"बतायी|बताई|बताये|बताए|कहकर|कहती\s+हुई|कहते\s+हुए"
    )

    if re.search(
        rf"[ऀ-ॿ]{{2,}}(?:\s+[ऀ-ॿ]{{2,}})?\s+ने\s+"
        rf"(?:[^।!?—–]{{0,60}}?\s+)?"
        rf"(?:{reporting_verbs})(?=\s|[।!?—–-]|$)",
        dialogue_text,
    ):
        return "named_speaker_reporting_clause_inside_candidate"

    if re.search(
        r"(?:कहकर|कहती\s+हुई|कहते\s+हुए|बोलकर|"
        r"—\s*कहकर|—\s*कहती\s+हुई|—\s*कहते\s+हुए)",
        dialogue_text,
    ):
        return "narrative_reporting_construction_inside_candidate"

    dash_starts = re.findall(
        r"(?:^|[।!?])\s*[—–-]\s*(?=[ऀ-ॿ])",
        dialogue_text,
    )
    if len(dash_starts) >= 2:
        return "multiple_dialogue_start_markers_inside_candidate"

    # A named reporting clause immediately before the extracted span conflicts
    # with a different proposed speaker and is stronger than broad proximity.
    if is_valid_character(proposed_speaker) and candidate_start > 0:
        prefix_start = max(0, candidate_start - 120)
        prefix = source_paragraph[prefix_start:candidate_start]
        preceding = find_explicit_attribution(prefix)

        if preceding:
            preceding_speaker, evidence, evidence_start, _ = preceding
            evidence_end = evidence_start + len(evidence)
            gap = prefix[evidence_end:]
            aliases = {
                "इन्द्रदेव": "इंद्रदेव",
                "इंद्रदेव": "इंद्रदेव",
            }
            same_speaker = aliases.get(preceding_speaker, preceding_speaker) == aliases.get(
                proposed_speaker,
                proposed_speaker,
            )

            if (
                is_valid_character(preceding_speaker)
                and not same_speaker
                and len(gap) <= 20
                and re.fullmatch(r"[\s—–\-:'\"“”‘’]*", gap)
            ):
                return "adjacent_explicit_attribution_conflicts_with_candidate"

        boundary_attribution = re.search(
            rf"(?P<name>{names})\s+ने\s+"
            rf"(?:[^\s—–-]+\s+){{0,3}}?"
            rf"(?:{reporting_verbs})\s*(?:—|–|-|:)\s*$",
            prefix,
        )
        if boundary_attribution:
            preceding_speaker = boundary_attribution.group("name")
            aliases = {
                "इन्द्रदेव": "इंद्रदेव",
                "इंद्रदेव": "इंद्रदेव",
            }
            if (
                aliases.get(preceding_speaker, preceding_speaker)
                != aliases.get(proposed_speaker, proposed_speaker)
            ):
                return "adjacent_explicit_attribution_conflicts_with_candidate"

    narrative_predicates = (
        r"कटी\s+जा\s+रही\s+थी|कटा\s+जा\s+रहा\s+था|"
        r"रही\s+थी|रहा\s+था|रहे\s+थे|हो\s+उठी|हो\s+उठा|"
        r"घबरा\s+उठी|निकल\s+गई|निकल\s+गया|पहुंच\s+गई|"
        r"पहुंच\s+गया|लौट\s+पड़ी|चल\s+पड़ी|दौड़\s+पड़ी|"
        r"करने\s+लगी|करने\s+लगा|करने\s+लगे|बैठ\s+गई|"
        r"खड़ी\s+हो\s+गई|उठ\s+गई|उठ\s+गया"
    )
    narrative_subject = rf"(?:वह|उसने|उसे|उसको|उसकी|उसके|{names})"
    if re.search(
        rf"(?:^|[।!?]\s*){narrative_subject}"
        rf"[^।!?]{{0,120}}?(?:{narrative_predicates})",
        dialogue_text,
    ):
        return "third_person_narrative_clause_inside_candidate"

    return ""


# ============================================================================
# CANDIDATE CLASSIFICATION
# ============================================================================

def classify_candidate(
    row: dict,
    source_paragraph: str,
):
    dialogue_text = normalize_space(
        row.get("dialogue_text")
        or row.get("candidate_text")
        or ""
    )

    if not dialogue_text:
        return (
            "",
            "REVIEW",
            "LOW",
            "empty_dialogue",
            "",
            "Candidate contains no dialogue text.",
        )

    try:
        candidate_start = int(
            row.get("source_start")
            or 0
        )
    except (TypeError, ValueError):
        candidate_start = 0

    candidate_name = clean_name(
        row.get("attribution_name_candidate")
        or row.get("attribution_name_candidat")
        or ""
    )

    contamination = structural_contamination_reason(
        row,
        dialogue_text,
        source_paragraph,
        candidate_start,
        candidate_name,
    )
    if contamination:
        return (
            "Unknown",
            "REVIEW",
            "LOW",
            "structural_contamination_review",
            "",
            contamination,
        )

    # -----------------------------------------------------------------------
    # First priority:
    # candidate extractor's explicit speaker name
    # -----------------------------------------------------------------------

    if is_valid_character(candidate_name):

        return (
            candidate_name,
            "ATTRIBUTED",
            "HIGH",
            "candidate_explicit_name",
            row.get("attribution_text", ""),
            "",
        )

    # -----------------------------------------------------------------------
    # Second priority:
    # source-context attribution
    # -----------------------------------------------------------------------

    attribution = infer_from_local_context(
        source_paragraph,
        dialogue_text,
        candidate_start,
    )

    if attribution:

        (
            speaker,
            method,
            evidence,
            confidence,
            reason,
        ) = attribution

        if is_valid_character(speaker):

            return (
                speaker,
                "ATTRIBUTED",
                confidence,
                method,
                evidence,
                reason,
            )

    # -----------------------------------------------------------------------
    # Unresolved
    # -----------------------------------------------------------------------

    return (
        "Unknown",
        "UNKNOWN",
        "LOW",
        "unresolved_local_attribution",
        "",
        "No defensible explicit character attribution found.",
    )


# ============================================================================
# PROVENANCE VERIFICATION
# ============================================================================

def candidate_provenance_errors(row, source_lookup):
    section = (row.get("section") or "").strip()

    try:
        paragraph_index = int(row.get("source_paragraph_index") or -1)
        source_start = int(row.get("source_start"))
        source_end = int(row.get("source_end"))
    except (TypeError, ValueError):
        return ["invalid paragraph index or source offsets"]

    source_record = source_lookup.get((section, paragraph_index))
    if source_record is None:
        return ["canonical source paragraph lookup failed"]

    errors = []
    if (row.get("source_file") or "").strip() != source_record["source_file"]:
        errors.append("source_file mismatch")
    if row.get("source_paragraph") != source_record["text"]:
        errors.append("source paragraph text mismatch")

    dialogue_text = row.get("dialogue_text") or ""
    source_text = source_record["text"]
    if source_start < 0 or source_end < source_start or source_end > len(source_text):
        errors.append("source offsets out of bounds")
    elif source_text[source_start:source_end] != dialogue_text:
        errors.append("source slice does not equal dialogue_text")

    return errors


def verify_provenance(
    rows,
    source_lookup,
    sample_size=100,
):

    if not rows:
        return {
            "sample_size": 0,
            "matches": 0,
            "mismatches": 0,
            "details": [],
        }

    random.seed(20260929)

    if len(rows) > sample_size:
        sample = random.sample(
            rows,
            sample_size,
        )
    else:
        sample = rows

    matches = 0
    mismatches = 0
    details = []

    for row in sample:

        errors = candidate_provenance_errors(row, source_lookup)
        if not errors:
            matches += 1
        else:
            mismatches += 1
            details.append(
                f"MISMATCH | {row.get('candidate_id', '')} | "
                f"section={row.get('section', '')} | "
                f"paragraph={row.get('source_paragraph_index', '')} | "
                f"{'; '.join(errors)}"
            )

    return {
        "sample_size": len(sample),
        "matches": matches,
        "mismatches": mismatches,
        "details": details,
    }


# ============================================================================
# FILE HASH
# ============================================================================

def sha256_file(path: Path) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as handle:

        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


# ============================================================================
# MAIN
# ============================================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------------
    # Required inputs
    # ------------------------------------------------------------------------

    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found:\n{CANDIDATE_FILE}"
        )

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Canonical source file not found:\n{SOURCE_FILE}"
        )

    # ------------------------------------------------------------------------
    # Load canonical source
    # ------------------------------------------------------------------------

    sections = load_source_paragraphs()

    source_lookup = build_source_lookup(
        sections
    )

    total_source_paragraphs = sum(
        len(paragraphs)
        for paragraphs in sections.values()
    )

    # ------------------------------------------------------------------------
    # Load candidates
    # ------------------------------------------------------------------------

    candidates = []

    with CANDIDATE_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:

        reader = csv.DictReader(handle)

        for row in reader:
            candidates.append(row)

    # ------------------------------------------------------------------------
    # Reconstruction
    # ------------------------------------------------------------------------

    output_rows = []

    speaker_counter = Counter()
    status_counter = Counter()
    confidence_counter = Counter()
    method_counter = Counter()
    section_counter = Counter()

    invalid_speakers = []
    empty_dialogue = []
    narrative_flags = []

    source_lookup_misses = []
    structural_downgraded = 0

    for index, row in enumerate(
        candidates,
        start=1,
    ):

        candidate_id = (
            row.get("candidate_id")
            or f"TITLI_CAND_{index:05d}"
        )

        section = (
            row.get("section")
            or ""
        ).strip()

        source_file = (
            row.get("source_file")
            or ""
        ).strip()

        try:
            paragraph_index = int(
                row.get("source_paragraph_index")
                or row.get("paragraph_number")
                or 0
            )

        except (TypeError, ValueError):

            paragraph_index = 0

        source_record = source_lookup.get(
            (
                section,
                paragraph_index,
            ),
            None,
        )
        source_paragraph = source_record["text"] if source_record else ""

        if not source_paragraph:

            source_lookup_misses.append(
                (
                    candidate_id,
                    section,
                    paragraph_index,
                )
            )

        dialogue_text = normalize_space(
            row.get("dialogue_text")
            or row.get("candidate_text")
            or ""
        )

        (
            speaker,
            status,
            confidence,
            method,
            evidence,
            reason,
        ) = classify_candidate(
            row,
            source_paragraph,
        )

        if method == "structural_contamination_review":
            structural_downgraded += 1

        # --------------------------------------------------------------------
        # Final speaker validation
        # --------------------------------------------------------------------

        if (
            status == "ATTRIBUTED"
            and not is_valid_character(speaker)
        ):

            invalid_speakers.append(
                (
                    candidate_id,
                    speaker,
                )
            )

            speaker = "Unknown"
            status = "UNKNOWN"
            confidence = "LOW"
            method = "invalid_attribution_rejected"
            evidence = ""
            reason = (
                "Speaker token failed verified character-name validation."
            )

        # --------------------------------------------------------------------
        # Quality flags
        # --------------------------------------------------------------------

        if not dialogue_text:

            empty_dialogue.append(
                candidate_id
            )

        if (
            len(dialogue_text) > 500
            and status != "ATTRIBUTED"
        ):

            narrative_flags.append(
                candidate_id
            )

        # --------------------------------------------------------------------
        # Deterministic turn ID
        # --------------------------------------------------------------------

        turn_id = (
            f"TITLI_TURN_{index:05d}"
        )

        output_rows.append(
            {
                "turn_id": turn_id,
                "candidate_id": candidate_id,
                "section": section,
                "source_file": source_file,
                "source_paragraph_index": paragraph_index,
                "source_paragraph": source_paragraph,
                "dialogue_text": dialogue_text,
                "speaker": speaker,
                "speaker_status": status,
                "confidence": confidence,
                "attribution_method": method,
                "attribution_evidence": evidence,
                "review_reason": reason,
            }
        )

        status_counter[status] += 1
        confidence_counter[confidence] += 1
        method_counter[method] += 1
        section_counter[section] += 1

        if status == "ATTRIBUTED":
            speaker_counter[speaker] += 1

    # =========================================================================
    # WRITE OUTPUT CSV
    # =========================================================================

    previous_output = OUTPUT_FILE.read_bytes() if OUTPUT_FILE.exists() else None

    fieldnames = [
        "turn_id",
        "candidate_id",
        "section",
        "source_file",
        "source_paragraph_index",
        "source_paragraph",
        "dialogue_text",
        "speaker",
        "speaker_status",
        "confidence",
        "attribution_method",
        "attribution_evidence",
        "review_reason",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )

        writer.writeheader()

        for row in output_rows:
            writer.writerow(row)

    reproducibility_match = (
        previous_output is not None
        and previous_output == OUTPUT_FILE.read_bytes()
    )

    # =========================================================================
    # PROVENANCE
    # =========================================================================

    provenance = verify_provenance(
        candidates,
        source_lookup,
        sample_size=100,
    )
    full_provenance_mismatches = [
        (row, candidate_provenance_errors(row, source_lookup))
        for row in candidates
    ]
    full_provenance_mismatches = [
        (row, errors)
        for row, errors in full_provenance_mismatches
        if errors
    ]
    full_provenance_matches = len(candidates) - len(full_provenance_mismatches)

    # =========================================================================
    # DUPLICATE DIALOGUE ANALYSIS
    # =========================================================================

    dialogue_groups = defaultdict(list)

    for row in output_rows:

        text = normalize_space(
            row["dialogue_text"]
        )

        if text:
            dialogue_groups[text].append(
                row["turn_id"]
            )

    duplicate_groups = {
        text: ids
        for text, ids in dialogue_groups.items()
        if len(ids) > 1
    }

    duplicate_rows = sum(
        len(ids)
        for ids in duplicate_groups.values()
    )

    duplicate_excess = sum(
        len(ids) - 1
        for ids in duplicate_groups.values()
    )

    # =========================================================================
    # HASH
    # =========================================================================

    csv_hash = sha256_file(
        OUTPUT_FILE
    )

    # =========================================================================
    # VALIDATION REPORT
    # =========================================================================

    report = []

    report.append(
        "TITLI SPEAKER ATTRIBUTION / DIALOGUE RECONSTRUCTION VALIDATION"
    )
    report.append("=" * 72)
    report.append("")

    report.append(
        f"Candidate input: {CANDIDATE_FILE}"
    )

    report.append(
        f"Canonical source: {SOURCE_FILE}"
    )

    report.append(
        f"Output CSV: {OUTPUT_FILE}"
    )

    report.append("")

    report.append(
        f"Canonical source sections: {len(sections)}"
    )

    report.append(
        f"Canonical source paragraphs: {total_source_paragraphs}"
    )

    report.append(
        f"Input candidates: {len(candidates)}"
    )

    report.append(
        f"Output rows: {len(output_rows)}"
    )

    report.append("")

    # -------------------------------------------------------------------------
    # STATUS
    # -------------------------------------------------------------------------

    report.append(
        "STATUS COUNTS"
    )
    report.append("-" * 72)

    for status, count in sorted(
        status_counter.items()
    ):

        report.append(
            f"{status}: {count}"
        )

    report.append("")

    # -------------------------------------------------------------------------
    # CONFIDENCE
    # -------------------------------------------------------------------------

    report.append(
        "CONFIDENCE COUNTS"
    )
    report.append("-" * 72)

    for confidence, count in sorted(
        confidence_counter.items()
    ):

        report.append(
            f"{confidence}: {count}"
        )

    report.append("")

    # -------------------------------------------------------------------------
    # SPEAKERS
    # -------------------------------------------------------------------------

    report.append(
        "ATTRIBUTED SPEAKER COUNTS"
    )
    report.append("-" * 72)

    if speaker_counter:

        for speaker, count in sorted(
            speaker_counter.items(),
            key=lambda item: (-item[1], item[0]),
        ):

            report.append(
                f"{speaker}: {count}"
            )

    else:

        report.append(
            "None"
        )

    report.append("")

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    report.append(
        "ATTRIBUTION METHODS"
    )
    report.append("-" * 72)

    for method, count in sorted(
        method_counter.items(),
        key=lambda item: (-item[1], item[0]),
    ):

        report.append(
            f"{method}: {count}"
        )

    report.append("")

    # -------------------------------------------------------------------------
    # SECTIONS
    # -------------------------------------------------------------------------

    report.append(
        "SECTION COUNTS"
    )
    report.append("-" * 72)

    for section, count in sorted(
        section_counter.items()
    ):

        report.append(
            f"{section}: {count}"
        )

    report.append("")

    # -------------------------------------------------------------------------
    # SOURCE LOOKUP
    # -------------------------------------------------------------------------

    report.append(
        "SOURCE LOOKUP"
    )
    report.append("-" * 72)

    report.append(
        f"Source lookup misses: {len(source_lookup_misses)}"
    )

    if source_lookup_misses:

        for (
            candidate_id,
            section,
            paragraph_index,
        ) in source_lookup_misses[:25]:

            report.append(
                f"  {candidate_id}: "
                f"section={section}, "
                f"paragraph={paragraph_index}"
            )

    report.append("")

    # -------------------------------------------------------------------------
    # PROVENANCE
    # -------------------------------------------------------------------------

    report.append(
        "PROVENANCE"
    )
    report.append("-" * 72)

    report.append(
        f"Sampled rows: {provenance['sample_size']}"
    )

    report.append(
        f"Exact source matches: {provenance['matches']}"
    )

    report.append(
        f"Source mismatches: {provenance['mismatches']}"
    )

    report.append(
        f"Full candidate provenance matches: "
        f"{full_provenance_matches}/{len(candidates)}"
    )

    report.append(
        f"Full candidate provenance mismatches: "
        f"{len(full_provenance_mismatches)}"
    )

    if provenance["mismatches"] == 0:

        report.append(
            "PROVENANCE STATUS: PASS"
        )

    else:

        report.append(
            "PROVENANCE STATUS: FAIL"
        )

        for detail in provenance["details"][:25]:

            report.append(
                f"  {detail}"
            )

    if full_provenance_mismatches:
        for row, errors in full_provenance_mismatches[:25]:
            report.append(
                f"  FULL FIELD MISMATCH | {row.get('candidate_id', '')} | "
                f"{'; '.join(errors)}"
            )

    report.append("")

    # -------------------------------------------------------------------------
    # SPEAKER VALIDATION
    # -------------------------------------------------------------------------

    report.append(
        "SPEAKER VALIDATION"
    )
    report.append("-" * 72)

    report.append(
        f"Invalid speaker assignments rejected: "
        f"{len(invalid_speakers)}"
    )

    if invalid_speakers:

        for candidate_id, speaker in invalid_speakers[:25]:

            report.append(
                f"  {candidate_id}: {speaker}"
            )

    report.append("")

    # -------------------------------------------------------------------------
    # DIALOGUE QUALITY
    # -------------------------------------------------------------------------

    report.append(
        "DIALOGUE QUALITY FLAGS"
    )
    report.append("-" * 72)

    report.append(
        f"Empty dialogue rows: "
        f"{len(empty_dialogue)}"
    )

    report.append(
        f"Long unresolved/review rows (>500 chars): "
        f"{len(narrative_flags)}"
    )

    report.append(
        f"Exact duplicate dialogue groups: "
        f"{len(duplicate_groups)}"
    )

    report.append(
        f"Rows involved in duplicate groups: "
        f"{duplicate_rows}"
    )

    report.append(
        f"Excess duplicate occurrences: "
        f"{duplicate_excess}"
    )

    report.append("")

    # -------------------------------------------------------------------------
    # CSV INTEGRITY
    # -------------------------------------------------------------------------

    report.append(
        "CSV INTEGRITY"
    )
    report.append("-" * 72)

    report.append(
        f"CSV SHA256: {csv_hash}"
    )

    report.append("")

    # -------------------------------------------------------------------------
    # LIMITATIONS
    # -------------------------------------------------------------------------

    report.append(
        "LIMITATIONS"
    )
    report.append("-" * 72)

    report.append(
        "This is the speaker-attribution/reconstruction layer, "
        "not the final corpus."
    )

    report.append(
        "Unknown candidates are intentionally preserved."
    )

    report.append(
        "No speaker is assigned solely from a generic pronoun."
    )

    report.append(
        "Repeated dialogue is preserved when provenance differs."
    )

    report.append(
        "Final corpus construction must occur only after independent audit."
    )

    report.append("")

    # -------------------------------------------------------------------------
    # OVERALL STATUS
    # -------------------------------------------------------------------------

    report.append(
        "OVERALL STATUS"
    )
    report.append("-" * 72)

    structural_pass = (
        len(output_rows) == len(candidates)
        and len(source_lookup_misses) == 0
        and provenance["mismatches"] == 0
        and len(full_provenance_mismatches) == 0
        and len(invalid_speakers) == 0
        and len(empty_dialogue) == 0
    )

    if structural_pass:

        report.append(
            "ATTRIBUTION LAYER STRUCTURAL STATUS: PASS"
        )

    else:

        report.append(
            "ATTRIBUTION LAYER STRUCTURAL STATUS: REVIEW REQUIRED"
        )

    VALIDATION_FILE.write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    candidate_id_counts = Counter(
        row.get("candidate_id", "")
        for row in candidates
    )
    duplicate_candidate_ids = sorted(
        candidate_id
        for candidate_id, count in candidate_id_counts.items()
        if count > 1
    )
    known_problem_attributions = sorted(
        row["candidate_id"]
        for row in output_rows
        if row["candidate_id"] in KNOWN_PROBLEMATIC_CANDIDATE_IDS
        and row["speaker_status"] == "ATTRIBUTED"
    )
    repair_ready = (
        structural_pass
        and not duplicate_candidate_ids
        and not known_problem_attributions
        and reproducibility_match
        and full_provenance_matches == len(candidates)
    )
    repair_report = [
        "TITLI RECONSTRUCTION REPAIR VALIDATION",
        "=" * 72,
        "",
        f"Input candidates: {len(candidates)}",
        f"Output rows: {len(output_rows)}",
        f"ATTRIBUTED count: {status_counter.get('ATTRIBUTED', 0)}",
        f"UNKNOWN count: {status_counter.get('UNKNOWN', 0)}",
        f"REVIEW count: {status_counter.get('REVIEW', 0)}",
        f"Unique speakers: {len(speaker_counter)}",
        f"Empty dialogue count: {len(empty_dialogue)}",
        f"Duplicate candidate IDs: {len(duplicate_candidate_ids)}",
        (
            "Duplicate candidate ID values: "
            + (", ".join(duplicate_candidate_ids) or "None")
        ),
        f"Known problematic candidates still attributed: {len(known_problem_attributions)}",
        (
            "Known problematic candidate IDs still attributed: "
            + (", ".join(known_problem_attributions) or "None")
        ),
        (
            f"Provenance result: {'PASS' if full_provenance_matches == len(candidates) else 'FAIL'} "
            f"({full_provenance_matches}/{len(candidates)})"
        ),
        f"Invalid speaker assignments: {len(invalid_speakers)}",
        (
            "Rows downgraded because of multi-speaker/narrative evidence: "
            f"{structural_downgraded}"
        ),
        (
            "Reproducibility result: "
            f"{'PASS' if reproducibility_match else 'PENDING SECOND IDENTICAL RUN'}"
        ),
        (
            "READY FOR FINAL-CORPUS CONSTRUCTION: "
            f"{'YES' if repair_ready else 'NO'}"
        ),
        f"Reconstruction CSV SHA256: {csv_hash}",
        "",
        "Readiness requires complete rows and provenance, no invalid speakers, ",
        "no empty dialogue, no duplicate candidate IDs, and an identical prior run.",
    ]
    REPAIR_VALIDATION_FILE.write_text(
        "\n".join(repair_report) + "\n",
        encoding="utf-8",
    )

    # =========================================================================
    # TERMINAL SUMMARY
    # =========================================================================

    print(
        f"Canonical source sections: {len(sections)}"
    )

    print(
        f"Canonical source paragraphs: {total_source_paragraphs}"
    )

    print(
        f"Input candidates: {len(candidates)}"
    )

    print(
        f"Output rows: {len(output_rows)}"
    )

    print(
        f"Attributed: "
        f"{status_counter.get('ATTRIBUTED', 0)}"
    )

    print(
        f"Unknown: "
        f"{status_counter.get('UNKNOWN', 0)}"
    )

    print(
        f"Review: "
        f"{status_counter.get('REVIEW', 0)}"
    )

    print(
        f"Unique attributed speakers: "
        f"{len(speaker_counter)}"
    )

    print(
        f"Source lookup misses: "
        f"{len(source_lookup_misses)}"
    )

    print(
        f"Provenance: "
        f"{provenance['matches']}/"
        f"{provenance['sample_size']} "
        f"sampled rows matched; "
        f"full-field checks {full_provenance_matches}/{len(candidates)}"
    )

    print(
        f"Invalid speaker assignments rejected: "
        f"{len(invalid_speakers)}"
    )

    print(
        f"Empty dialogue rows: "
        f"{len(empty_dialogue)}"
    )

    print(
        f"Duplicate dialogue groups: "
        f"{len(duplicate_groups)}"
    )

    print(
        f"CSV SHA256: {csv_hash}"
    )

    if structural_pass:

        print(
            "ATTRIBUTION STRUCTURAL VALIDATION: PASS"
        )

    else:

        print(
            "ATTRIBUTION STRUCTURAL VALIDATION: "
            "REVIEW REQUIRED"
        )

    print(
        f"Validation report: {VALIDATION_FILE}"
    )

    print(
        f"Repair validation report: {REPAIR_VALIDATION_FILE}"
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()