import argparse
import requests
from pathlib import Path


class Structure:

    @staticmethod
    def module(name: str):
        """Return a dictionary how the module structure should look like."""
        return {name: {"FILES": ["__init__.py"]}}

    @staticmethod
    def package(name: str):
        """Return a dictionary how the package structure should look like."""
        return {
            name: {
                "src": {name: {"FILES": ["__init__.py"]}},
                "FILES": ["LICENSE", "README.md", "pyproject.toml", ".gitignore"],
            }
        }


class FileContent(dict):

    def __init__(self, license: str = None, **kwargs):
        kwargs.setdefault(".gitignore", self.get_gitignore())
        kwargs.setdefault("LICENSE", self.get_license(license))
        kwargs.setdefault("pyproject.toml", self.get_pyproject_toml())
        kwargs.setdefault("README.md", self.get_readme())
        super().__init__(**kwargs)

    @staticmethod
    def get_gitignore():
        return (
            "__pycache__\n"
            "#.gitignore\n"
            ".env\n"
            ".venv\n"
            ".vscode\n"
            ".draft*\n"
            ".playground*\n"
            "*.egg-info"
        )

    @staticmethod
    def get_license(license: str = None):
        if license is None:
            return ""
        try:
            return get_license(license)
        except Exception as err:
            return ""

    @staticmethod
    def get_pyproject_toml():
        return (
            """[project]\nname = "PACKAGENAME"\nversion = "0.1"\n"""
            """authors = [{ name="AUTHORNAME", email="AUTHORMAIL@SOMETHING.com" },]\n"""
            """description = "PACKAGEDESCRIPTION"\nreadme = "README.md"\n"""
            """license = { file = "LICENSE" }\nrequires-python = ">=3.XX"\n"""
            """dependencies = []\n"""
            """classifiers=[\n    "Programming Language :: Python :: 3",\n    """
            """"Operating System :: OS Independent",\n]"""
        )

    @staticmethod
    def get_readme():
        return (
            "# PACKAGENAME\n\n**PACKAGEDESCRIPTION**\n\n"
            "Developed and maintained by [AUTHORNAME](https://github.com/USERNAME).\n\n"
            "* **Source code:** https://github.com/USERNAME/PACKAGENAME\n"
            "* **Report bugs:** https://github.com/USERNAME/PACKAGENAME/issues\n\n"
            "## License\n\nDistributed under the [LICENSENAME](./LICENSE).\n\n"
            "## Features\n\n1. [FEATURE 1](#feature-1)\n2. [FEATURE 2](#feature-2)\n\n"
            "### FEATURE 1\n\n### FEATURE 2\n\n"
            "## Requirements"
        )


def create_components(path: Path, structure: dict, file_content: dict = None):
    """Create directory/file structure recursively."""
    for key, substructure in structure.items():
        if key == "FILES":
            # Create files and, if available, set the content
            for filename in substructure:
                file = path.joinpath(filename)
                file.touch(exist_ok=False)
                if file_content and filename in file_content:
                    with open(file, "w") as file_obj:
                        file_obj.write(file_content[filename])
        else:
            # Create subdirectory
            dir_path = path.joinpath(key)
            dir_path.mkdir()
            create_components(dir_path, substructure, file_content=file_content)


def create_package_structure(
    destination_path: str | Path, name: str, ask: bool = True, license: str = None
):
    """Get the wanted package structure and create it."""
    parent_dir = Path(destination_path)
    structure = Structure.package(name)
    file_content = FileContent(license=license)
    if ask:
        user_input = input(f"Create package '{name}' at '{parent_dir}'? (Y/n): ")
        if user_input == "Y":
            create_components(parent_dir, structure, file_content=file_content)
        else:
            print(f"Creation aborted by user input '{user_input}'...")
    else:
        create_components(parent_dir, structure, file_content=file_content)


def get_available_licenses(api_url: str = None):
    """
    Get available license form the 'choosealicense.com' repository.

    You may specify a different GitHub repository by changing the 'api_url'.
    """
    if api_url is None:
        api_url = (
            "https://api.github.com/repos/github/choosealicense.com/contents/_licenses"
        )

    response = requests.get(api_url)
    response.raise_for_status()
    contents = response.json()

    return {
        str(Path(item["name"]).with_suffix("")): item["download_url"]
        for item in contents
        if item["type"] == "file"
    }


def get_license(name: str, licenses: dict = None):
    """Download the chosen licenses."""
    if licenses is None:
        licenses = get_available_licenses()
    download_url = licenses[name]
    response = requests.get(download_url)
    response.raise_for_status()

    text = response.text
    try:
        return text.split("\n---\n")[1].lstrip("\n")
    except IndexError:
        return text


def get_sys_args():
    parser = argparse.ArgumentParser(
        description="Create a new Python package structure with optional license."
    )

    parser.add_argument("name", help="name of the Python package to create")
    parser.add_argument(
        "-d",
        "--destination",
        default=".",
        help="destination directory for the package structure",
    )
    parser.add_argument(
        "-l",
        "--license",
        default=None,
        help="optional license to include in the package",
    )
    parser.add_argument(
        "--list-licenses",
        action="store_true",
        help="list all available licenses and exit",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_sys_args()
    if args.list_licenses:
        licenses_str = ", ".join(get_available_licenses().keys())
        print(f"Available licenses are:\n{licenses_str}")
    else:
        create_package_structure(
            args.destination, args.name, ask=True, license=args.license
        )
