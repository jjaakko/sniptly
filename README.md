# Sniptly

A Python command line tool for managing [user defined code snippets](https://code.visualstudio.com/docs/editor/userdefinedsnippets) in code for [vscode](https://code.visualstudio.com/).

Sniptly makes it possible to mantain code snippets in code and build the json representation vscode uses for code snippets when needed. Maintaining snippets in code is more convenient and allows one to benefit from code formatters or, for larger code snippet libraries, to have unit tests for the snippets.

Sniptly is at experimental stage for now. It is tested to some extent with Python. In principle, it *should* work with other languages as well.

# Installation

To install the latest release on PYPI run

```
pip install sniptly
```
# Usage

- Create configuration file by running `snitply create-config`
- Edit the newly created `sniptly.toml` configuration file by adding the languages you wish to create code snippets for. By default the configuration specifies to look for python and javascript files.
- **NOTE**: Sniptly tries to figure out the folder where vscode keeps user snippets. Verify that the `vscode_snippets_dir` configuration has the correct value.
- Optional steps with first time usage
    - Run `sniptly create-sample` to create a sample file named `python_sniptly_snippets.py` with sniptly comments. See [the file contents](#sample) to understand how comments are used to turn code fragments to user defined code snippets in vscode.
    - Run `sniptly build --source python_sniptly_snippets.py` to build the code snippet and to add the snippet to your existing vscode snippets.
    - Add sniptly code snippet template by running `sniptly add-snippet-template --lang [language, for example: python]`. Code from which to generate code snippets is commented with special comments. By adding the template as a code snippet it's easy to turn existing code fragments to vscode snippets.
- Start adding sniptly comments for the code fragments you want to turn into vscode snippets
- Run `sniptly build --source [file or folder]` to build code snippets from the specified file or folder for the languages you have enabled in `sniptly.toml`

# Syntax for marking code fragments for snippet creation

The start sequence will specify where the snippet starts. The following lines specify name, prefix and description that will be used in the vscode's json representation for user defined code snippets. The end sequence ends the snippet.

Syntax can be modified via `sniptly.toml`. The `{}` in `start_sequence` and `stop_sequence` will be replaced by the value set in `comment_character`.

 See the sample file contents below to see how code fragments can be marked for snippet creation.

<a id="sample"></a>
# Example of Python code fragment marked for snippet creation

```python
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
```