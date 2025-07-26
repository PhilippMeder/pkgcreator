import pytest
from pathlib import Path

from pkgcreator import (
    GIT_AVAILABLE,
    GitRepository,
    GitNotAvailableError,
    GitRepositoryExistsError,
    GitRepositoryNotFoundError,
)


def test_git_init(tmp_path: Path):
    def check_existence():
        if (tmp_path / ".git").is_dir():
            assert repo.exists()
            return True
        else:
            assert not repo.exists()
            return False

    def check_init():
        try:
            repo.init()
            return True
        except GitRepositoryExistsError:  # TODO: How to assert the error type?
            return False

    # Test if init of class object works (depending on Git)
    try:
        repo = GitRepository(tmp_path)
        assert GIT_AVAILABLE
    except GitNotAvailableError:
        assert not GIT_AVAILABLE
        return

    # Test if .exists() works
    check_existence()

    # Test if Git init works
    check_init()

    # At this point, the repository exists!
    assert check_existence()
    assert not check_init()


def test_git_commit(tmp_path: Path):
    if not GIT_AVAILABLE:
        return

    # Make sure the tmp directory does not exist, else this test function is useless
    repo_path = tmp_path / "tmp_git_commit_test"
    if repo_path.exists():
        raise FileExistsError()

    repo = GitRepository(repo_path)

    # Test the GitRepositoryNotFoundError
    def check_existence_error():
        try:
            repo.add()
            return True
        except GitRepositoryNotFoundError:  # TODO: How to assert the error type?
            return False

    assert not check_existence_error()

    # Create repo (test is done in a different function)
    repo.init()
    (repo_path / "example_file.txt").touch()

    # Add/commit created file
    assert not repo.add().returncode
    assert not repo.commit().returncode

    # Add/commit file again -> Error: nothing to commit
    assert repo.add(check=False).returncode
    assert repo.commit(check=False).returncode
