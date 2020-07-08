import os
from typing import List, Dict, Tuple
from enum import Enum
from pathlib import Path
from typing import Dict
import toml
from appdirs import user_data_dir
import sniptly.config
from sniptly.output import err, out
from sniptly.utils import extensions_to_glob_patterns


def guess_vscode_snippet_dir() -> Path:
    """Get the directory where vscode stores user snippets.

    Returns:
        Path: Path object corresponding the vscode snippets directory.
    """
    app_name: str = "Code"
    username: str = os.getlogin()
    # roaming=True is needed for Windows.
    vscode_user_data_dir: str = user_data_dir(
        app_name, username, roaming=True
    )  # type: ignore
    snippet_dir: Path = Path(vscode_user_data_dir + "/User/snippets")
    return snippet_dir


def get_config(path) -> Tuple[Dict, Path]:
    """Load sniptly.toml configuration file.

    Returns:
        Dict: Configuration.
    """

    try:
        config_file_path = find_config_file(path)
        with open(config_file_path, "r") as f:
            file_contents = f.read()
            config: Dict = toml.loads(file_contents)  # type: ignore
    except FileNotFoundError as e:
        err(str(e))
        out(
            f"Create a default config file in current directory by running `sniptly create-config` and "
            "modify it for your needs."
        )
        import sys

        sys.exit(1)

    return config, config_file_path


def find_config_file(src: Path) -> Path:
    """Look for sniptly.toml config file

    Args:
        src (Path): File or folder where to look for sniptly snippets.

    Raises:
        FileNotFoundError

    Returns:
        Path: Path to tohe config file.
    """
    parents = src.resolve().parents
    paths_to_search_in = [src] + list(parents) if src.is_dir() else parents
    for path in paths_to_search_in:
        if (path / "sniptly.toml").exists():
            return path / "sniptly.toml"
    raise FileNotFoundError(
        f"Config file was not found. Looked in {str(paths_to_search_in)}"
    )


def get_extension_to_lang(config: Dict):
    """Based on configuration, return a dictionary that maps file extension to a specific language,
    such python, javascript etc.

    Args:
        config (dict): Configuration.
    """
    extension_to_lang = {}
    for lang_name, conf_dict in config["languages"].items():
        for ext in conf_dict["extensions"]:
            extension_to_lang[ext] = lang_name

    return extension_to_lang


class Config:
    """Provide interface for configuration."""

    # These will be overridden when initialize is called.
    config: Dict = {}
    extension_to_lang: Dict[str, str] = {}
    start_sequence: str = ""
    stop_sequence: str = ""

    @classmethod
    def initialize(cls):
        """Read values from config file.
        """
        cls.config, config_file = sniptly.config.get_config(Path.cwd())
        out(f"Using config file: {config_file}.")

        cls.start_sequence = cls.config["start_sequence"]
        cls.stop_sequence = cls.config["stop_sequence"]

        cls.extension_to_lang = get_extension_to_lang(cls.config)

    @classmethod
    def get_enabled_languages(cls) -> List[str]:
        """Generate list of enabled languages.

        Returns:
            List[str]: enabled languages.
        """

        enabled_languages = [
            lang for lang, data in cls.config["languages"].items() if data["enabled"]
        ]
        return enabled_languages

    @classmethod
    def get_search_patterns(cls) -> List[str]:
        """Generate glob patterns for all enabled languages.

        Returns:
            List[str]: glob patterns.
        """
        patterns: List[str] = []
        for _lang, data in cls.config["languages"].items():
            if data["enabled"]:
                patterns.extend(extensions_to_glob_patterns(data["extensions"]))

        return patterns

    @classmethod
    def extension_to_comment_char(cls, ext: str) -> str:
        comment: str = cls.config["languages"][cls.extension_to_lang[ext]][
            "comment_character"
        ]
        return comment

    @classmethod
    def get_start_sequence(cls, ext: str) -> str:
        comment: str = cls.config["languages"][cls.extension_to_lang[ext]][
            "comment_character"
        ]
        return cls.start_sequence.format(comment)

    @classmethod
    def get_stop_sequence(cls, ext: str) -> str:
        comment: str = cls.config["languages"][cls.extension_to_lang[ext]][
            "comment_character"
        ]
        return cls.stop_sequence.format(comment)

    @classmethod
    def map_extension_to_file_name(cls, ext: str):
        return f"{cls.extension_to_lang[ext]}.json"

    @classmethod
    def map_lang_to_extension(cls, lang: str):
        # Take the first extension but leave out the first character, the dot.
        extension = cls.config["languages"][lang]["extensions"][0][1:]
        return extension

    @classmethod
    def get_vscode_snippet_dir(cls):
        return Path(cls.config["vscode_snippets_dir"])


def get_default_config() -> str:
    """Generate contents for a default config file.

    Returns:
        str: Configuration as a string.
    """

    default_config_d: dict = {
        "start_sequence": "{} -->",
        "stop_sequence": "{} <--",
        "vscode_snippets_dir": str(guess_vscode_snippet_dir().resolve()),
        "languages": {
            "python": {
                "comment_character": "#",
                "enabled": True,
                "extensions": [".py"],
            },
            "javascript": {
                "comment_character": "//",
                "enabled": True,
                "extensions": [".js"],
            },
        },
    }
    default_config: str = toml.dumps(default_config_d)

    return default_config


def create_config_file(config: str):
    """Create default config file.

    Args:
        config (str): Configuration to write.
    """
    config_file_path: Path = Path().cwd() / "sniptly.toml"
    if config_file_path.exists():
        raise Exception(f"Config file {str(config_file_path)} already exists.")
    try:
        with open(config_file_path, "w") as f:
            f.write(config)
    except Exception as e:
        raise Exception(
            f"Exception occured for when processing {str(config_file_path)}"
        )


class SniptlyLines(Enum):
    START_SEQUENCE = 1
    STOP_SEQUENCE = 2
