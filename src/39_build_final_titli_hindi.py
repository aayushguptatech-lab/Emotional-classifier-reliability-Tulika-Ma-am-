from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)
SOURCE_PATH = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"
FINAL_PATH = ROOT / "data" / "final" / "hindi" / "titli_dialogue_final.csv"
VALIDATION_PATH = ROOT / "data" / "final" / "hindi" / "titli_final_validation.txt"

EXPECTED_RECONSTRUCTION_SHA256 = (
    "0557d39c9a2a19f4633eed1eb71253b8de5233f7c05b0b764c7b051c4f586bc3"
)
EXPECTED_SOURCE_SHA256 = (
    "21f45bccbb755181ba5832d4f0c20291d9db23e929b0668190879362f15132ec"
)
EXPECTED_SOURCE_PARAGRAPHS = 1406

REQUIRED_FIELDS = {
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
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return reader.fieldnames, list(reader)


def normalize_for_comparison(text: str) -> str:
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()


def load_source_paragraphs() -> dict[tuple[str, int], tuple[str, str]]:
    header_re = re.compile(
        r"^===== TITLI SECTION "
        r"(?P<section>\d+\.\d+)"
        r" \| SOURCE "
        r"(?P<source_file>[^=]+?)"
        r" =====$"
    )
    lookup = {}
    current_section = ""
    current_source_file = ""
    paragraph_index = 0

    for raw_line in SOURCE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = header_re.fullmatch(line)
        if match:
            current_section = match.group("section")
            current_source_file = match.group("source_file").strip()
            continue

        if not current_section:
            raise ValueError("Source paragraph encountered before a section header")

        paragraph_index += 1
        lookup[(current_section, paragraph_index)] = (current_source_file, line)

    if paragraph_index != EXPECTED_SOURCE_PARAGRAPHS:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_PARAGRAPHS} source paragraphs, "
            f"found {paragraph_index}"
        )
    return lookup


def provenance_errors(
    rows: list[dict[str, str]],
    source_lookup: dict[tuple[str, int], tuple[str, str]],
) -> list[str]:
    errors = []
    for row in rows:
        candidate_id = row.get("candidate_id", "")
        try:
            paragraph_index = int(row.get("source_paragraph_index", ""))
        except (TypeError, ValueError):
            errors.append(f"{candidate_id}: invalid source paragraph index")
            continue

        source_record = source_lookup.get((row.get("section", ""), paragraph_index))
        if source_record is None:
            errors.append(f"{candidate_id}: canonical source paragraph not found")
            continue

        source_file, source_paragraph = source_record
        if row.get("source_file", "") != source_file:
            errors.append(f"{candidate_id}: source file mismatch")
        if row.get("source_paragraph", "") != source_paragraph:
            errors.append(f"{candidate_id}: source paragraph mismatch")

        dialogue = normalize_for_comparison(row.get("dialogue_text", ""))
        canonical = normalize_for_comparison(source_paragraph)
        if not dialogue or dialogue not in canonical:
            errors.append(f"{candidate_id}: dialogue missing from source paragraph")

    return errors


def duplicate_values(values: list[str]) -> tuple[int, int]:
    counts = Counter(values)
    groups = sum(count > 1 for count in counts.values())
    rows = sum(count for count in counts.values() if count > 1)
    return groups, rows


