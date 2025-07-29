"""Tests for the GitHub tools."""

import pytest

from pkgcreator import GithubRepository


def test_github_urls() -> None:
    """Test the URLs created by GithubRepository."""
    user = "python"
    repo_name = "cpython"
    branch = "main"
    repository = GithubRepository(user, repo_name, branch=branch)

    # Test if the parameters were set correctly
    assert repository.owner == user
    assert repository.name == repo_name
    assert repository.branch == branch

    # Test repository URLs (the URLs might change in the future)
    repo_url = "https://github.com/python/cpython"
    commits_url = "https://github.com/python/cpython/commits"
    readme_url = "https://github.com/python/cpython/README.md"
    assert repository.url == repo_url
    assert repository.get_url("repository", branch=False) == repo_url
    assert repository.get_url("homepage", branch=False) == repo_url
    assert repository.get_url("download", branch=False) == repo_url
    assert repository.get_url("changelog", branch=False) == commits_url
    assert repository.get_url("releasenotes", branch=False) == commits_url
    assert repository.get_url("documentation", branch=False) == readme_url
    assert (
        repository.get_url("issues", branch=False)
        == "https://github.com/python/cpython/issues"
    )
    assert (
        repository.get_url("source", branch=False)
        == "https://github.com/python/cpython.git"
    )
    assert repository.get_url("owner", branch=False) == "https://github.com/python"

    # Test API URLs
    assert repository.api_url == "https://api.github.com/repos/python/cpython"
    assert (
        repository.get_api_url("contents", branch=False)
        == "https://api.github.com/repos/python/cpython/contents"
    )


@pytest.mark.skip(reason="github api limits access rate")
def test_github_download() -> None:
    """Test the download function of GithubRepository."""
    # TODO: Write and move import to top
    # from importlib.util import find_spec

    # REQUESTS_AVAILABLE = False if find_spec("requests") is None else True
    raise NotImplementedError()
