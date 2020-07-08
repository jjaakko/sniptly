from pathlib import Path
import shutil
from typing import Optional, List, Dict, Tuple, Union
import tempfile
import json
import re
import jstyleson

from sniptly.config import Config, SniptlyLines
from sniptly.file_line_wrapper import FileLineWrapper
from sniptly.types import Snippet, Snippets
from sniptly.string_manipulation import remove_leading_whitespace
from sniptly.output import out, err


class SniptlySyntaxException(Exception):
    pass


class SniptlyPreviousSnippetContinues(Exception):
    pass


def get_key_from_filename(base: str, suffix: str) -> str:
    if suffix == "":
        # We have to have a hashable key to map files that don't have suffix.
        key = base
    else:
        key = suffix
    return key


def get_filepaths_for_existing_json_snippets(snippet_dir: Path) -> List[Path]:
    """Get file paths for existing snippets in json format.

    Args:
        snippet_dir (Path): Snippet directory.
    """
    filepaths_to_existing_snippets: List[Path] = []
    for item in Path(snippet_dir).iterdir():
        if item.is_file() and item.stem in Config.get_enabled_languages():
            filepaths_to_existing_snippets.append(snippet_dir / item)

    return filepaths_to_existing_snippets


def get_json_snippets_from_file(snippet_filepath: Path) -> Dict[str, Snippet]:
    """Load json snippets from a file.

    Args:
        snippet_filepath (Path): Snippet file.

    Returns:
        Dict[str, Snippet]: Snippets from the file as a dictionary.
    """
    with open(snippet_filepath) as file:
        content = file.read()
    data: Dict[str, Snippet] = jstyleson.loads(content)
    return data


def matches_sequence(
    string: str, filename_suffix: str, sequence_type: SniptlyLines
) -> bool:
    """Check whether a string matches a sequence type such as START_SEQUENCE for sniptly code snippet.

    This function is used to test whether a sequence starts or ends.

    Args:
        string (str): String (a line from a file usually).
        filename_suffix (str): Suffix is needed as comment character is language dependent.
        sequence_type (SniptlyLines): [description]
    """
    sequence: str
    if sequence_type == SniptlyLines.START_SEQUENCE:
        sequence = Config.get_start_sequence(filename_suffix)
    elif sequence_type == SniptlyLines.STOP_SEQUENCE:
        sequence = Config.get_stop_sequence(filename_suffix)
    else:
        return False
    pattern: str = r"\s*" + sequence + r"\s*$"
    if re.search(pattern, string):
        return True
    return False


def get_sniptly_line_type_and_value(
    string: str, filename_suffix: str, strict_mode=False
) -> Union[Tuple[str, str]]:
    """Gets the name and value of a snitply code template property.

    Property can be `name`, `description` or `prefix` which correspond to the properties
    in json snippet format.

    Client sets strict_mode to false only when checking the first line following start sequence.
    This line can be a normal code line if the snippet has been collecting lines previously.

    Args:
        string (str): String (a line from a file usually).
        filename_suffix (str): Suffix is needed as comment character is language dependent.
        strict_mode (bool, optional): [description]. Defaults to False.

    Raises:
        SniptlySyntaxException: if the string does not match any of the properties and strict_mode is true.
        SniptlyPreviousSnippetContinues: if the string does not match any of the properties and strict_mode is false.

    Returns:
        Union[Tuple[str, str]]: [description]
    """
    stripped_string: str = string.strip(" \t\n")
    pattern: str = r"" + f"{Config.extension_to_comment_char(filename_suffix)} " + r"(?P<property_name>name|description|prefix): (?P<property_value>.+)"
    match = re.search(pattern, stripped_string)
    if match:
        property_name: str = match.group("property_name")
        property_value: str = match.group("property_value")
        return (property_name, property_value)
    elif strict_mode:
        raise SniptlySyntaxException(f"Incorrect syntax")
    else:
        raise SniptlyPreviousSnippetContinues()


