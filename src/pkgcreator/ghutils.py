import argparse
from pathlib import Path

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

    def download(
        self,
        destination: str | Path,
        subfolder: str = None,
        branch: str = None,
        recursively: bool = True,
    ):
        """
        Download contents of a GitHub repository (or subfolder) via the API.

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
        url = self.get_api_url(name="contents", add=subfolder, branch=branch)
        response = requests.get(url)
        response.raise_for_status()
        contents = response.json()

        # Make destination
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        # Download (recursively if wanted)
        for item in contents:
            name = item["name"]
            if item["type"] == "file":
                download_url = item["download_url"]
                file_path = destination / name
                print(f"Downloading {name}...")
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


def get_sys_args():
    parser = argparse.ArgumentParser(
        description="Download a folder (or full content) from a github repository without cloning it."
    )
    parser.add_argument("owner", help="github username or organisation name")
    parser.add_argument("repository", help="repository name")
    parser.add_argument(
        "-b", "--branch", default="main", help="branch name (default: 'main')"
    )
    parser.add_argument(
        "-s", "--subfolder", default=None, help="path to subfolder in the repository"
    )
    parser.add_argument(
        "-d",
        "--destination",
        default=None,
        help="local destination directory (default: ./downloaded_<repository>)",
    )
    parser.add_argument(
        "-n",
        "--no-recursive",
        action="store_true",
        help="do not download folders recursively",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_sys_args()

    repository = GithubRepository(
        owner=args.owner, repository=args.repository, branch=args.branch
    )
    if args.destination is None:
        destination = f"downloaded_{args.repository}"
    else:
        destination = args.destination

    repository.download(
        destination=destination,
        subfolder=args.subfolder,
        recursively=not args.no_recursive,
    )
