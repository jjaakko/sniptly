import filecmp
from pathlib import Path
from typing import Dict, List, Tuple
from click.testing import CliRunner
import toml

from sniptly.cli import index
from sniptly import __version__
from sniptly.types import Snippet
from sniptly.cli import build_json_snippets_from_sniptly_snippets
import sniptly.snippet_functions
import sniptly.config
from sniptly.config import Config


def get_path_to_resource(file_basename):
    filepath_relative_to_this_file = Path(__file__).parent.parent / file_basename
    return filepath_relative_to_this_file


def test_version():
    assert __version__ == "0.1.0"


def test_build_json_snippets_from_sniptly_snippets(monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)
    sniptly.config.Config.initialize()

    expected_snippets: Dict[str, Snippet] = {
        "Create Pandas dataframe": {
            "prefix": "pd_create_df",
            "body": [
                'df = pd.DataFrame({"x": [0, 1, 2, 3, 4], "y": [10, 11, 10, 9, 12]})'
            ],
            "description": "Creates Pandas dataframe",
        }
    }

    snippets: Dict[str, Snippet] = build_json_snippets_from_sniptly_snippets(
        Path("tests") / "data" / "sniptly_snippets" / "python_single_snippet.py"
    )
    assert snippets == expected_snippets


def test_build_fails_without_source(monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)

    runner = CliRunner()
    result = runner.invoke(index, ["build"])
    assert "Error: Missing option '--source'" in result.output


def test_build_succeeds_with_one_snippet(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)

    runner = CliRunner()
    source: str = str(Path("tests/data/sniptly_snippets/python_single_snippet.py"))
    result = runner.invoke(
        index, ["build", "--source", source, "--target", str(tmp_path), "--rm-existing"]
    )
    assert (
        f"Built 1 code snippets from {source} to {tmp_path}/python.json"
        in result.output
    )

    known_correct_file = Path("tests/data/json_snippets/python_single_snippet.json")
    files_match, content1, content2 = util_file_comparison(
        tmp_path / "python.json", known_correct_file
    )
    if not files_match:
        assert content1 == content2

    assert True


def test_build_succeeds_with_multiple_snippets(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)

    runner = CliRunner()
    source: str = str(Path("tests/data/sniptly_snippets/python_multiple_snippets.py"))
    result = runner.invoke(
        index, ["build", "--source", source, "--target", str(tmp_path), "--rm-existing"]
    )
    assert (
        f"Built 3 code snippets from {source} to {tmp_path}/python.json"
        in result.output
    )

    known_correct_file = Path("tests/data/json_snippets/python_multiple_snippets.json")
    files_match, content1, content2 = util_file_comparison(
        tmp_path / "python.json", known_correct_file
    )
    if not files_match:
        assert content1 == content2

    assert True


def test_toml_loads_works_as_expected():
    toml_str = """
    start_sequence = "{} -->"
    stop_sequence = "{} <--"

    [languages.python]
        comment_character = "#"
        enabled = true
        file_name_pattern = "*.py"
        extensions = [".py"]

    [languages.javascript]
        comment_character = "//"
        enabled = false
        file_name_pattern = "*.js"
        extensions = [".js"]
    """
    config = toml.loads(toml_str)
    config_expected = {
        "start_sequence": "{} -->",
        "stop_sequence": "{} <--",
        "languages": {
            "python": {
                "comment_character": "#",
                "enabled": True,
                "file_name_pattern": "*.py",
                "extensions": [".py"],
            },
            "javascript": {
                "comment_character": "//",
                "enabled": False,
                "file_name_pattern": "*.js",
                "extensions": [".js"],
            },
        },
    }
    assert config == config_expected


def test_lang_enabled_config_is_respected(monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)

    enabled_languages = Config.get_enabled_languages()
    assert enabled_languages == ["python", "javascript"]


def test_get_extension_to_lang(monkeypatch):
    monkeypatch.setattr(sniptly.config, "get_config", mock_get_config)
    Config.initialize()
    ext_to_lang = sniptly.config.get_extension_to_lang(Config.config)
    expected: Dict = {".py": "python", ".js": "javascript", ".php": "php"}
    assert ext_to_lang == expected


def util_file_comparison(file1: Path, file2: Path) -> Tuple[bool, List[str], List[str]]:
    files_match = filecmp.cmp(file1, file2)
    content1 = []
    content2 = []

    if not files_match:
        with open(file1, "r") as file:
            content1 = file.readlines()
        with open(file2, "r") as file:
            content2 = file.readlines()
        print(
            f"\nThe generated file contents do not match with the known correct file contents."
        )
        print(f"\nRun diff between the two files for more information, for instance:")
        print(f"diff -u {file2} {file1}\n")

    return files_match, content1, content2


def mock_get_config(*args, **kwargs):
    toml_str = """
        start_sequence = "{} -->"
        stop_sequence = "{} <--"

        [languages]
            [languages.python]
                comment_character = "#"
                enabled = true
                extensions = [".py"]

            [languages.javascript]
                comment_character = "//"
                enabled = true
                extensions = [".js"]

            [languages.php]
                comment_character = "//"
                enabled = false
                extensions = [".php"]
        """
    config = toml.loads(toml_str)
    return config, "foo"