def build_json_snippets_from_sniptly_snippets(filename: Path) -> Dict[str, Snippet]:
    """Build snippets in vscode format from sniptly code snippets.

    Args:
        filename (Path): A single code file containing code snippets.

    Raises:
        SniptlySyntaxException: if sniptly code snippet syntax is not valid.

    Returns:
        Dict[str, Snippet]: Dict containing snippets read from the file.
    """
    snippets: Dict[str, Snippet] = {}
    snippet_name: Optional[str] = None
    snippet_types: Tuple[str, str, str] = ("name", "prefix", "description")
    snippet_data: Dict[str, str] = {}
    # Indicates whether a line resides inside start and end sequence, that is, whether the current line
    # should be processed either for reading snippet meta information or reading snippet code lines.
    collect_lines: bool = False
    next_line: str = ""
    with FileLineWrapper(open(filename, "r")) as file:
        line: str = file.readline()
        leading_whitespace_length: int = 0

        while line:
            if matches_sequence(line, filename.suffix, SniptlyLines.START_SEQUENCE):
                try:
                    # Read next three lines from the file to extract snippet name, prefix and description.
                    for snippet_type in snippet_types:
                        # Readline returns empty string when all the lines have been read.
                        next_line = file.readline()

                        strict_mode = (
                            False if snippet_type == "name" and snippets != {} else True
                        )
                        (
                            line_snippet_type,
                            property_value,
                        ) = get_sniptly_line_type_and_value(
                            next_line, filename.suffix, strict_mode
                        )

                        # Make sure that this line has the correct type, such as "prefix" for example
                        if line_snippet_type == snippet_type:
                            snippet_data[snippet_type] = property_value
                        else:
                            raise SniptlySyntaxException()

                        collect_lines = True

                except (TypeError, SniptlySyntaxException):
                    err(f"Incorrect syntax in {str(filename)} on line {file.line}")
                except SniptlyPreviousSnippetContinues:
                    leading_whitespace_length = add_content_line_and_get_leading_whitespace_length(
                        next_line, snippet_name, snippets, leading_whitespace_length
                    )
                    line = file.readline()
                    collect_lines = True
                    continue

                snippet_name = snippet_data["name"]
                snippet: Snippet = {
                    "prefix": snippet_data["prefix"],
                    "body": [],
                    "description": snippet_data["description"],
                }
                snippets[snippet_name] = snippet
            elif matches_sequence(line, filename.suffix, SniptlyLines.STOP_SEQUENCE):
                # Snippet end sequence on the current line, do not process lines until
                # snippet start sequence found.
                collect_lines = False
                # Set indent for actual code lines to zero, if indent is present
                # this value will be recalculated.
                leading_whitespace_length = 0
            elif collect_lines:
                leading_whitespace_length = add_content_line_and_get_leading_whitespace_length(
                    line, snippet_name, snippets, leading_whitespace_length
                )

            line = file.readline()
    return snippets


def add_content_line_and_get_leading_whitespace_length(
    line, snippet_name, snippets, leading_whitespace_length
):
    """Adds a new code line to a snippet by modifying the snippets argument inline.

    Calculates white space length if the line is the first code line to be added to the snippet.

    Args:
        line ([type]): New code line to add.
        snippet_name ([type]): Name of the snippet.
        snippets ([type]): Existing snippets.
        leading_whitespace_length ([type]): whitespace length for adjusting indents.

    Returns:
        [type]: Returns whitespace length in the beginning of the line.
    """
    if not snippets[snippet_name]["body"]:
        # This is the first actual code line.
        # Calculate the length of leading whitespace, length can be also zero.

        # Note: This logic cannot handle situations
        # where snippet has been previously started, but it now continues
        # from different level of indentation as snippets[snippet_name]["body"] exists already
        # and we don't want don't want to recalculate leading_whitespace_length otherwise
        # indentation for code consisting of different indent levels could be messed up.
        line_without_whitespace_at_left_end: str = line.lstrip()

        # This is calculated from the level where the snippet is defined. If the indent of snippet definition
        # is for example 4, this amount of characters are ignored from the beginning of snippet code line.
        leading_whitespace_length = len(line) - len(line_without_whitespace_at_left_end)
    line_without_whitespace_at_right_end: str = line.rstrip()[
        leading_whitespace_length:
    ]
    snippets[snippet_name]["body"].append(line_without_whitespace_at_right_end)
    return leading_whitespace_length


