import pandas as pd
from pathlib import Path


INPUT_FILE = Path(
    "data/extracted/english/"
    "the_man_who_was_thursday_dialogue_turns_v1.csv"
)


print("Inspecting MWT turn reconstruction structure...")
print()

df = pd.read_csv(INPUT_FILE)

print(f"Turns loaded: {len(df):,}")
print()


# ---------------------------------------------------------
# BASIC STRUCTURE
# ---------------------------------------------------------

def split_candidate_ids(value):
    if pd.isna(value):
        return []
    
    return [
        x.strip()
        for x in str(value).split("|")
        if x.strip()
    ]


df["candidate_count"] = df[
    "source_candidate_ids"
].apply(
    lambda x: len(split_candidate_ids(x))
)


print("CANDIDATE GROUPING SUMMARY")
print("--------------------------")

print(
    f"Turns containing 1 candidate: "
    f"{(df['candidate_count'] == 1).sum():,}"
)

print(
    f"Turns containing 2 candidates: "
    f"{(df['candidate_count'] == 2).sum():,}"
)

print(
    f"Turns containing 3 candidates: "
    f"{(df['candidate_count'] == 3).sum():,}"
)

print(
    f"Turns containing 4+ candidates: "
    f"{(df['candidate_count'] >= 4).sum():,}"
)

print()


# ---------------------------------------------------------
# FIRST 50 MULTI-CANDIDATE TURNS
# ---------------------------------------------------------

multi = df[df["candidate_count"] > 1]

print("FIRST 40 MULTI-CANDIDATE TURNS")
print("------------------------------")

for _, row in multi.head(40).iterrows():

    print(
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['candidate_count']} candidates | "
        f"{row['source_candidate_ids']}"
    )

    print(
        f"  {str(row['quoted_text'])[:350]}"
        .replace("\n", " ")
    )

    print()


# ---------------------------------------------------------
# FIRST 40 SINGLE-CANDIDATE TURNS
# ---------------------------------------------------------

print("FIRST 40 SINGLE-CANDIDATE TURNS")
print("--------------------------------")

single = df[df["candidate_count"] == 1]

for _, row in single.head(40).iterrows():

    print(
        f"{row['turn_id']} | "
        f"{row['speaker']} | "
        f"{row['source_candidate_ids']}"
    )

    print(
        f"  {str(row['quoted_text'])[:250]}"
        .replace("\n", " ")
    )

    print()


print("Inspection complete.")