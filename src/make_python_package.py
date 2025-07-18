import argparse
import warnings
from dataclasses import dataclass, fields
from pathlib import Path

# Try to import requests. It is okay if this fails since most parts will work anyway.
try:
    import requests

    REQUESTS_IMPORT_ERROR = False
except Exception as err:
    # print(dir(err))
    requests = None
    REQUESTS_IMPORT_ERROR = err


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


@dataclass(kw_only=True)
class ProjectSettings:

    name: str = "PACKAGENAME"
    description: str = "PACKAGEDESCRIPTION"
    license_id: str = None
    author_name: str = "AUTHORNAME"
    author_mail: str = "AUTHORMAIL@SOMETHING.com"
    github_username: str = "USERNAME"
    github_repositoryname: str = "REPOSITORYNAME"
    changelog: str = None
    documentation: str = None
    download: str = None
    funding: str = None
    homepage: str = None
    issues: str = None
    releasenotes: str = None
    source: str = None

    def __getattribute__(self, name):
        """Return value of attribute 'name', but take care of default values."""
        value = super().__getattribute__(name)  # getattr(self, name)
        if value is None:
            match name:
                case "changelog" | "releasenotes":
                    return f"{self.github}/commits"
                case "documentation":
                    return f"{self.github}/README.md"
                case "download" | "homepage":
                    return self.github
                case "issues":
                    return f"{self.github}/issues"
                case "source":
                    return f"{self.github}.git"
                case "funding" | _:
                    return value
        else:
            return value

    @property
    def github(self) -> str:
        """Return the link to the github repository."""
        return f"https://github.com/{self.github_username}/{self.github_repositoryname}"

    @property
    def github_owner(self) -> str:
        """Return the link to the owner of the github repository."""
        return f"https://github.com/{self.github_username}"

    @staticmethod
    def get_url_fields():
        """Return a tuple of field names that represent a project url."""
        return (
            "changelog",
            "documentation",
            "download",
            "funding",
            "homepage",
            "issues",
            "releasenotes",
            "source",
        )

    @property
    def urls(self) -> dict[str]:
        """Return '{name: url}' dictionary for project urls."""
        names = self.get_url_fields()
        return {
            name: _url for name in names if (_url := getattr(self, name)) is not None
        }

    @classmethod
    def add_to_argparser(
        cls, parser: argparse.ArgumentParser, ignore: tuple[str] | list[str] = None
    ):
        """Add all fields that are not in 'ignore' to an argument parser."""
        if ignore is None:
            ignore = []
        for field in fields(cls):
            if field.name in ignore:
                continue
            argument = f"--{field.name.replace("_", "-")}"
            help_str = f"{field.name.replace("_", " ")}"
            if field.name in cls.get_url_fields():
                help_str = f"url to {help_str}  (default: composed from other settings)"
            else:
                help_str = f"{help_str} (default: {field.default})"
            options = {
                "type": field.type,
                "help": help_str,
                "default": field.default,
            }
            parser.add_argument(argument, **options)

    @classmethod
    def from_argparser(cls, args: argparse.Namespace):
        """Return instance of this class with options set to the values of 'args'."""
        args_dict = vars(args)
        names = [field.name for field in fields(cls)]
        options = {name: value for name, value in args_dict.items() if name in names}

        return cls(**options)


