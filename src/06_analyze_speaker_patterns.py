from pathlib import Path
import re


# ---------------------------------------------------------
# 1. File location
# ---------------------------------------------------------

CLEAN_FILE = Path(
    "data/cleaned/english/the_valley_of_fear_clean.txt"
)


# ---------------------------------------------------------
# 2. Read the cleaned novel
# ---------------------------------------------------------

text = CLEAN_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------
# 3. Normalize only physical line wrapping
#
# IMPORTANT:
# This does NOT modify the saved novel.
# It is only used for pattern inspection.
# ---------------------------------------------------------

inspection_text = re.sub(
    r"\s*\n\s*",
    " ",
    text
)

inspection_text = re.sub(
    r"\s+",
    " ",
    inspection_text
)


# ---------------------------------------------------------
# 4. Extract quotation spans
# ---------------------------------------------------------

quotation_pattern = re.compile(
    r"“(.*?)”",
    flags=re.DOTALL
)

quotations = list(
    quotation_pattern.finditer(text)
)


# ---------------------------------------------------------
# 5. Speaker-attribution verbs
# ---------------------------------------------------------

speaker_verbs = (
    "said",
    "asked",
    "replied",
    "answered",
    "remarked",
    "continued",
    "cried",
    "exclaimed",
    "shouted",
    "whispered",
    "observed",
    "returned",
    "added",
    "murmured",
    "declared",
    "demanded",
    "suggested",
    "explained",
    "repeated",
    "called",
    "protested",
    "rejoined",
    "urged",
    "begged",
    "pleaded",
    "retorted",
    "interrupted",
)


# ---------------------------------------------------------
# 6. Helper function
# ---------------------------------------------------------

def contains_speaker_verb(text_fragment):
    """
    Check whether a text fragment contains
    one of our known speaker-attribution verbs.
    """

    lower_fragment = text_fragment.lower()

    for verb in speaker_verbs:

        if re.search(
            rf"\b{re.escape(verb)}\b",
            lower_fragment
        ):
            return True

    return False


# ---------------------------------------------------------
# 7. Counters
# ---------------------------------------------------------

after_quote_attribution = 0
before_quote_attribution = 0
inside_quote_attribution = 0
no_obvious_attribution = 0

examples_after = []
examples_before = []
examples_inside = []
examples_unknown = []


# ---------------------------------------------------------
# 8. Inspect every quotation
# ---------------------------------------------------------

for match in quotations:

    quote_start = match.start()
    quote_end = match.end()

    quote_text = match.group(1).strip()

    # -----------------------------------------------------
    # Context before quotation
    # -----------------------------------------------------

    before_start = max(
        0,
        quote_start - 150
    )

    before_context = text[
        before_start:quote_start
    ]

    # -----------------------------------------------------
    # Context after quotation
    # -----------------------------------------------------

    after_end = min(
        len(text),
        quote_end + 150
    )

    after_context = text[
        quote_end:after_end
    ]

    # -----------------------------------------------------
    # Check for speaker attribution after quotation
    # -----------------------------------------------------

    after_has_verb = contains_speaker_verb(
        after_context
    )

    # -----------------------------------------------------
    # Check for speaker attribution before quotation
    # -----------------------------------------------------

    before_has_verb = contains_speaker_verb(
        before_context
    )

    # -----------------------------------------------------
    # Check for attribution inside quotation
    #
    # This is useful for cases such as:
    #
    # “Really, Holmes,” said I severely, “...”
    #
    # The regex here is intentionally conservative.
    # -----------------------------------------------------

    inside_has_verb = contains_speaker_verb(
        quote_text
    )

    # -----------------------------------------------------
    # Classify
    # -----------------------------------------------------

    if after_has_verb:

        after_quote_attribution += 1

        if len(examples_after) < 15:
            examples_after.append(
                (
                    quote_text,
                    after_context.strip()
                )
            )

    elif before_has_verb:

        before_quote_attribution += 1

        if len(examples_before) < 15:
            examples_before.append(
                (
                    before_context.strip(),
                    quote_text
                )
            )

    elif inside_has_verb:

        inside_quote_attribution += 1

        if len(examples_inside) < 15:
            examples_inside.append(
                quote_text
            )

    else:

        no_obvious_attribution += 1

        if len(examples_unknown) < 15:
            examples_unknown.append(
                quote_text
            )


# ---------------------------------------------------------
# 9. Print summary
# ---------------------------------------------------------

print("=" * 70)
print("SPEAKER ATTRIBUTION PATTERN ANALYSIS")
print("=" * 70)

print()
print(f"Total quotation spans: {len(quotations):,}")

print()
print("Classification counts")
print("-" * 70)

print(
    f"Attribution after quotation:  {after_quote_attribution:,}"
)

print(
    f"Attribution before quotation: {before_quote_attribution:,}"
)

print(
    f"Possible attribution inside quotation: "
    f"{inside_quote_attribution:,}"
)

print(
    f"No obvious attribution nearby: {no_obvious_attribution:,}"
)


# ---------------------------------------------------------
# 10. Examples: attribution after quotation
# ---------------------------------------------------------

print()
print("=" * 70)
print("EXAMPLES — ATTRIBUTION AFTER QUOTATION")
print("=" * 70)

for i, (quote, after) in enumerate(
    examples_after,
    start=1
):

    print()
    print(f"[Example {i}]")
    print("-" * 70)
    print(f"QUOTATION: {quote}")
    print(f"AFTER:     {after}")


# ---------------------------------------------------------
# 11. Examples: attribution before quotation
# ---------------------------------------------------------

print()
print("=" * 70)
print("EXAMPLES — ATTRIBUTION BEFORE QUOTATION")
print("=" * 70)

for i, (before, quote) in enumerate(
    examples_before,
    start=1
):

    print()
    print(f"[Example {i}]")
    print("-" * 70)
    print(f"BEFORE:    {before}")
    print(f"QUOTATION: {quote}")


# ---------------------------------------------------------
# 12. Examples: possible attribution inside quotation
# ---------------------------------------------------------

print()
print("=" * 70)
print("EXAMPLES — POSSIBLE ATTRIBUTION INSIDE QUOTATION")
print("=" * 70)

for i, quote in enumerate(
    examples_inside,
    start=1
):

    print()
    print(f"[Example {i}]")
    print("-" * 70)
    print(quote)


# ---------------------------------------------------------
# 13. Examples: no obvious attribution
# ---------------------------------------------------------

print()
print("=" * 70)
print("EXAMPLES — NO OBVIOUS ATTRIBUTION")
print("=" * 70)

for i, quote in enumerate(
    examples_unknown,
    start=1
):

    print()
    print(f"[Example {i}]")
    print("-" * 70)
    print(quote)


# ---------------------------------------------------------
# 14. Final message
# ---------------------------------------------------------

print()
print("=" * 70)
print("SPEAKER PATTERN ANALYSIS COMPLETE")
print("=" * 70)