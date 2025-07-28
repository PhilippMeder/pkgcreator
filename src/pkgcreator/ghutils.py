"""
Module for working with parts of a GitHub repository.

Includes tools to:
- Get important URLs of a GitHub repository.
- Get the content of a GitHub repository.
- Download (a part of) the content of a GitHub repository.
"""

from pathlib import Path

from pkgcreator.logging_tools import logger

# There is a soft dependency on "requests" for GithubRepository().download()


class GithubRepository:
    """
    Represents a GitHub repository and allows downloading its contents (or subfolders).

    Parameters
    ----------
    owner : str
        GitHub username or organisation.
    repository : str
        Name of the repository.
    branch : str, optional
        Branch to target (default is "main").

    Notes
    -----
    The `download` method requires the `requests` library as a soft dependency.
    """

    _base_url = "https://github.com"
    _base_api_url = "https://api.github.com/repos"

    def __init__(self, owner: str, repository: str, branch: str = None):
        self._owner = owner
        self._repository_name = repository
        self.branch = branch if branch else "main"

        self._create_important_urls()

    @property
    def owner(self) -> str:
        """str: Repository owner (username or organisation)."""
        return self._owner

    @property
    def name(self) -> str:
        """str: Repository name."""
        return self._repository_name

    @property
    def url(self) -> str:
        """str: Public GitHub URL of the repository."""
        return self._url

    @property
    def api_url(self) -> str:
        """str: GitHub API base URL for the repository."""
        return self._api_url

    def get_url(
        self, name: str = None, add: str = None, branch: str = None
    ) -> str | None:
        """
        Get a constructed GitHub URL based on a logical name.

        Parameters
        ----------
        name : str, optional
            Logical target name, e.g. "repository", "owner", "issues", etc.
        add : str, optional
            Additional path to append.
        branch : str, optional
            Branch to use for the URL query parameter.

        Returns
        -------
        str or None
            Constructed URL or None if the logical name is unknown.
        """
        repo_url = self.url
        match name:
            case None | "repository" | "download" | "homepage":
                url = repo_url
            case "owner":
                url = self._url_owner
            case "changelog" | "releasenotes":
                url = f"{repo_url}/commits"
            case "documentation":
                url = f"{repo_url}/README.md"
            case "issues":
                url = f"{repo_url}/issues"
            case "source":
                url = f"{repo_url}.git"
            case "funding" | _:
                return None

        return self._finalize_url(url, add=add, branch=branch)

    def get_api_url(
        self, name: str = None, add: str = None, branch: str = None
    ) -> str | None:
        """
        Get a constructed GitHub API URL.

        Parameters
        ----------
        name : str, optional
            Logical API resource name (e.g. "contents").
        add : str, optional
            Additional path to append.
        branch : str, optional
            Branch to use for the API query.

        Returns
        -------
        str or None
            Constructed API URL or None if unknown.
        """
        repo_url = self.api_url
        match name:
            case "content" | "contents":
                url = f"{repo_url}/contents"
            case _:
                return None

        return self._finalize_url(url, add=add, branch=branch)

    def contents(
        self, subfolder: str = None, branch: str = None, ensure_list: bool = True
    ) -> list[dict]:
        """
        Get contents of the GitHub repository (or subfolder) via the API.

        Parameters
        ----------
        subfolder : str, optional
            Repository subfolder to inspect. If None, the root is used.
        branch : str, optional
            Git branch to target. If None, defaults to self.branch.
        ensure_list : bool, optional
            Whether to ensure a list is returned, even for one child (default: True).

        Raises
        ------
        ModuleNotFoundError
            If the `requests` library is not installed.
        HTTPError
            If a request to the GitHub API or file URL fails.
        """
        import requests  # Soft dependency (violates PEP 8 on purpose)

        # Get contents json from github api
        url = self.get_api_url(name="contents", add=subfolder, branch=branch)
        response = requests.get(url)
        response.raise_for_status()
        contents = response.json()

        # Make sure contents is a list (esp. when there is only one item)
        if not isinstance(contents, list) and ensure_list:
            contents = [contents]

        return contents

    def download(
        self,
        destination: str | Path,
        subfolder: str = None,
        branch: str = None,
        recursively: bool = True,
    ):
        """
        Download contents of the GitHub repository (or subfolder) via the API.

        Parameters
        ----------
        destination : str or Path
            Local path where files will be saved.
        subfolder : str, optional
            Repository subfolder to download. If None, the root is used.
        branch : str, optional
            Git branch to target. If None, defaults to self.branch.
        recursively : bool, optional
            Whether to download folders recursively (default: True).

        Raises
        ------
        ModuleNotFoundError
            If the `requests` library is not installed.
        HTTPError
            If a request to the GitHub API or file URL fails.
        """
        import requests  # Soft dependency (violates PEP 8 on purpose)

        # Get contents json from github api
        contents = self.contents(subfolder=subfolder, branch=branch)

        # Make destination
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        # Download (recursively if wanted)
        for item in contents:
            name = item["name"]
            if item["type"] == "file":
                download_url = item["download_url"]
                file_path = destination / name
                logger.info(f"Downloading {name}...")
                file_response = requests.get(download_url)
                file_response.raise_for_status()
                # The following line is fine, pathlib uses a proper context manager
                file_path.write_bytes(file_response.content)
            elif item["type"] == "dir" and recursively:
                new_subfolder = f"{subfolder}/{name}" if subfolder else name
                new_destination = destination / name
                self.download(
                    new_destination,
                    subfolder=new_subfolder,
                    recursively=recursively,
                )

    def get_contents_str(
        self,
        subfolder: str = None,
        branch: str = None,
        recursively: bool = True,
        _level: int = 0,
    ) -> list[dict]:
        """
        Get a formatted string of the contents of the repository (or subfolder).

        Parameters
        ----------
        subfolder : str, optional
            Repository subfolder to inspect. If None, the root is used.
        branch : str, optional
            Git branch to target. If None, defaults to self.branch.
        recursively : bool, optional
            Whether to get the content recursively (default: True).

        Raises
        ------
        ModuleNotFoundError
            If the `requests` library is not installed.
        HTTPError
            If a request to the GitHub API or file URL fails.
        """

        def format_size(size: int, n_max: int = 4):
            """Format a file size value in kB."""
            units = {0: " B", 1: "kB", 2: "MB", 3: "GB", 4: "TB", 5: "PB"}
            diff = 1000
            idx = 0
            while n_max < len(f"{size:.2f}"):
                idx += 1
                size /= diff

            unit = units.get(idx, "??")

            return f"{size:>4.2f} {unit}"

        n_tab = 4
        tab = f"{'':{n_tab}}"
        size_tab = f"{'':{n_tab + 3}}"
        # Get contents json from github api
        contents = self.contents(subfolder=subfolder, branch=branch)

        # Get content
        lines = [f"{size_tab}{tab * _level}/{subfolder}"] if subfolder else []
        for item in contents:
            name = item["name"]
            size = item["size"]
            if item["type"] == "file":
                lines.append(
                    f"{format_size(size, n_max=n_tab)}{tab * (_level + 1)}{name}"
                )
            elif item["type"] == "dir" and recursively:
                new_subfolder = f"{subfolder}/{name}" if subfolder else name
                lines.append(
                    self.get_contents_str(
                        subfolder=new_subfolder,
                        branch=branch,
                        recursively=recursively,
                        _level=_level + 1,
                    )
                )

        return "\n".join(lines)

    def _finalize_url(self, url: str, add: str = None, branch: str = None) -> str:
        """
        Add 'add' and 'branch' reference to url.

        Parameters
        ----------
        url : str
            URL to finalise.
        add : str, optional
            Part to add to the URL.
        branch : str, optional
            Git branch to target. If None, defaults to self.branch. If False, do not add
            a branch reference at the end of the URL.

        Returns
        -------
        str
            Constructed URL.
        """
        if add is not None:
            url = f"{url}/{add}"
        if branch is None:
            branch = self.branch
        if branch:
            url = f"{url}?ref={branch}"

        return url

    def _create_important_urls(self):
        """Create important URLs of the repository."""
        self._url_owner = f"{self._base_url}/{self.owner}"
        self._url = f"{self._url_owner}/{self.name}"
        self._api_url = f"{self._base_api_url}/{self.owner}/{self.name}"
