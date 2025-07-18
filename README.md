# Code Snippets

**Useful small tools, esp. for code development and worklflow.**

Developed and maintained by [Philipp Meder](https://github.com/philippmeder).

* **Source code:** https://github.com/philippmeder/snippets
* **Report bugs:** https://github.com/philippmeder/snippets/issues

## License

Distributed under the [BSD 3-Clause License](./LICENSE).


## Features

1. [Python Package Structure Generator](#python-package-structure-generator) to create a typical package structure including many common files
2. [GitHub Downloader](#github-downloader) to download the content of a repository (partially)

### Python Package Structure Generator

A simple command-line tool to create a clean folder structure for a new Python package. Optionally includes a license file.

**Features:**
- Creates
    -`src\package-name` (structure recommended for Python packages)
    -`pyproject.toml.py`
    -`README.md` (with an example structure)
    -`.gitignore` (with my current preferences)
    -`LICENSE` (see below)
- Adds a license file from a predefined list (e.g. MIT, Apache-2.0) if wanted
- Initalises a Git repository if wanted (requires `Git`)

**Usage:**

```bash
python make_python_package.py my_package --destination ./all_packages --license mit
```

To list available licenses:

```bash
python make_python_package.py my_package --list-licenses
```

To list available options with explanations:

```bash
python make_python_package.py --help
```

**About the `-m, --prompt-mode` Option**

If not explicitly set, some arguments will suggest values based on context:

- `--github-repositoryname` may suggest using the package name
- `--author-name` may suggest using `user.name` from `git config`, if available
- `--author-mail` may suggest using `user.email` from `git config`, if available
- `--init-git` may ask whether to initialise a Git repository

Use the `-m, --prompt-mode` option to control whether these suggestions are shown or automatically handled:

| Option                   | `yes` | `auto` | `no`  |
|--------------------------|:-----:|:------:|:-----:|
| `--github-repositoryname`|  ✅   |   ✅    |  ❌   |
| `--author-name`          |  ✅   |   ✅    |  ❌   |
| `--author-mail`          |  ✅   |   ✅    |  ❌   |
| `--init-git`             |  ✅   |   ❌    |  ❌   |

- `yes`: Automatically accept all suggestions
- `no`: Skip all prompts and use defaults or leave unset
- `auto`: Accept safe suggestions only (e.g., use Git info, but skip Git initialisation)
- `ask` *(default)*: Prompt interactively for each case, and ask again before creating the project structure



### GitHub Downloader

Download a specific folder (or the entire contents) from a public GitHub repository using the GitHub API.

#### Python Version

Located in: [`github_download.py`](./src/github_download.py)

**Features:**

* Downloads a subfolder or the full repository
* Supports branch selection
* Recursive or non-recursive download

**Usage:**

```bash
python github_download.py ExampleOwner example_repo \
  --branch main \
  --subfolder src/utils \
  --destination ./downloaded_code
```

To download the entire repository contents (default branch `main`):

```bash
python github_download.py ExampleOwner example_repo
```

#### Bash Version

Located in: [`github_download.sh`](./src/github_download.sh)

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


## Requirements

* Python 3.13+ (may work with lower versions, but not tested)
* `requests` library (for Python GitHub downloader and license selection)
* `git` (for sparse-checkout Bash script)

To install Python dependencies (if needed):

```bash
pip install requests
```
