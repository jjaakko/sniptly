from typing import List, Dict, Generator, Set, Tuple, Union
from pathlib import Path
import traceback
import sys
import click

from sniptly.config import Config, get_default_config, create_config_file
from sniptly.types import Snippet
from sniptly.output import out, err

from sniptly.snippet_functions import (
    build_json_snippets_from_sniptly_snippets,
    create_sample_file,
    get_existing_snippets,
    get_combined_snippets,
    write_json_snippet_file,
)
import sniptly.snippet_functions as snp


@click.group(help="Create vscode snippets from code files.")
def index():
    pass


@click.option("--debug", is_flag=True)
@click.command(
    short_help="Create sniptly.toml configuration file in the current directory."
)
def create_config(debug):
    config: str = get_default_config()
    try:
        create_config_file(config)
        out(
            "Config file created. In the config file you can specify which languages "
            "you want to create sniptly snippets for."
        )
    except Exception as e:
        err(str(e))
        if debug:
            err(traceback.format_exc())
        sys.exit(1)


@click.option("--debug", is_flag=True)
@click.command(
    short_help="Create sample file for sniptly code snippets in the current directory."
)
def create_sample(debug):
    try:
        create_sample_file()
        out("Sample file for sniptly code snippets created.")
    except Exception as e:
        err(str(e))
        if debug:
            err(traceback.format_exc())
        sys.exit(1)


@click.command(
    short_help="Build snippets in json format for vscode from sniptly code snippets"
)
@click.option("--source", type=click.Path(exists=True), required=True)
@click.option("--target", type=click.Path(exists=False))
@click.option("--rm-existing", is_flag=True)
@click.option("--debug", is_flag=True)
def build(source: str, target: str, rm_existing: bool, debug: bool):
    """Take in code snippets in the sniptly form and produce a json file(s) adhering to the
    syntax vscode uses for defining snippets.

    Args:
        source (str): Directory of code snippets or single file.
        target (str): Where to place the json snippets.
        rm_existing (bool): Whether existing json snippets should be deleted or updated if there are
        snippets with the same names.
        debug (bool): Whether to include debug information in case of error.
    """
    Config.initialize()
    files: Union[Generator[Path, None, None], List[Path]] = []
    filename_patterns_to_search_for: List[str]
    if Path(source).is_file():
        # If source is a file, ensure that we only process that file.
        # There should be exactly one filename_patterns_to_search_for, but the value
        # does not matter as rglob will not be performed.
        filename_patterns_to_search_for = ["foo"]
        files = [Path(source)]
    else:
        filename_patterns_to_search_for = Config.get_search_patterns()

    for filename_pattern in filename_patterns_to_search_for:
        # Source can be either a single file or directory.
        if Path(source).is_dir():
            # Source is a directory, get all the files that match the pattern.
            files = Path(source).rglob(filename_pattern)
        for file in files:
            if file.name == "__init__.py":
                # Skip __init__.py
                continue

            # Build snippets from sniptly format and store them as a dictionary.
            snippets: Dict[str, Snippet] = build_json_snippets_from_sniptly_snippets(
                file
            )
            file_ext: str = file.suffix

            # If target is not specified, use vscode's user snippets directory.
            target_directory: Path = (
                Path(target) if target else Config.get_vscode_snippet_dir()
            )

            dst_file_basename: str = Config.map_extension_to_file_name(file_ext)
            path_to_existing_snippets: Path = Path(
                f"{target_directory}/{dst_file_basename}"
            )

            try:
                existing_snippets = get_existing_snippets(
                    path_to_existing_snippets, rm_existing=False
                )

                # Combine the old snippets, if any, and the new snippets. Add sniptly snippet
                # template as one code snippet.
                snippets_to_write = get_combined_snippets(
                    existing_snippets, snippets, file_ext
                )
                write_json_snippet_file(
                    snippets_to_write,
                    target_directory,
                    dst_file_basename,
                    snippets=snippets,
                    file=file,
                )
            except Exception as e:
                err(f"Exception occured for when processing {str(file)}.")
                if debug:
                    err(str(e))
                    err(traceback.format_exc())


@click.option("--lang", type=str, required=True)
@click.option("--debug", is_flag=True)
@click.command(short_help="Adds sniptly code snippet template as a snippet.")
def add_snippet_template(lang: str, debug: bool):
    Config.initialize()
    try:
        file_ext = f".{Config.map_lang_to_extension(lang)}"
        target_directory: Path = Config.get_vscode_snippet_dir()
        dst_file_basename: str = Config.map_extension_to_file_name(file_ext)
        path_to_existing_snippets: Path = Path(
            f"{target_directory}/{dst_file_basename}"
        )
        existing_snippets = get_existing_snippets(
            path_to_existing_snippets, rm_existing=False
        )
        snippets_to_write = get_combined_snippets(existing_snippets, {}, file_ext)
        write_json_snippet_file(
            snippets_to_write,
            target_directory,
            dst_file_basename,
            snippets=None,
            file=None,
        )
        out(f"Wrote to {path_to_existing_snippets}")
    except KeyError as e:
        err(f"Language {lang} is not declared in sniptly.conf.")
        if debug:
            err(str(e))
            err(traceback.format_exc())

    print(f"{lang}.json")


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


index.add_command(build)
index.add_command(create_config)
index.add_command(create_sample)
index.add_command(add_snippet_template)

if __name__ == "__main__":
    index()