def main() -> None:
    if not RECONSTRUCTION_PATH.exists():
        raise FileNotFoundError(f"Reconstruction CSV not found: {RECONSTRUCTION_PATH}")
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Canonical clean source not found: {SOURCE_PATH}")

    reconstruction_hash = sha256_file(RECONSTRUCTION_PATH)
    source_hash = sha256_file(SOURCE_PATH)
    if reconstruction_hash != EXPECTED_RECONSTRUCTION_SHA256:
        raise ValueError(
            "Reconstruction SHA256 does not match the validated input: "
            f"{reconstruction_hash}"
        )
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"Clean source SHA256 does not match the protected input: {source_hash}"
        )

    fieldnames, reconstruction_rows = read_csv(RECONSTRUCTION_PATH)
    missing_fields = REQUIRED_FIELDS.difference(fieldnames)
    if missing_fields:
        raise ValueError(f"Reconstruction is missing fields: {sorted(missing_fields)}")

    status_counts = Counter(row.get("speaker_status", "") for row in reconstruction_rows)
    unexpected_statuses = sorted(
        status for status in status_counts if status not in {"ATTRIBUTED", "UNKNOWN", "REVIEW"}
    )
    if unexpected_statuses:
        raise ValueError(f"Unexpected speaker statuses: {unexpected_statuses}")

    final_rows = [
        row for row in reconstruction_rows
        if row.get("speaker_status") == "ATTRIBUTED"
    ]
    source_lookup = load_source_paragraphs()
    provenance_failures = provenance_errors(final_rows, source_lookup)

    empty_dialogue_count = sum(
        not row.get("dialogue_text", "").strip()
        for row in final_rows
    )
    invalid_speaker_count = sum(
        not row.get("speaker", "").strip() or row.get("speaker", "").strip() == "Unknown"
        for row in final_rows
    )
    candidate_duplicate_groups, candidate_duplicate_rows = duplicate_values(
        [row.get("candidate_id", "") for row in final_rows]
    )
    dialogue_duplicate_groups, dialogue_duplicate_rows = duplicate_values(
        [row.get("dialogue_text", "") for row in final_rows]
    )

    FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    previous_output = FINAL_PATH.read_bytes() if FINAL_PATH.exists() else None
    with FINAL_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(final_rows)

    output_fields, written_rows = read_csv(FINAL_PATH)
    output_hash = sha256_file(FINAL_PATH)
    output_size = FINAL_PATH.stat().st_size
    reproducible = previous_output is not None and previous_output == FINAL_PATH.read_bytes()
    non_attributed_count = sum(
        row.get("speaker_status", "") != "ATTRIBUTED"
        for row in written_rows
    )
    exact_projection = output_fields == fieldnames and written_rows == final_rows

    speaker_counts = Counter(row.get("speaker", "").strip() for row in written_rows)
    final_ids = [row.get("candidate_id", "") for row in written_rows]
    final_candidate_duplicate_groups, final_candidate_duplicate_rows = duplicate_values(final_ids)
    final_dialogue_duplicate_groups, final_dialogue_duplicate_rows = duplicate_values(
        [row.get("dialogue_text", "") for row in written_rows]
    )
    provenance_pass = not provenance_failures
    structural_pass = (
        exact_projection
        and non_attributed_count == 0
        and empty_dialogue_count == 0
        and invalid_speaker_count == 0
        and final_candidate_duplicate_groups == 0
        and provenance_pass
    )
    validation_pass = structural_pass and reproducible
    classification = (
        "FINAL CORPUS VALIDATED; REPRODUCIBILITY VERIFIED"
        if validation_pass
        else "FINAL CORPUS CONSTRUCTED; VALIDATION OR REPRODUCIBILITY PENDING"
    )

    report = [
        "TITLI FINAL HINDI DIALOGUE CORPUS VALIDATION",
        "=" * 76,
        "",
        f"Final classification: {classification}",
        f"Input reconstruction: {RECONSTRUCTION_PATH.relative_to(ROOT)}",
        f"Input reconstruction SHA256: {reconstruction_hash}",
        f"Canonical clean source SHA256: {source_hash}",
        "",
        f"Input reconstruction row count: {len(reconstruction_rows)}",
        f"Final corpus row count: {len(written_rows)}",
        f"Excluded UNKNOWN count: {status_counts.get('UNKNOWN', 0)}",
        f"Excluded REVIEW count: {status_counts.get('REVIEW', 0)}",
        f"Unique speaker count: {len(speaker_counts)}",
        f"Empty dialogue count: {empty_dialogue_count}",
        f"Duplicate candidate ID count: {final_candidate_duplicate_groups}",
        f"Duplicate candidate ID rows involved: {final_candidate_duplicate_rows}",
        f"Duplicate dialogue-text groups: {final_dialogue_duplicate_groups}",
        f"Rows involved in duplicate dialogue-text groups: {final_dialogue_duplicate_rows}",
        f"Non-ATTRIBUTED rows accidentally present: {non_attributed_count}",
        f"Invalid/empty speaker count: {invalid_speaker_count}",
        f"SHA256 of final CSV: {output_hash}",
        f"Final CSV byte size: {output_size}",
        f"Reproducibility status: {'PASS' if reproducible else 'PENDING SECOND IDENTICAL RUN'}",
        f"Source/reconstruction provenance status: {'PASS' if provenance_pass else 'FAIL'}",
        f"Exact ATTRIBUTED-only projection status: {'PASS' if exact_projection else 'FAIL'}",
        "",
        "Speaker frequency table:",
    ]
    for speaker, count in sorted(speaker_counts.items(), key=lambda item: (-item[1], item[0])):
        report.append(f"  {speaker} = {count}")

    if provenance_failures:
        report.extend(["", "Provenance failures:"])
        report.extend(f"  {failure}" for failure in provenance_failures[:50])

    report.extend(
        [
            "",
            "Repeated dialogue was retained; no dialogue-text deduplication was performed.",
            "All reconstruction columns and source row ordering were preserved.",
            "",
        ]
    )
    VALIDATION_PATH.write_text("\n".join(report), encoding="utf-8")

    print(f"Input reconstruction rows: {len(reconstruction_rows)}")
    print(f"Final corpus rows: {len(written_rows)}")
    print(f"Excluded UNKNOWN: {status_counts.get('UNKNOWN', 0)}")
    print(f"Excluded REVIEW: {status_counts.get('REVIEW', 0)}")
    print(f"Unique speakers: {len(speaker_counts)}")
    for speaker, count in sorted(speaker_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{speaker}={count}")
    print(f"Final CSV byte size: {output_size}")
    print(f"Final CSV SHA256: {output_hash}")
    print(f"Reproducibility: {'PASS' if reproducible else 'PENDING SECOND IDENTICAL RUN'}")
    print(f"Source/reconstruction provenance: {'PASS' if provenance_pass else 'FAIL'}")
    print(f"Validation result: {'PASS' if validation_pass else 'PENDING'}")
    print(f"Final CSV: {FINAL_PATH.relative_to(ROOT)}")
    print(f"Validation report: {VALIDATION_PATH.relative_to(ROOT)}")

    if not structural_pass:
        raise RuntimeError("Final corpus structural validation failed; see validation report")


if __name__ == "__main__":
    main()