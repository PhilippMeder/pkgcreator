import argparse
from dataclasses import dataclass, fields, field, MISSING
from pathlib import Path

from pkgcreator import GithubRepository


class PackageExistsError(FileExistsError):
    """Exception class when package directory already exists."""


def default_classifiers() -> list[str]:
    """Return list of classifiers used as defaults."""
    return [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]


@dataclass(kw_only=True)
class ProjectSettings:

    make_script: bool = False
    dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    classifiers: list[str] = field(default_factory=default_classifiers)
    license_id: str = None
    name: str = "PACKAGENAME"
    description: str = "PACKAGEDESCRIPTION"
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

    def __post_init__(self):
        self.github_repository = GithubRepository(
            self.github_username, self.github_repositoryname
        )

    def __getattribute__(self, name):
        """Return value of attribute 'name', but take care of default values."""
        value = super().__getattribute__(name)
        if value is None and name in self.get_url_fields():
            return self.github_repository.get_url(name, branch=False)
        else:
            return value

    def is_default(self, name: str) -> bool:
        """Check if the value of field 'name' equals to the default value."""
        for _field in fields(self):
            if _field.name != name:
                continue
            return getattr(self, name) == _field.default
        else:
            raise AttributeError(f"Field '{name}' unkown!")

    @property
    def github(self) -> str:
        """Return the link to the github repository."""
        return self.github_repository.get_url(branch=False)

    @property
    def github_owner(self) -> str:
        """Return the link to the owner of the github repository."""
        return self.github_repository.get_url("owner", branch=False)

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

    @staticmethod
    def get_advanced_fields():
        """Return a tuple of field names that represent an advanced setting."""
        return (
            "classifiers",
            "dependencies",
            "optional_dependencies",
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
            _field.name: value
            for _field in fields(self)
            if (value := getattr(self, _field.name))
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
        # Setup sections
        settings = parser.add_argument_group(
            title="project settings",
            description="information used to create 'README' and 'pyproject.toml'",
        )
        urls = parser.add_argument_group(
            title="project urls",
            description=(
                "urls to project pages used for 'pyproject.toml' "
                "(default: create from github settings)"
            ),
        )
        url_fields = cls.get_url_fields()
        advanced = parser.add_argument_group(
            title="advanced project settings",
            description=(
                "further information passed to 'pyproject.toml' "
                "(probably evolve during package development)"
            ),
        )
        advanced_fields = cls.get_advanced_fields()

        # Add arguments to the correct sections
        for _field in fields(cls):
            # Ignoring or special treatment
            if _field.name in ignore:
                continue
            elif _field.name == "license_id":
                settings.add_argument(
                    "-l",
                    "--license",
                    dest="license_id",
                    metavar="LICENSE_ID",
                    help="license to include in the package (default: %(default)s)",
                    default=None,
                )
                continue
            # Default treatment according to settings above
            argument = f'--{_field.name.replace("_", "-")}'
            help_str = f'{_field.name.replace("_", " ")}'
            options = {"type": _field.type, "default": cls.get_field_default(_field)}
            if _field.name in url_fields:
                options["help"] = f"url to {help_str}"
                options["metavar"] = "URL"
                _parser = urls
            elif _field.name in advanced_fields:
                options["metavar"] = "STR"
                options["nargs"] = "+"
                options["type"] = str  # argparse needs the type of the list content!
                _parser = advanced
            else:
                options["help"] = f'{help_str} (default: {options["default"]})'
                _parser = settings

            _parser.add_argument(argument, **options)

    @classmethod
    def from_argparser(cls, args: argparse.Namespace):
        """Return instance of this class with options set to the values of 'args'."""
        args_dict = vars(args)
        names = [_field.name for _field in fields(cls)]
        options = {name: value for name, value in args_dict.items() if name in names}

        return cls(**options)

    @classmethod
    def get_field_default(cls, _field, raise_err: bool = True):
        """Return the default value of a field while taking care of default_factory."""
        if _field.default is not MISSING:
            return _field.default
        elif _field.default_factory is not MISSING:
            return _field.default_factory()
        else:
            if raise_err:
                raise ValueError(f"Default for field '{_field.name}' is missing!")
            return None


class PythonPackage:

    def __init__(
        self,
        destination: str | Path,
        name: str,
        dir_name: str = None,
        add_main: bool = False,
    ):
        self._parent_dir = Path(destination)
        self._dir_name = dir_name or name
        self._name = name
        self.add_main = add_main
        self._set_project_path()

    @property
    def parent_dir(self) -> Path:
        return self._parent_dir

    @parent_dir.setter
    def parent_dir(self, new_value: str | Path):
        self._parent_dir = Path(new_value)

    @property
    def dir_name(self) -> str:
        return self._dir_name

    @dir_name.setter
    def dir_name(self, new_value: str):
        self._dir_name = new_value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = new_value

    @property
    def project_path(self) -> Path:
        return self._project_path

    @property
    def structure(self) -> dict:
        module_files = ["__init__.py"]
        if self.add_main:
            module_files.append("__main__.py")
        return {
            self.dir_name: {
                "src": {self.name: {"FILES": module_files}},
                "FILES": ["LICENSE", "README.md", "pyproject.toml", ".gitignore"],
            }
        }

    def create(self, file_content: dict = None):
        if self.project_path.exists():
            msg = f"The project path '{self.project_path}' already exists!"
            raise PackageExistsError(msg)
        create_dir_structure(self.parent_dir, self.structure, file_content=file_content)

    def get_all_filenames(self):
        return get_all_filenames_from_structure(self.structure)

    def _set_project_path(self):
        if len(keys := list(self.structure.keys())) == 1:
            self._project_path = self.parent_dir.joinpath(keys[0])
        else:
            self._project_path = self.parent_dir


def create_dir_structure(path: Path, structure: dict, file_content: dict = None):
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
            create_dir_structure(dir_path, substructure, file_content=file_content)


def get_all_filenames_from_structure(structure: dict) -> list[str]:
    files = []
    for key, substructure in structure.items():
        if key == "FILES":
            files += substructure
        else:
            files += get_all_filenames_from_structure(substructure)

    return files
