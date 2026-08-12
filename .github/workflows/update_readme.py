"""
Update the README.md "current release" version after a GitHub release.

The README contains exactly one marker pair delimiting the version string:

    <!-- RBP-VERSION -->`2.3.0.0`<!-- /RBP-VERSION -->

Only that marked span is rewritten. Everything else in the file is preserved
byte-for-byte (UTF-8 content and CRLF line endings included), so unrelated
version numbers - IronPython 2.7.12/3.4.2, Dynamo versions, the upstream BVN
installer link, four-part assembly versions, etc. - are never touched.

If the marker pair is missing or ambiguous, the script exits non-zero so the
workflow fails loudly instead of mangling the README.

Environment variables:
    TAG_VALUE         Release tag, e.g. "2.3.0.0", "v2.3.0.0" or "v2.3.0.0-beta".
    VERSION_NUM       Legacy fallback used only when TAG_VALUE is unset.
    GITHUB_WORKSPACE  Repository root (optional; defaults to current directory).
"""

import os
import re
import sys

README_FILE_NAME = "README.md"

# The marker pair in README.md that wraps the displayed current-release version.
VERSION_SPAN_PATTERN = re.compile(
    r"<!--\s*RBP-VERSION\s*-->.*?<!--\s*/RBP-VERSION\s*-->",
    re.DOTALL,
)
VERSION_SPAN_TEMPLATE = "<!-- RBP-VERSION -->`{version}`<!-- /RBP-VERSION -->"

# Accepts 2.1.1, 2.1.1.0, and optional pre-release suffixes such as -beta.
VERSION_TEXT_PATTERN = re.compile(r"\d+\.\d+\.\d+(\.\d+)?(-[0-9A-Za-z.]+)?")


def normalize_display_version(raw_tag):
    """Return the tag text to display: leading 'v' stripped, suffix kept."""
    tag = raw_tag.strip()
    if tag.lower().startswith("v"):
        tag = tag[1:]
    if not VERSION_TEXT_PATTERN.fullmatch(tag):
        raise ValueError(
            f"Release tag {raw_tag!r} does not look like a version number."
        )
    return tag


def update_readme():
    raw_tag = os.getenv("TAG_VALUE") or os.getenv("VERSION_NUM")
    if not raw_tag:
        sys.exit("ERROR: neither TAG_VALUE nor VERSION_NUM is set.")

    try:
        version = normalize_display_version(raw_tag)
    except ValueError as exc:
        sys.exit(f"ERROR: {exc}")

    workspace = os.getenv("GITHUB_WORKSPACE")
    if workspace:
        os.chdir(workspace)

    # newline="" round-trips the original CRLF/LF bytes untouched.
    with open(README_FILE_NAME, "r", encoding="utf-8", newline="") as file:
        readme = file.read()

    matches = VERSION_SPAN_PATTERN.findall(readme)
    if len(matches) != 1:
        sys.exit(
            f"ERROR: expected exactly 1 RBP-VERSION marker pair in "
            f"{README_FILE_NAME}, found {len(matches)}. Refusing to edit."
        )

    replacement = VERSION_SPAN_TEMPLATE.format(version=version)
    # Lambda replacement avoids any regex group-reference surprises.
    updated = VERSION_SPAN_PATTERN.sub(lambda _: replacement, readme, count=1)

    if updated == readme:
        print(f"README.md already shows version {version}; nothing to do.")
        return

    with open(README_FILE_NAME, "w", encoding="utf-8", newline="") as file:
        file.write(updated)

    print(f"README.md version span: {matches[0]!r}")
    print(f"README.md updated to  : {replacement!r}")


if __name__ == "__main__":
    update_readme()
