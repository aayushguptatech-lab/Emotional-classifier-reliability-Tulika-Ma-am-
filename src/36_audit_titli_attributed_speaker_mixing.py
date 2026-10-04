import csv
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_dialogue_turns_attributed.csv"
)

OUTPUT = (
    ROOT
    / "data"
    / "extracted"
    / "hindi"
    / "titli"
    / "titli_attributed_speaker_mixing_audit.txt"
)

# Verified/observed Titli character names used by the current attribution layer.
SPEAKERS = [
    "शैला",
    "इन्द्रदेव",
    "इंद्रदेव",
    "मधुबन",
    "मधुवा",
    "तितली",
    "रामनाथ",
    "अनवरी",
    "राजकुमारी",
    "माधुरी",
    "महंगू",
    "बंजो",
    "रामजस",
    "तहसीलदार",
    "सुखदेव",
    "कृष्णमोहन",
]


def main():
    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    attributed = [
        r for r in rows
        if r.get("speaker_status") == "ATTRIBUTED"
    ]

    flagged = []

    for row in attributed:
        dialogue = row.get("dialogue_text", "")

        mentions = []
        for speaker in SPEAKERS:
            if speaker in dialogue:
                mentions.append(speaker)

        # Deduplicate exact repeated mentions while preserving order.
        seen = set()
        mentions_unique = []
        for name in mentions:
            if name not in seen:
                seen.add(name)
                mentions_unique.append(name)

        assigned = row.get("speaker", "")

        # Flag if another known character appears in the dialogue,
        # or if more than one known character name occurs.
        other_speakers = [
            name for name in mentions_unique
            if name != assigned
        ]

        if len(mentions_unique) >= 2 or other_speakers:
            flagged.append(
                (
                    row,
                    mentions_unique,
                    other_speakers,
                )
            )

    lines = []

    lines.append("=" * 100)
    lines.append("TITLI ATTRIBUTED SPEAKER-MIXING AUDIT")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Total reconstructed rows: {len(rows)}")
    lines.append(f"Attributed rows: {len(attributed)}")
    lines.append(f"Potentially mixed/name-containing rows: {len(flagged)}")
    lines.append("")
    lines.append(
        "IMPORTANT: presence of a character name does NOT automatically mean "
        "speaker contamination. This is a screening audit only."
    )
    lines.append("")

    for i, (row, mentions, others) in enumerate(flagged, start=1):
        lines.append("-" * 100)
        lines.append(f"FLAGGED ROW #{i}")
        lines.append(f"Candidate ID: {row.get('candidate_id', '')}")
        lines.append(f"Section: {row.get('section', '')}")
        lines.append(f"Source file: {row.get('source_file', '')}")
        lines.append(f"Assigned speaker: {row.get('speaker', '')}")
        lines.append(f"Detected character names: {', '.join(mentions)}")
        lines.append(
            f"Other character names besides assigned speaker: "
            f"{', '.join(others) if others else 'NONE'}"
        )
        lines.append(f"Dialogue length: {len(row.get('dialogue_text', ''))}")
        lines.append("")
        lines.append("DIALOGUE:")
        lines.append(row.get("dialogue_text", ""))
        lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print("Titli speaker-mixing audit complete.")
    print(f"Total reconstructed rows: {len(rows)}")
    print(f"Attributed rows: {len(attributed)}")
    print(f"Potentially mixed/name-containing rows: {len(flagged)}")
    print(f"Audit report: {OUTPUT}")


if __name__ == "__main__":
    main()