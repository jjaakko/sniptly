from typing import List


def extensions_to_glob_patterns(extensions: List) -> List[str]:
    """Generate a list of glob patterns from a list of extensions.
    """
    patterns: List[str] = []
    for ext in extensions:
        pattern = ext.replace(".", "*.")
        patterns.append(pattern)

    return patterns
