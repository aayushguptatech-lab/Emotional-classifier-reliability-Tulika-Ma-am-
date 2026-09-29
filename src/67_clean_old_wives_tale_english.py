from pathlib import Path


RAW_FILE = Path(
    "data/raw/english/the_old_wives_tale_raw.txt"
)

CLEAN_FILE = Path(
    "data/cleaned/english/the_old_wives_tale_clean.txt"
)


print("Cleaning The Old Wives' Tale")
print("============================")
print()


# =========================================================
# LOAD RAW SOURCE
# =========================================================

if not RAW_FILE.exists():

    raise FileNotFoundError(
        f"Raw file not found: {RAW_FILE}"
    )


text = RAW_FILE.read_text(
    encoding="utf-8"
)


print(
    f"Raw characters: {len(text):,}"
)


# =========================================================
# FIND NOVEL START
# =========================================================

start_markers = [
    "*** START OF THE PROJECT GUTENBERG EBOOK",
    "THE OLD WIVES' TALE",
]


start_position = None


for marker in start_markers:

    position = text.upper().find(
        marker.upper()
    )

    if position != -1:

        # For Gutenberg's START marker, begin after
        # the marker's line. For the title fallback,
        # use the title occurrence directly.

        if marker.startswith("*** START"):

            newline = text.find(
                "\n",
                position
            )

            if newline != -1:

                start_position = newline + 1

            else:

                start_position = position

        else:

            start_position = position

        print(
            f"Start marker found: {marker}"
        )

        print(
            f"Start position: {position:,}"
        )

        break


if start_position is None:

    raise ValueError(
        "Could not find the beginning of the novel."
    )


# =========================================================
# FIND NOVEL END
# =========================================================

end_markers = [
    "*** END OF THE PROJECT GUTENBERG EBOOK",
    "*** END OF THE PROJECT GUTENBERG",
]


end_position = None


for marker in end_markers:

    position = text.upper().find(
        marker.upper(),
        start_position
    )

    if position != -1:

        end_position = position

        print(
            f"End marker found: {marker}"
        )

        print(
            f"End position: {position:,}"
        )

        break


if end_position is None:

    raise ValueError(
        "Could not find the end of the novel."
    )


# =========================================================
# EXTRACT NOVEL BODY
# =========================================================

clean_text = text[
    start_position:end_position
]


# =========================================================
# NORMALIZE NEWLINES ONLY
# =========================================================

clean_text = clean_text.replace(
    "\r\n",
    "\n"
)

clean_text = clean_text.replace(
    "\r",
    "\n"
)


# Remove excessive blank lines at the very edges.
# Internal novel formatting is preserved.

clean_text = clean_text.strip()


# =========================================================
# WRITE CLEAN FILE
# =========================================================

CLEAN_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


CLEAN_FILE.write_text(
    clean_text,
    encoding="utf-8",
    newline="\n"
)


# =========================================================
# REPORT
# =========================================================

print()
print("CLEANING COMPLETE")
print("------------------")

print(
    f"Clean characters: "
    f"{len(clean_text):,}"
)

print(
    f"Clean words: "
    f"{len(clean_text.split()):,}"
)

print(
    f"Clean lines: "
    f"{len(clean_text.splitlines()):,}"
)

print()

print(
    f"Saved to: {CLEAN_FILE}"
)

print()
print(
    "Raw source was not modified."
)