def dump_to_file(snippets: Snippets):
    """Writes snippets to a temporary file.

    Returns:
        [type]: Path to the created file.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(json.dumps(snippets, indent=2))
    return f.name


def get_sniptly_snippet_template(extension: str) -> Snippets:
    """Creates a snippet for producing a template for sniptly code snippets.

    Args:
        extension (str):  extension is needed as comment characters are language dependent.
    """
    comment = Config.extension_to_comment_char(extension)
    snitply_snippet_template: Snippets = {
        "sniptly snippet template": {
            "prefix": "sniptly_snippet_template",
            "body": [
                Config.get_start_sequence(extension),
                f"{comment} name: [my awesome snippet]",
                f"{comment} prefix: [prefix for my awesome snippet]",
                f"{comment} description: [snippet description]",
                Config.get_stop_sequence(extension),
            ],
            "description": "Template for creating sniptly snippets. Replace the brackets and the text within the brackets with your snippet information.",
        }
    }
    return snitply_snippet_template


def get_sample_file_content() -> str:
    content: str = """
    # -->
    # name: [my awesome snippet]
    # prefix: [prefix for my awesome snippet]
    # description: [snippet description]
    import json
    data = {"foo": "bar"}
    data_as_json = json.dumps(data, indent=2)
    with open("file.json", "w") as f:
        f.write(data_as_json)
    # <--
    """
    content_final = remove_leading_whitespace(content)
    return content_final


def create_sample_file():
    sample_file: Path = Path().cwd() / "python_sniptly_snippets.py"
    content = get_sample_file_content()
    if sample_file.exists():
        raise Exception(f"File {str(sample_file)} already exists.")
    try:
        with open(sample_file, "w") as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"Exception occured for when processing {str(sample_file)}")


def get_existing_snippets(
    path_to_existing_snippets: Path, rm_existing: bool
) -> Snippets:
    """Get existing snippets from vscode or return an empty dict.

    Args:
        path_to_existing_snippets (Path): Filepath.
        rm_existing ([type]): If rm_existing is true ignore existing snippets and return an empty dict.
    """
    if path_to_existing_snippets.exists() and not rm_existing:
        # If the source exists and --rm-existing flag is not present,
        # add new snippets and update existing ones.
        existing_snippets = get_json_snippets_from_file(path_to_existing_snippets)
    else:
        # There are no existing snippets or the existing ones are to be removed.
        existing_snippets = {}

    return existing_snippets


def get_combined_snippets(existing_snippets, sniptly_snippets, file_ext):
    sniptly_snippet_template = get_sniptly_snippet_template(file_ext)
    # Combine the old snippets, if any, and the new snippets. Add sniptly snippet
    # template as one code snippet.
    combined_snippets: Snippets = {
        **existing_snippets,
        **sniptly_snippets,
        **sniptly_snippet_template,
    }
    return combined_snippets


def write_json_snippet_file(
    snippets_to_write, target_directory, dst_file_basename, snippets, file
):
    new_json_snippet_file = Path(dump_to_file(snippets_to_write))

    dst: Path = Path(f"{target_directory}/{dst_file_basename}")
    if not target_directory.exists():
        # If the destination folder that file is to be created in does not exist, create it.
        target_directory.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(new_json_snippet_file), str(dst))
    new_json_snippet_file.unlink()
    if snippets:
        out(f"Built {len(snippets)} code snippets from {str(file)} to {str(dst)}.\n")
