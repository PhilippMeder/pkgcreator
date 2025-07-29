"""Tests for the CLI creation mode called by 'pkgcreator create'."""

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

import pytest

from pkgcreator.cli import GIT_AVAILABLE, creation_mode


REQUESTS_AVAILABLE = False if find_spec("requests") is None else True


@dataclass(kw_only=True)
class MockCLIArgs:
    """Class to mock CLI arguments."""

    destination: Path
    name: str
    make_script: bool = True
    prompt_mode: str = "no"
    license_id: str = "mit"
    init_git: bool = False
    init_venv: bool = False


def get_mock_args(tmp_path: Path, **kwargs) -> MockCLIArgs:
    """Return example mocked CLI arguments."""
    return MockCLIArgs(destination=tmp_path, name="test_package", **kwargs)


def test_creation_fails_if_path_exists(tmp_path: Path) -> None:
    """Test whether the creation raises an error if the project path already exists."""
    args = get_mock_args(tmp_path)

    # Simulate existing package
    (args.destination / args.name).mkdir()

    # Check File_ExistsError
    with pytest.raises(FileExistsError):
        creation_mode(args)


def test_basic_package_structure(tmp_path: Path) -> None:
    """Test the correct creation of the package structure."""
    args = get_mock_args(tmp_path)
    creation_mode(args)

    pkg_path = tmp_path / args.name
    assert pkg_path.is_dir()

    non_empty_files = [pkg_path / "pyproject.toml", pkg_path / "README.md"]
    for file in non_empty_files:
        assert file.is_file()
        assert file.stat().st_size > 0

    assert (pkg_path / "LICENSE").is_file()


@pytest.mark.skipif(not GIT_AVAILABLE, reason="Git not available")
def test_git_initialised(tmp_path: Path) -> None:
    """Test whether the creation mode correctly initalises a Git repository."""
    args = get_mock_args(tmp_path, init_git=True)

    creation_mode(args)

    pkg_path = tmp_path / args.name
    assert (pkg_path / ".git").is_dir()


@pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests not installed")
def test_license_file_created(tmp_path: Path) -> None:
    """Test whether the creation mode correctly creates the LICENSE file with text."""
    args = get_mock_args(tmp_path)
    creation_mode(args)

    license_file = tmp_path / args.name / "LICENSE"
    assert license_file.exists()
    assert license_file.stat().st_size > 0
