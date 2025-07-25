<h1 align="center">
<img src="./docs/figs/pkgcreator_logo.svg" width="300">
</h1>

`pkgcreator` is a Python CLI tool that helps you quickly set up a new Python package with a recommended folder structure, a virtual environment, license file, Git repository, and pre-filled configuration files like `pyproject.toml` and `README.md`.

It supports interactive prompts, smart defaults (e.g. from your Git config), and includes additional utilities like a GitHub folder downloader, CLI/formatter helpers, and virtual environment management.

Whether you're preparing a new project or just want a clean setup for your next internal tool — `pkgcreator` automates the boilerplate and saves you time.

Developed and maintained by [Philipp Meder](https://github.com/PhilippMeder).

- **Source code**: https://github.com/PhilippMeder/pkgcreator.git
- **Report bugs**: https://github.com/PhilippMeder/pkgcreator/issues

Quick overview:

1. [Quick Start](#quick-start)
2. [License](#license)
3. [Features](#features) **(most interesting part)**
4. [Requirements and Dependencies](#requirements-and-dependencies)

## Quick Start

Install this package (replace `pkgcreator` with `pkgcreator[full]` to install all optional dependencies on Python packages):

```bash
pip install pkgcreator
```

Create a new package structure, initialise Git, create a virtual environment, and include the *MIT license*:

```bash
pkgcreator create mypackage --git --venv --license MIT
```

For a detailed list of available options, see the section [Package Structure Creator](#package-structure-creator).

## License

Distributed under the [BSD 3-Clause License](./LICENSE).

## Features

Following features are covered here, with focus on the main feature **[Package Structure Creator](#package-structure-creator)**.

1. [Package Structure Creator](#package-structure-creator)
    1. [Creating the package structure](#creating-the-package-structure)
    2. [Configuring the creation process and adding Git/venv](#configuring-the-creation-process-and-adding-gitvenv)
    3. [Configuring project settings](#configuring-project-settings)
    4. [Using preselections and suggestions](#using-preselections-and-suggestions)
2. [Accessing Git with Python](#accessing-git-with-python)
3. [GitHub Downloader](#github-downloader)
    1. [Python version](#python-version)
    2. [Bash version](#bash-version)
4. [Creating and Managing Virtual Environments](#creating-and-managing-virtual-environments)
5. [Tools](#tools)
    1. [Logging tools](#logging-tools)
    2. [CLI tools](#cli-tools)

To use the core features, you may directly call one of the two following lines:

```bash
pkgcreator [OPTIONS]
python -m pkgcreator [OPTIONS]
```

For a list of available options, see the next sections or run:

```bash
pkgcreator --help
```

### Package Structure Creator

Create a typical file structure for a python package with the necessary files and their content.

#### Creating the package structure

Running `pkgcreator create <NAME>` will create the following package structure as officially recommended:

- `NAME`
  - `src/NAME`
    - `__init__.py`
    - `__main__.py` (if the `--script` option is used)
  - `.gitignore` (with some presets)
  - `LICENSE` (with content if the `-l, --license>` option is used)
  - `pyproject.toml` (with content according to the options used, see `--help`)
  - `README.md` (with content according to the options used, see `--help`)

For a list of available options, read the next sections or run:

```bash
pkgcreator create --help
```

#### Configuring the creation process and adding Git/venv

There are several important options you may consider when creating the package structure:

- Adding a license text with `--license <LICENSE>`:

  Using the `-l, --license <LICENSE>` option allows you to add the text of `<LICENSE>` if this is a valid identifier. To list all available identifiers, use `--list-licenses`. This option requires the python package `requests` and will fail if it is not installed.

- Initialising a Git repository with `--git`:

  If `Git` is available on your system, using the `--git` option automatically initialises a Git repository and commits all created files.

- Creating a virtual environment with `--venv`:

  Using the `--venv` option automatically creates a virtual environment in `NAME/.venv` (ignored by `Git`) and installs the created package in editable mode so you can run it as `python -m <NAME>` or import it with `import <NAME>` inside the activated environment.

- Providing the package as a script with `--script`:

  Using the `--script` option will create a `__main__.py` with function `main()` that is called whenever you run the package as a module (`python -m <NAME>`). In addition, the `pyproject.toml` registers the terminal command `<NAME>` that will also call this function.

#### Using preselections and suggestions

If not explicitly set, some arguments will suggest values based on context:

- `--github-repositoryname` may suggest using the package name
- `--author-name` may suggest using `user.name` from `git config`, if available
- `--author-mail` may suggest using `user.email` from `git config`, if available
- `--git` may ask whether to initialise a Git repository
- `--venv` may ask whether to initialise a virtual environment and install the package in editable mode

Use the `-m, --prompt-mode` option to control whether these suggestions are shown or automatically handled:

| Option                   | `yes` | `auto` | `no`  |
|--------------------------|:-----:|:------:|:-----:|
| `--github-repositoryname`|  ✅   |   ✅    |  ❌   |
| `--author-name`          |  ✅   |   ✅    |  ❌   |
| `--author-mail`          |  ✅   |   ✅    |  ❌   |
| `--git`                  |  ✅   |   ❌    |  ❌   |
| `--venv`                 |  ✅   |   ❌    |  ❌   |

- `yes`: Automatically accept all suggestions
- `no`: Skip all prompts and use defaults or leave unset
- `auto`: Accept safe suggestions only (e.g., use Git info, but skip Git initialisation)
- `ask` *(default)*: Prompt interactively for each case, and ask again before creating the project structure

#### Configuring project settings

There are a bunch of variables that are used for the creation of the `pyproject.toml`, `README.md`, and `LICENSE` (if `-l` is used).

**These can be changed later in the mentioned files.**

Available options are (the names are self-explanatory):

| Option |  Notes |
|--------|------------|
| `--description` |   |
| `--author-name` | suggests `git config user.name` if not set |
| `--author-mail` | suggests `git config user.email` if not set |
| `--github-username` | used for various project URLs (if not provided) |
| `--github-repositoryname` | used for various project URLs (if not provided), suggests the package name if not set |

In addition, a typical package also links to some of its online resources.
If not set, each of them will link to a subpage of the github repository defined by `--github-username` and `--github-repositoryname`.

- `--changelog`
- `--documentation`
- `--download`
- `--funding`
- `--homepage`
- `--issues`
- `--releasenotes`
- `--source`

If some dependencies, optional dependencies or classifiers (for PyPI) are already known, they can be set with the following commands:

- `--dependencies package1 package2 ...`
- `--optional-dependencies package1 package2 ...` (available as a `[full]` option during package installation)
- `--classifiers classifier1 classifier2 ...` (for a full list see [PyPI classifier](https://pypi.org/classifiers/))

### Accessing Git with Python

This feature is provided for completeness since it is used as a handy tool during the package structure creation process.
You may run

```bash
pkgcreator git --help
```

to list the available options.
However, **running Git directly** is usually more flexible and preferred.

### GitHub Downloader

Download a specific folder (or the entire contents) from a public GitHub repository using the GitHub API.

#### Python version

**Features:**

* Downloads a subfolder or the full repository
* Supports branch selection
* Recursive or non-recursive download

**Usage:**

To download the repository contents (default branch `main`), run:

```bash
pkgcreator github-download <OWNER> <REPOSITORY> [OPTIONS]
```

Available options are (run `pkgcreator github-download --help` for a full list):

- `-b, --branch` Selects the branch name (default: *main*).
- `-s, --subfolder` If not provided, download the full repository. If set to a subdirectory of the repository, download this subdirectory. If set to a single file, only download this file.
- `-d, --destination` Local directory where the files should be downloaded to (default: *./downloaded_<REPOSITORY>*).
- `-n, --no-recursive` Do not download folders recursively.
- `--list` List the content of the repository (or the given subfolder) and exit.

**Note:** The GitHub API limits the number of requests per time period. For more information see the [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

#### Bash version

For completeness, a bash version is provided.

Located in: [`github_download.sh`](./scripts/github_download.sh)

**Features:**

* Uses `git sparse-checkout` to efficiently fetch only a folder
* Minimal download size, ideal for large repositories

**Usage:**

```bash
./github_download.sh ExampleOwner example_repo main ./target_folder subdir/in/repo
```

Arguments:

```text
<owner> <repo> [branch=main] [target_dir=<repo>_sparse] [folder=None]
```

If no folder is specified, the full repository is checked out.

### Creating and Managing Virtual Environments

The command

```bash
pkgcreator venv [OPTIONS]
```

can create a virtual environment and install packages in this environment.
Available options are (run `pkgcreator github-download --help` for a full list):

- `-d, --destination` Directory where the venv folder will be created (default: current working directory).
- `-c, --create` Create the virtual environment.
- `-i, --install` List of packages to install (via pip).
- `-e, --editable` List of packages/local package paths to install in editable mode (-e).
- `--name` Name of the virtual environment folder (default: .venv).
- `--version-suffix` Append Python major/minor version to the venv folder name.

### Tools

In addition to the main features, also some useful tools that were written for the functionality of this package are available.

#### Logging tools

- `LoggerFormatter` provides a formatter that is a subclass of the standard library's `logging.Formatter`. The logger messages will be color coded and start with `[Error], [Warning], [Info]` depending on the message type.
- `logged_subprocess_run` provides a wrapper around `subprocess.run` where the output feed of the process is streamed live to the given logger.

To use these features and understand their parameters, run:

```python
from pkgcreator.logging_tools import LoggerFormatter, logged_subprocess_run

help(LoggerFormatter)
help(logged_subprocess_run)
```

#### CLI tools

- `ConsistentFormatter` provides an `argparse.HelpFormatter` that aims at a consistent appearance. It enforces capitalization and periods where needed.
- `generate_parser_template` generates a template Python function that consistently creates an `argparse.Argparser` that is either a standalone or a subparser.

To use these features and understand their parameters, run:

```python
from pkgcreator.cli_tools import ConsistentFormatter, generate_parser_template

help(ConsistentFormatter)
help(generate_parser_template)
```

## Requirements and Dependencies

Following **requirements** must be satisfied:

* `Python 3.13+` (may work with lower versions, but not tested)

Following **optional dependencies** are recommended, but not required:

* `requests` library (for Python GitHub downloader and license selection/download)
* `Git` (for sparse-checkout Bash script or if you want to initialise a Git repository when creating a Python package)

To install Python dependencies you may either use

```bash
pip install DEPENDENCY
```

or directly specify that you want to install all optional dependencies when installing this package with:

```bash
pip install pkgcreator[full]
```