import argparse
import subprocess
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

    def is_default(self, name: str) -> bool:
        """Check if the value of field 'name' equals to the default value."""
        for field in fields(self):
            if field.name != name:
                continue
            return getattr(self, name) == field.default
        else:
            raise AttributeError(f"Field '{name}' unkown!")

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

    @property
    def nice_str(self) -> str:
        """Return a table-like string representation of the fields."""
        values = {
            field.name: value
            for field in fields(self)
            if (value := getattr(self, field.name))
        }
        n_max = max(map(len, values.keys()))

        return "\n".join([f"{name:<{n_max}} {value}" for name, value in values.items()])

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
            warning_text = (
                f"Could not download license '{self.project_settings.license_id}'! "
                f"({type(err).__qualname__}: {err})"
            )
            warnings.warn(warning_text, UserWarning, stacklevel=2)
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
    project_settings: ProjectSettings = None,
) -> Path:
    """Get the wanted package structure and create it."""
    if project_settings is None:
        project_settings = ProjectSettings()
    parent_dir = Path(destination_path)
    structure = Structure.package(name)
    file_content = FileContent(project_settings)
    create_components(parent_dir, structure, file_content=file_content)

    if len(keys := list(structure.keys())) == 1:
        return parent_dir.joinpath(keys[0])
    else:
        return parent_dir


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


def get_git_config_value(key: str) -> str | None:
    """Return the value for 'key' from the git config."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def run_git_command(*args, suppress_output: bool = False, **kwargs):
    """Run a git command with 'args' ('kwargs' are passed to 'subprocess.run()')."""
    kwargs.setdefault("check", True)
    if suppress_output:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    subprocess.run(["git", *args], **kwargs)


def create_git_repository(path: Path):
    """Create git repository and stage and commit all files."""
    try:
        # Return if repository already exists
        run_git_command("status", cwd=path, suppress_output=True)
        warnings.warn(
            f"It seems like there already is a repository in {path}!",
            UserWarning,
            stacklevel=2,
        )
        return
    except subprocess.CalledProcessError:
        pass

    run_git_command("init", "-b", "main", cwd=path)
    run_git_command("add", "-A", cwd=path)
    run_git_command("commit", "-m Created repository", cwd=path)


def get_prompt_bool(message: str, mode: str, auto_decision: bool = False) -> bool:
    """Return True/False for a prompt according to mode or user input."""
    match mode:
        case "yes":
            return True
        case "no":
            return False
        case "auto":
            return auto_decision
        case "ask" | _:
            user_input = input(f"{message} (Y/n): ")
            return user_input == "Y"


def patch_default_settings(project_settings: ProjectSettings, args: argparse.Namespace):
    """Ask or decide how a few settings should behave when not set explicitly."""
    if project_settings.is_default("github_repositoryname"):
        if get_prompt_bool(
            f"'--github-repositoryname' was not set. Set to {args.name}?",
            args.prompt_mode,
            auto_decision=True,
        ):
            project_settings.github_repositoryname = args.name
            print(f"Set '--github-repositoryname' to {args.name}")
    if project_settings.is_default("author_name"):
        if git_user := get_git_config_value("user.name"):
            if get_prompt_bool(
                f"'--author-name' was not set. Set to {git_user} (from 'git config')?",
                args.prompt_mode,
                auto_decision=True,
            ):
                project_settings.author_name = git_user
                print(f"Set '--author-name' to {git_user}")
    if project_settings.is_default("author_mail"):
        if git_mail := get_git_config_value("user.email"):
            if get_prompt_bool(
                f"'--author-mail' was not set. Set to {git_mail} (from 'git config')?",
                args.prompt_mode,
                auto_decision=True,
            ):
                project_settings.author_mail = git_mail
                print(f"Set '--author-mail' to {git_mail}")


def creation_mode(args: argparse.Namespace):
    """Run the creation process."""
    # Setup the project settings
    project_settings = ProjectSettings.from_argparser(args)
    project_settings.license_id = args.license
    destination_path = Path(args.destination)

    if (guessed_package_path := destination_path / args.name).exists():
        err_msg = f"'{guessed_package_path}' already exists!"
        raise FileExistsError(err_msg)

    # Ask for some settings if not specified
    patch_default_settings(project_settings, args)

    # Check and return if creation is aborted, but ignore the "no" mode this time!
    msg = (
        f"Settings:\n{project_settings.nice_str}\n"
        f"Create package '{args.name}' at '{destination_path.absolute()}'?"
    )
    if (
        not get_prompt_bool(msg, args.prompt_mode, auto_decision=True)
        and args.prompt_mode != "no"
    ):
        print(f"Creation aborted")
        return

    # Create the package structure
    project_path = create_package_structure(
        destination_path, args.name, project_settings=project_settings
    )
    print(f"Created project '{args.name}' at '{project_path}'")

    # Create git repository if wanted
    git_msg = "Initalise Git repository (requires 'Git')?"
    if args.init_git or get_prompt_bool(git_msg, args.prompt_mode, auto_decision=False):
        create_git_repository(project_path)


def get_sys_args():
    """Get the settings."""
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
        "-m",
        "--prompt-mode",
        choices=["ask", "yes", "no", "auto"],
        default="ask",
        help=(
            "control prompts for user interaction: ask (default), yes (always accept), "
            "no (always decline), auto (decide automatically)"
        ),
    )
    parser.add_argument(
        "-i",
        "--init-git",
        action="store_true",
        help="initialise Git repository and commit created files (requires 'Git')",
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
        creation_mode(args)
