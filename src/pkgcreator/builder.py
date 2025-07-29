"""
Module for managing Python package settings and generating the directory structure.

Includes tools to:
- Define and parse project metadata.
- Interface with GitHub-based URLs.
- Generate a file and folder structure for Python packages.
"""

import argparse
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path

from pkgcreator import GithubRepository


class PackageExistsError(FileExistsError):
    """Raised when the package directory already exists and creation is attempted."""


def default_classifiers() -> list[str]:
    """
    Return a list of default PyPI classifiers.

    Returns
    -------
    list of str
        Default classifiers used in the package metadata.
    """
    return [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]


@dataclass(kw_only=True)
class ProjectSettings:
    """
    Container for project metadata and configuration used to create a Python package.

    This includes fields for package name, author, URLs, dependencies, classifiers, and
    GitHub repository information.

    Attributes
    ----------
    make_script : bool
        Whether to create an entry-point script.
    dependencies : list of str
        Required dependencies for the package.
    optional_dependencies : list of str
        Optional dependencies for the package.
    classifiers : list of str
        List of PyPI classifiers.
    license_id : str or None
        License identifier.
    name : str
        Package name.
    description : str
        Short package description.
    author_name : str
        Author's name.
    author_mail : str
        Author's email address.
    github_username : str
        GitHub username.
    github_repositoryname : str
        GitHub repository name.
    changelog, documentation, download, funding, homepage : str or None
        Optional URLs related to the project.
    issues, releasenotes, source : str or None
        Optional URLs related to the project.
    """

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

    def __post_init__(self) -> None:
        """Create the GithubRepository object from the parameters."""
        self.github_repository = GithubRepository(
            self.github_username, self.github_repositoryname
        )

    def __getattribute__(self, name: str):
        """
        Get attribute value and automatically generate URL if unset.

        Parameters
        ----------
        name : str
            Attribute name.

        Returns
        -------
        any
            Attribute value or auto-generated URL.
        """
        value = super().__getattribute__(name)
        if value is None and name in self.get_url_fields():
            return self.github_repository.get_url(name, branch=False)
        else:
            return value

    def is_default(self, name: str) -> bool:
        """
        Check whether a field is set to its default value.

        Parameters
        ----------
        name : str
            Field name.

        Returns
        -------
        bool
            True if field has default value, False otherwise.

        Raises
        ------
        AttributeError
            If the field name is invalid.
        """
        for _field in fields(self):
            if _field.name != name:
                continue
            return getattr(self, name) == _field.default
        else:
            msg = f"Field '{name}' unkown!"
            raise AttributeError(msg)

    @property
    def github(self) -> str:
        """
        Get the URL to the GitHub repository.

        Returns
        -------
        str
            GitHub repository URL.
        """
        return self.github_repository.get_url(branch=False)

    @property
    def github_owner(self) -> str:
        """
        Get the URL to the GitHub account (repository owner).

        Returns
        -------
        str
            GitHub owner URL.
        """
        return self.github_repository.get_url("owner", branch=False)

    @staticmethod
    def get_url_fields() -> tuple[str]:
        """
        Return the names of fields that represent URLs.

        Returns
        -------
        tuple of str
            Field names for URL fields.
        """
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
    def get_advanced_fields() -> tuple[str]:
        """
        Return the names of fields that are considered advanced settings.

        Returns
        -------
        tuple of str
            Field names for advanced settings.
        """
        return (
            "classifiers",
            "dependencies",
            "optional_dependencies",
        )

    @property
    def urls(self) -> dict[str]:
        """
        Get dictionary of URL-related fields and their values.

        Returns
        -------
        dict of str
            Mapping of field names to URL values.
        """
        names = self.get_url_fields()
        return {
            name.capitalize(): _url
            for name in names
            if (_url := getattr(self, name)) is not None
        }

    @property
    def nice_str(self) -> str:
        """
        Return a formatted string representation of all fields with their values.

        Returns
        -------
        str
            Multiline string displaying all non-empty fields.
        """
        values = {
            _field.name: value
            for _field in fields(self)
            if (value := getattr(self, _field.name))
        }
        n_max = max(map(len, values.keys()))

        return "\n".join([f"{name:<{n_max}} {value}" for name, value in values.items()])

    @classmethod
    def add_to_argparser(
        cls,
        parser: argparse.ArgumentParser,
        ignore: tuple[str] | list[str] | None = None,
    ) -> None:
        """
        Add project fields as arguments to an argparse.ArgumentParser.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            Argument parser to modify.
        ignore : list or tuple of str, optional
            Field names to ignore.
        """
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
        """
        Create a ProjectSettings instance from parsed arguments.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments.

        Returns
        -------
        ProjectSettings
            Initialized project settings object.
        """
        args_dict = vars(args)
        names = [_field.name for _field in fields(cls)]
        options = {name: value for name, value in args_dict.items() if name in names}

        return cls(**options)

    @classmethod
    def get_field_default(cls, _field, raise_err: bool = True):
        """
        Get the default value of a dataclass field (takes care of default_factory).

        Parameters
        ----------
        _field : dataclasses.Field
            Dataclass field to evaluate.
        raise_err : bool, optional
            Whether to raise an error if no default is defined.

        Returns
        -------
        any
            Default value of the field.

        Raises
        ------
        ValueError
            If no default or factory is found and raise_err is True.
        """
        if _field.default is not MISSING:
            return _field.default
        elif _field.default_factory is not MISSING:
            return _field.default_factory()
        else:
            if raise_err:
                raise ValueError(f"Default for field '{_field.name}' is missing!")
            return None


