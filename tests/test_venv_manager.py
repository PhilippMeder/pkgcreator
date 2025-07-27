import subprocess
from pathlib import Path

import pytest

from pkgcreator import FileContent, ProjectSettings, PythonPackage, VirtualEnvironment


@pytest.mark.skip(reason="needs to long, turn it on again later")
def test_venv_creation(tmp_path: Path) -> None:
    # Create a package to install later
    package_name = "test_package"
    builder = PythonPackage(tmp_path, package_name)
    builder.create(file_content=FileContent(ProjectSettings()))
    toml = builder.project_path / "pyproject.toml"
    assert toml.is_file()
    assert toml.stat().st_size > 0

    # Venv should not exist right now
    virtual_env = VirtualEnvironment(tmp_path)
    assert not virtual_env.exists()

    # Create venv -> should exist with .gitignore
    virtual_env.create()
    assert virtual_env.exists()
    gitignore_file = virtual_env.venv_dir / ".gitignore"
    assert gitignore_file.is_file()
    assert "\n*\n" in gitignore_file.read_text()

    # Creating again should not be possible
    with pytest.raises(FileExistsError):
        virtual_env.create()

    virtual_env.install_packages(
        editable_packages=[str(builder.project_path.resolve())]
    )

    result = subprocess.run(
        [virtual_env.python, "-m", "pip", "list"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert package_name in result.stdout
