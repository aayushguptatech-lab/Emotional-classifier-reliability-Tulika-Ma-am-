from pathlib import Path
import pandas as pd


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_speaker_candidates_v4.csv"
)


OUTPUT_FILE = Path(
    "data/extracted/english/"
    "the_old_wives_tale_unusual_speaker_audit_v1.csv"
)


print("Auditing unusual speaker identities")
print("====================================")
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
# IDENTITIES THAT NEED EXPLICIT REVIEW
# --------------------------------------------------

review_names = {
    "Between",
    "Carlier",
    "Lewis Mardon",
    "Cyril Povey",
    "Mr. Shawcross",
    "Jacqueline",
    "Maud",
    "Dr. Stirling",
    "Mr. Till",
    "Dick Povey",
    "Gerald Scales",
    "James Boon",
    "Daniel Povey",
}


review = df[
    df["speaker_before"].isin(review_names)
].copy()


print("UNUSUAL SPEAKER IDENTITIES")
print("--------------------------")
print(
    f"Rows requiring review: {len(review):,}"
)
print()


# --------------------------------------------------
# PRINT EVERY CASE
# --------------------------------------------------

for speaker in sorted(
    review["speaker_before"].unique()
):

    subset = review[
        review["speaker_before"]
        == speaker
    ]

    print("=" * 70)
    print(
        f"SPEAKER: {speaker}"
    )
    print(
        f"COUNT: {len(subset)}"
    )
    print("=" * 70)

    for _, row in subset.iterrows():

        quoted = " ".join(
            str(
                row["quoted_text"]
            ).split()
        )

        if len(quoted) > 250:
            quoted = (
                quoted[:250]
                + "..."
            )

        print(
            f'{row["candidate_id"]}: '
            f'"{quoted}"'
        )

        print(
            "  Attribution source: "
            f'{row["attribution_source"]}'
        )

        print(
            "  Raw after attribution: "
            f'{row["speaker_after_raw"]}'
        )

        print(
            "  Raw before attribution: "
            f'{row["speaker_before_raw"]}'
        )

        print(
            "  Context before: "
            f'{row["context_before"]}'
        )

        print(
            "  Context after: "
            f'{row["context_after"]}'
        )

        print()


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

review.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print("OUTPUT")
print("------")
print(OUTPUT_FILE)
print()

print(
    "UNUSUAL SPEAKER AUDIT COMPLETE."
)