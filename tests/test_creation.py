from dataclasses import dataclass
from pathlib import Path

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from pkgcreator.cli import creation_mode, GIT_AVAILABLE


@dataclass(kw_only=True)
class MockCLIArgs:

    make_script: bool
    destination: Path
    name: str
    prompt_mode: str
    license_id: str

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError as err:
            return name


def get_mock_args(tmp_path: Path, make_git_venv: bool = False):
    return MockCLIArgs(
        make_script=True,
        destination=tmp_path,
        name="test_package",
        prompt_mode="yes" if make_git_venv else "auto",
        license_id="mit",
    )


def test_package_creation(tmp_path: Path):
    args = get_mock_args(tmp_path, True)

    creation_mode(args)

    pkg_path = args.destination / args.name
    src_path = pkg_path / "src" / args.name

    pkg_files = ["README.md", "LICENSE", "pyproject.toml", ".gitignore"]
    module_files = ["__init__.py"]
    if args.make_script:
        module_files.append("__main__.py")

    # Test if package directory and files exist
    assert pkg_path.is_dir()
    for file in pkg_files:
        assert (pkg_path / file).is_file()

    # Test if source directory and files exist
    assert src_path.is_dir()
    for file in module_files:
        assert (src_path / file).is_file()

    # Test if LICENSE download worked
    if REQUESTS_AVAILABLE and args.license_id:
        license_file = pkg_path / "LICENSE"
        assert license_file.stat().st_size > 0

    # Test if Git repository was initialised
    if GIT_AVAILABLE and args.prompt_mode == "yes":
        import subprocess

        result = subprocess.run(
            ["git", "status"], cwd=pkg_path, capture_output=True, text=True
        )
        assert "On branch" in result.stdout

    # Test if venv was created
    if args.prompt_mode == "yes":
        assert (pkg_path / ".venv").is_dir()


def test_package_exists_error(tmp_path: Path):
    raise NotImplementedError()
    args = get_mock_args(tmp_path, False)

    creation_mode(args)


if __name__ == "__main__":
    import sys

    tmp_path = Path(sys.argv[1])
    if input(f"{tmp_path.resolve()=} (Y/n): ") == "Y":
        test_package_creation(tmp_path)
