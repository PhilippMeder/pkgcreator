"""Tests for the Git tools."""

from pathlib import Path
from subprocess import CalledProcessError

import pytest

from pkgcreator import (
    GIT_AVAILABLE,
    GitRepository,
    GitRepositoryExistsError,
    GitRepositoryNotFoundError,
)


@pytest.mark.skipif(not GIT_AVAILABLE, reason="Git not available")
def test_git_init(tmp_path: Path) -> None:
    """Test the correct initialisation of a GitRepository and failing if it exists."""
    # Check init
    repo = GitRepository(tmp_path)
    repo.init()
    assert repo.exists()

    # Check GitRepositoryExistsError
    with pytest.raises(GitRepositoryExistsError):
        repo.init()


@pytest.mark.skipif(not GIT_AVAILABLE, reason="Git not available")
def test_git_commit(tmp_path: Path) -> None:
    """Test commiting to a Git repository."""
    # Make sure the tmp directory does not exist, else this test function is useless
    repo = GitRepository(tmp_path)

    # Test the GitRepositoryNotFoundError
    with pytest.raises(GitRepositoryNotFoundError):
        repo.add()

    # Create repo (test is done in a different function)
    repo.init()
    (tmp_path / "example_file.txt").touch()

    # Add/commit created file
    assert repo.add().returncode == 0
    assert repo.commit("Test commit").returncode == 0

    # Commit again -> Error: nothing to commit
    with pytest.raises(CalledProcessError):
        repo.commit("Test commit")
