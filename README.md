# pkgcreator

**Create python package structure, necessary files with content, git repository and venv.**

Developed and maintained by [Philipp Meder](https://github.com/PhilippMeder).

- **Source code**: https://github.com/PhilippMeder/REPOSITORYNAME.git
- **Report bugs**: https://github.com/PhilippMeder/REPOSITORYNAME/issues

Quick overview:

1. [License](#license)
2. [Usage](#usage)
3. [Features](#features) **(most interesting part)**
4. [Requirements and Dependencies](#requirements-and-dependencies)

## License

Distributed under the [BSD 3-Clause License](./LICENSE).

## Usage

You may directly call one of the two following lines:

```bash
pkgcreator [OPTIONS]
python -m pkgcreator [OPTIONS]
```

For a list of available options, run:

```bash
pkgcreator --help
```

For a list of available licenses to choose from, run:

```bash
pkgcreator --list-licenses
```

## Features

Following features are covered here, with focus on the main feature **[Package Structure Creator](#package-structure-creator)**.

1. [Package Structure Creator](#package-structure-creator)
    1. [Creating the package structure](#creating-the-package-structure)
    2. [Configuring the creation process and adding Git/venv](#configuring-the-creation-process-and-adding-gitvenv)
    3. [Configuring project settings](#configuring-project-settings)
    4. [Using preselections and suggestions](#using-preselections-and-suggestions)
2. [GitHub Downloader](#github-downloader)
    1. [Python version](#python-version)
    2. [Bash version](#bash-version)

### Package Structure Creator

Create a typical file structure for a python package with the necessary files and their content.

#### Creating the package structure

Running `pkgcreator <NAME>` will create the following package structure as offically recommended:

- `NAME`
  - `src/NAME`
    - `__init__.py`
    - `__main__.py` (if the `--script` option is used)
  - `.gitignore` (with some presets)
  - `LICENSE` (with content if the `-l, --license>` option is used)
  - `pyproject.toml` (with content according to the options used, see `--help`)
  - `README.md` (with content according to the options used, see `--help`)

#### Configuring the creation process and adding Git/venv

There are several important options you may consider when creating the package structure:

- Adding a license text with `--license <LICENSE>`:

  Using the `-l, --license <LICENSE>` option allows you to add the text of `<LICENSE>` if this is a valid identifier. To list all available identifiers, use `--list-licenses`. This option requires the python package `requests` and will fail if it is not installed.

- Initalising a Git repository with `--git`:

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
| `--github-username` | used for various project urls (if not provided) |
| `--github-repositoryname` | used for various project urls (if not provided), suggests the package name if not set |

In addition, a typical package also links to some of its online ressources.
If not set, each of them will link to a subpage of the github repository defined by `--github-username` and `--github-repositoryname`.

- `--changelog`
- `--documentation`
- `--download`
- `--funding`
- `--homepage`
- `--issues`
- `--releasenotes`
- `--source`

### GitHub Downloader

Download a specific folder (or the entire contents) from a public GitHub repository using the GitHub API.

#### Python version

Located in: [`ghutils.py`](./src/ghutils.py)

**Features:**

* Downloads a subfolder or the full repository
* Supports branch selection
* Recursive or non-recursive download

**Usage:**

```bash
python ghutils.py ExampleOwner example_repo \
  --branch main \
  --subfolder src/utils \
  --destination ./downloaded_code
```

To download the entire repository contents (default branch `main`):

```bash
python ghutils.py ExampleOwner example_repo
```

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

## Requirements and Dependencies

Following **requirements** must be satisfied:

* `Python 3.13+` (may work with lower versions, but not tested)

Following **optional dependencies** are recommended, but not required:

* `requests` library (for Python GitHub downloader and license selection/download)
* `Git` (for sparse-checkout Bash script or if you want to initalise a Git repository when creating a Python package)

To install Python dependencies you may use:

```bash
pip install DEPENDENCY
```