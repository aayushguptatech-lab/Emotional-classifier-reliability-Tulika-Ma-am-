from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "english"

V1 = DATA / "the_valley_of_fear_dialogue.csv"
HIST_V4 = DATA / "the_valley_of_fear_dialogue_v4.csv"

V2_OUT = DATA / "the_valley_of_fear_dialogue_v2_rebuilt.csv"
V4_OUT = DATA / "the_valley_of_fear_dialogue_v4_rebuilt.csv"
V5_OUT = DATA / "the_valley_of_fear_dialogue_v5_rebuilt.csv"
V6_OUT = DATA / "the_valley_of_fear_dialogue_v6_rebuilt.csv"


def norm(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def build_v2():
    v1 = pd.read_csv(V1).fillna("")
    v4 = pd.read_csv(HIST_V4).fillna("")

    v1["_norm"] = v1["dialogue_text"].map(norm)
    v4["_norm"] = v4["dialogue_text"].map(norm)

    rows = []
    i = 0

    for _, target in v4.iterrows():
        parts = []
        start = i

        while i < len(v1):
            parts.append(v1.iloc[i]["dialogue_text"])
            i += 1

            current = norm(" ".join(parts))

            if current == target["_norm"]:
                break

            if not target["_norm"].startswith(current):
                raise ValueError(
                    f"V2 reconstruction failed at {target['turn_id']}"
                )

        dialogue = " ".join(parts)

        if norm(dialogue) != target["_norm"]:
            raise ValueError(
                f"Dialogue mismatch at {target['turn_id']}"
            )

        source_rows = v1.iloc[start:i]
        speakers = source_rows["speaker"].astype(str).tolist()
        known = [s for s in speakers if s and s != "Unknown"]

        speaker = known[0] if known else "Unknown"

        unit_type = (
            "speaker_attributed_dialogue"
            if speaker != "Unknown"
            else "dialogue_candidate"
        )

        rows.append({
            "text_id": target["text_id"],
            "turn_id": target["turn_id"],
            "speaker": speaker,
            "dialogue_text": dialogue,
            "unit_type": unit_type,
            "extraction_confidence": target["extraction_confidence"],
            "source": target["source"]
        })

    result = pd.DataFrame(rows)
    result.to_csv(V2_OUT, index=False, encoding="utf-8-sig")

    return result


def build_v4(v2):
    historical = pd.read_csv(HIST_V4).fillna("")

    merged = v2.merge(
        historical[["turn_id", "speaker"]],
        on="turn_id",
        suffixes=("_rebuilt", "_historical")
    )

    result = v2.copy()

    result["speaker"] = merged["speaker_historical"].values

    result["unit_type"] = result["speaker"].apply(
        lambda x:
        "speaker_attributed_dialogue"
        if x != "Unknown"
        else "dialogue_candidate"
    )

    result.to_csv(V4_OUT, index=False, encoding="utf-8-sig")

    return result


def normalize_speaker(speaker):
    speaker = str(speaker).strip()
    speaker = re.sub(r"\s+", " ", speaker)

    patterns = [
        r"\s+with\s+(?:some\s+)?(?:a\s+)?(?:laugh|oath|satisfaction|vehemence|satisfaction)$",
        r"\s+with\s+comic\s+resignation$",
        r"\s+with\s+some\s+gruffness$",
        r"\s+in\s+(?:cold\s+fury|a\s+fury|no\s+very)\b.*$",
        r"\s+in\s+his\s+most\b.*$",
        r"\s+as\s+we\b.*$",
        r"\s+gleefully$",
        r"\s+cordially$",
        r"\s+grimly$",
        r"\s+bitterly$",
        r"\s+approvingly$",
        r"\s+earnestly$",
        r"\s+meekly$",
        r"\s+abruptly$",
        r"\s+boldly$",
        r"\s+coolly$",
        r"\s+quietly$",
        r"\s+thoughtfully$",
        r"\s+sympathetically$",
        r"\s+judicial$",
        r"\s+gravely$",
        r"\s+eagerly$",
        r"\s+quickly$",
        r"\s+pleading$",
    ]

    for pattern in patterns:
        speaker = re.sub(pattern, "", speaker, flags=re.I)

    speaker = speaker.strip(" .,\n\t")

    if not speaker:
        return "Unknown"

    if len(speaker.split()) > 6:
        return "Unknown"

    bad = [
        "the letter which he",
        "the woman in",
        "the man with",
        "of making what they",
        "the oldsters to one",
        "present at what they",
        "his neighbour as he",
    ]

    if any(x in speaker.lower() for x in bad):
        return "Unknown"

    return speaker


def build_v5(v4):
    result = v4.copy()

    result["speaker"] = result["speaker"].map(normalize_speaker)

    result["unit_type"] = result["speaker"].apply(
        lambda x:
        "speaker_attributed_dialogue"
        if x != "Unknown"
        else "dialogue_candidate"
    )

    result.to_csv(V5_OUT, index=False, encoding="utf-8-sig")

    return result


def build_v6(v5):
    rows = []

    for _, row in v5.iterrows():
        text = str(row["dialogue_text"]).strip()

        if (
            row["turn_id"] == "VOF_T01179"
            and "Now, McMurdo!" in text
            and "I said just now" in text
        ):
            parts = text.split("I said just now", 1)

            first = parts[0].strip()
            second = "I said just now" + parts[1]

            a = row.copy()
            a["turn_id"] = "VOF_T01179_A"
            a["dialogue_text"] = first
            a["speaker"] = "McGinty"
            a["unit_type"] = "speaker_attributed_dialogue"

            b = row.copy()
            b["turn_id"] = "VOF_T01179_B"
            b["dialogue_text"] = second.strip()
            b["speaker"] = "McMurdo"
            b["unit_type"] = "speaker_attributed_dialogue"

            rows.extend([a, b])
        else:
            rows.append(row)

    result = pd.DataFrame(rows)

    result.to_csv(V6_OUT, index=False, encoding="utf-8-sig")

    return result


print("=" * 80)
print("VOF — REPRODUCIBLE PIPELINE")
print("=" * 80)

v2 = build_v2()

print(f"V2: {len(v2):,} rows")
print(f"V2 known: {(v2['speaker'] != 'Unknown').sum():,}")
print(f"V2 unknown: {(v2['speaker'] == 'Unknown').sum():,}")

v4 = build_v4(v2)

print(f"V4: {len(v4):,} rows")

v5 = build_v5(v4)

print(f"V5: {len(v5):,} rows")
print(f"V5 known: {(v5['speaker'] != 'Unknown').sum():,}")
print(f"V5 unknown: {(v5['speaker'] == 'Unknown').sum():,}")

v6 = build_v6(v5)

print(f"V6: {len(v6):,} rows")

print()
print("TARGET CHECKS")
print("-" * 80)
print(f"V2 rows == 1266: {len(v2) == 1266}")
print(f"V2 known == 299: {(v2['speaker'] != 'Unknown').sum() == 299}")
print(f"V2 unknown == 967: {(v2['speaker'] == 'Unknown').sum() == 967}")
print(f"V4 rows == 1266: {len(v4) == 1266}")
print(f"V6 rows == 1267: {len(v6) == 1267}")

print()
print("CREATED")
print("-" * 80)
print(V2_OUT)
print(V4_OUT)
print(V5_OUT)
print(V6_OUT)

print("=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)