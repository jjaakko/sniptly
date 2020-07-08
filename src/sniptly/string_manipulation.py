import re


def remove_leading_whitespace(content: str) -> str:
    """Remove leading whitespace from multiline strings.

    Removes the first line if it is empty. Calculates the number of whitespace characters in the
    first line of the resulting string and removes that many white space characters from the
    beginning of each line.
    """

    # Remove first line if it is empty.
    # See https://stackoverflow.com/a/1331840/692695 for referencing newline in platform independent way.
    content = re.sub(r"^(\r\n?|\n)", "", content)

    # Calculate leading white space.
    line_without_whitespace_at_left_end: str = content.lstrip()
    leading_whitespace_length: int = len(content) - len(
        line_without_whitespace_at_left_end
    )

    # Strip leading white space.
    content = re.sub(
        r"^\s{" + str(leading_whitespace_length) + r"}", "", content, flags=re.MULTILINE
    )
    return content
