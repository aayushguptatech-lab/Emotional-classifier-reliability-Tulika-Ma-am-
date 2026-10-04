import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_candidates.csv"
)

RECONSTRUCTED_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_problematic_source_context.txt"
)

TARGET_IDS = {
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


def main():
    with CANDIDATE_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        candidates = list(csv.DictReader(f))

    with RECONSTRUCTED_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        reconstructed = list(csv.DictReader(f))

    candidate_map = {
        row["candidate_id"]: row
        for row in candidates
    }

    reconstructed_map = {
        row["candidate_id"]: row
        for row in reconstructed
    }

    lines = []

    lines.append("=" * 120)
    lines.append("TITLI PROBLEMATIC SOURCE CONTEXT INSPECTION")
    lines.append("=" * 120)
    lines.append("")
    lines.append(
        "Source paragraph and offsets are taken directly from the "
        "validated candidate layer."
    )
    lines.append("")

    found = 0

    for number, candidate_id in enumerate(
        sorted(TARGET_IDS),
        start=1,
    ):
        candidate = candidate_map.get(candidate_id)
        recon = reconstructed_map.get(candidate_id)

        lines.append("=" * 120)
        lines.append(f"CASE #{number}")
        lines.append("=" * 120)

        if candidate is None:
            lines.append(f"Candidate ID: {candidate_id}")
            lines.append("ERROR: Candidate not found.")
            lines.append("")
            continue

        found += 1

        lines.append(f"Candidate ID       : {candidate_id}")
        lines.append(f"Section            : {candidate.get('section', '')}")
        lines.append(f"Source file        : {candidate.get('source_file', '')}")
        lines.append(
            f"Source paragraph # : "
            f"{candidate.get('source_paragraph_index', '')}"
        )
        lines.append(
            f"Detection method   : "
            f"{candidate.get('detection_method', '')}"
        )
        lines.append(
            f"Candidate confidence: "
            f"{candidate.get('confidence', '')}"
        )
        lines.append("")

        lines.append("CANONICAL SOURCE PARAGRAPH:")
        lines.append(candidate.get("source_paragraph", ""))
        lines.append("")

        lines.append("CANDIDATE EXTRACTED DIALOGUE:")
        lines.append(candidate.get("dialogue_text", ""))
        lines.append("")

        lines.append("CANDIDATE ATTRIBUTION:")
        lines.append(
            candidate.get("attribution_name_candidate", "")
        )
        lines.append("")

        lines.append("SOURCE OFFSETS:")
        lines.append(
            f"start={candidate.get('source_start', '')}, "
            f"end={candidate.get('source_end', '')}"
        )
        lines.append("")

        lines.append("RECONSTRUCTED SPEAKER:")
        if recon:
            lines.append(recon.get("speaker", ""))
            lines.append(
                f"status={recon.get('speaker_status', '')}"
            )
        else:
            lines.append("[NO RECONSTRUCTED ROW]")
        lines.append("")

        lines.append("RECONSTRUCTED DIALOGUE:")
        if recon:
            lines.append(recon.get("dialogue_text", ""))
        else:
            lines.append("[NO RECONSTRUCTED DIALOGUE]")
        lines.append("")

    lines.append("=" * 120)
    lines.append("SUMMARY")
    lines.append("=" * 120)
    lines.append(f"Target candidates: {len(TARGET_IDS)}")
    lines.append(f"Candidates found: {found}")
    lines.append("")

    OUTPUT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("Titli provenance-based source inspection complete.")
    print(f"Target candidates: {len(TARGET_IDS)}")
    print(f"Candidates found: {found}")
    print(f"Inspection report: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