class FileContent(dict):

    def __init__(self, project_settings: ProjectSettings, **kwargs):
        self.project_settings = project_settings
        kwargs.setdefault(".gitignore", self.get_gitignore())
        kwargs.setdefault("LICENSE", self.get_license())
        try:
            self.license_name = kwargs["LICENSE"].splitlines()[0]
        except Exception as err:
            self.license_name = "LICENSENAME"
        kwargs.setdefault("pyproject.toml", self.get_pyproject_toml())
        kwargs.setdefault("README.md", self.get_readme())
        super().__init__(**kwargs)

    @staticmethod
    def get_gitignore():
        """Return default content for '.gitignore'."""
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

    def get_license(self):
        """Return license text according to 'project_settings.license_id'."""
        if self.project_settings.license_id is None:
            return ""
        try:
            return get_license(self.project_settings.license_id)
        except Exception as err:
            return ""

    def get_pyproject_toml(self):
        """Return default value for 'pyproject.toml' according to 'project_settings'."""
        project = self.project_settings
        author_str = f"""name="{project.author_name}", email="{project.author_mail}" """
        url_str = "".join(
            [
                f"""{name.capitalize()} = "{_url}"\n"""
                for name, _url in project.urls.items()
            ]
        )
        return (
            f"""[project]\nname = "{project.name}"\nversion = "0.1"\n"""
            f"""authors = [{{ {author_str} }},]\n"""
            f"""description = "{project.description}"\nreadme = "README.md"\n"""
            """license = { file = "LICENSE" }\nrequires-python = ">=3.XX"\n"""
            """dependencies = []\n"""
            """classifiers=[\n    "Programming Language :: Python :: 3",\n    """
            """"Operating System :: OS Independent",\n]"""
            f"""\n\n[project.urls]\n{url_str}"""
        )

    def get_readme(self):
        """Return default value for 'README' according to 'project_settings'."""
        project = self.project_settings
        return (
            f"# {project.name}\n\n**{project.description}**\n\n"
            "Developed and maintained by "
            f"[{project.author_name}]({project.github_owner}).\n\n"
            f"* **Source code:** {project.source}\n"
            f"* **Report bugs:** {project.issues}\n\n"
            f"## License\n\nDistributed under the [{self.license_name}](./LICENSE).\n\n"
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
    destination_path: str | Path,
    name: str,
    ask: bool = True,
    project_settings: ProjectSettings = None,
):
    """Get the wanted package structure and create it."""
    if project_settings is None:
        project_settings = ProjectSettings()
    parent_dir = Path(destination_path)
    structure = Structure.package(name)
    file_content = FileContent(project_settings)
    if ask:
        _input = input(f"Create package '{name}' at '{parent_dir.absolute()}'? (Y/n): ")
        if _input == "Y":
            create_components(parent_dir, structure, file_content=file_content)
        else:
            print(f"Creation aborted by user input '{_input}'...")
    else:
        create_components(parent_dir, structure, file_content=file_content)


def check_requests(text: str):
    """Raise warning and REQUESTS_IMPORT_ERROR if 'requests' is not available."""
    if REQUESTS_IMPORT_ERROR:
        warning_text = (
            f"{text} requires unavailable module 'requests'! "
            f"({type(REQUESTS_IMPORT_ERROR).__qualname__}: {REQUESTS_IMPORT_ERROR})"
        )
        warnings.warn(warning_text, UserWarning, stacklevel=3)
        REQUESTS_IMPORT_ERROR.add_note(warning_text)
        raise REQUESTS_IMPORT_ERROR


def get_available_licenses(api_url: str = None):
    """
    Get available license form the 'choosealicense.com' repository.

    You may specify a different GitHub repository by changing the 'api_url'.
    """
    check_requests("Showing available licenses")
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
    check_requests("Downloading a license")
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
        "-r",
        "--autoname-repository",
        action="store_true",
        help="ignore the value of 'github_repositoryname' and set it to 'name'",
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
    ProjectSettings.add_to_argparser(parser, ignore=("license_id", "name"))

    return parser.parse_args()


if __name__ == "__main__":
    args = get_sys_args()
    if args.list_licenses:
        available_licenses = get_available_licenses()
        licenses_str = ", ".join(available_licenses.keys())
        print(f"Available licenses are:\n{licenses_str}")
    else:
        project_settings = ProjectSettings.from_argparser(args)
        project_settings.license_id = args.license
        if args.autoname_repository:
            project_settings.github_repositoryname = args.name
        create_package_structure(
            args.destination, args.name, ask=True, project_settings=project_settings
        )
