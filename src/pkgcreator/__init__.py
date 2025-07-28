"""
Top-level package interface for `pkgcreator`.

This module exposes the main components of the package creator tool,
making them directly accessible when importing `pkgcreator`.

Available components include:
- Git repository management (`GitRepository`, `GithubRepository`)
- Virtual environment handling (`VirtualEnvironment`)
- Python package building (`PythonPackage`, `ProjectSettings`)
- License management (`get_available_licenses`, `get_license`)
- Git utilities and exceptions

Importing from `pkgcreator` gives access to the core functionality for
programmatic usage and integration.
"""

from pkgcreator.ghutils import GithubRepository
from pkgcreator.builder import PackageExistsError, ProjectSettings, PythonPackage
from pkgcreator.file_contents import FileContent, get_available_licenses, get_license
from pkgcreator.gitrepo import (
    GIT_AVAILABLE,
    GitNotAvailableError,
    GitRepository,
    GitRepositoryExistsError,
    GitRepositoryNotFoundError,
    get_git_config_value,
    run_git_command,
)
from pkgcreator.venv_manager import VirtualEnvironment

__all__ = [
    "GitNotAvailableError",
    "GitRepositoryExistsError",
    "GitRepositoryNotFoundError",
    "PackageExistsError",
    "FileContent",
    "GitRepository",
    "GithubRepository",
    "ProjectSettings",
    "PythonPackage",
    "VirtualEnvironment",
    "GIT_AVAILABLE",
    "get_available_licenses",
    "get_license",
    "get_git_config_value",
    "run_git_command",
]