class PythonPackage:
    """
    Tool to create a Python package directory structure.

    Parameters
    ----------
    destination : str or Path
        Base directory where the package should be created.
    name : str
        Name of the Python module/package.
    dir_name : str, optional
        Name of the directory for the new package (defaults to `name`).
    add_main : bool, optional
        Whether to include a `__main__.py` file (default is False).

    Attributes
    ----------
    parent_dir : Path
        Base directory where the package will be created.
    dir_name : str
        Name of the directory for the new package.
    name : str
        Name of the package (module name).
    add_main : bool
        Whether to include a `__main__.py` file.
    """

    def __init__(
        self,
        destination: str | Path,
        name: str,
        dir_name: str | None = None,
        add_main: bool = False,
    ) -> None:
        self._parent_dir = Path(destination)
        self._dir_name = dir_name or name
        self._name = name
        self.add_main = add_main
        self._set_project_path()

    @property
    def parent_dir(self) -> Path:
        """Get the base directory where the package is located."""
        return self._parent_dir

    @parent_dir.setter
    def parent_dir(self, new_value: str | Path) -> None:
        self._parent_dir = Path(new_value)

    @property
    def dir_name(self) -> str:
        """Get the name of the directory for the package."""
        return self._dir_name

    @dir_name.setter
    def dir_name(self, new_value: str) -> None:
        self._dir_name = new_value

    @property
    def name(self) -> str:
        """Get the name of the package."""
        return self._name

    @name.setter
    def name(self, new_value: str) -> None:
        self._name = new_value

    @property
    def project_path(self) -> Path:
        """Get the full project path."""
        return self._project_path

    @property
    def structure(self) -> dict:
        """Get the structure definition for the package."""
        module_files = ["__init__.py"]
        if self.add_main:
            module_files.append("__main__.py")
        return {
            self.dir_name: {
                "src": {self.name: {"FILES": module_files}},
                "FILES": ["LICENSE", "README.md", "pyproject.toml", ".gitignore"],
            }
        }

    def create(self, file_content: dict | None = None) -> None:
        """
        Create the folder and file structure for the package.

        Parameters
        ----------
        file_content : dict, optional
            Optional mapping of filenames to file content.

        Raises
        ------
        PackageExistsError
            If the target project directory already exists.
        """
        if self.project_path.exists():
            msg = f"The project path '{self.project_path}' already exists!"
            raise PackageExistsError(msg)
        create_dir_structure(self.parent_dir, self.structure, file_content=file_content)

    def get_all_filenames(self) -> list[str]:
        """
        Get a flat list of all filenames defined in the structure.

        Returns
        -------
        list of str
            List of all files in the structure.
        """
        return get_all_filenames_from_structure(self.structure)

    def _set_project_path(self) -> None:
        """Determine and set the full project path based on the directory structure."""
        if len(keys := list(self.structure.keys())) == 1:
            self._project_path = self.parent_dir.joinpath(keys[0])
        else:
            self._project_path = self.parent_dir


def create_dir_structure(
    path: Path, structure: dict, file_content: dict | None = None
) -> None:
    """
    Recursively create directory and file structure.

    Parameters
    ----------
    path : Path
        Root path where the structure should be created.
    structure : dict
        Nested dictionary describing folders and files.
    file_content : dict, optional
        Optional mapping of filenames to file content.
    """
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
    """
    Recursively extract all filenames from a folder structure definition.

    Parameters
    ----------
    structure : dict
        Nested dictionary describing files and folders.

    Returns
    -------
    list of str
        All file names in the structure.
    """
    files = []
    for key, substructure in structure.items():
        if key == "FILES":
            files += substructure
        else:
            files += get_all_filenames_from_structure(substructure)

    return files
