import argparse
import requests
from pathlib import Path


class GithubRepository:
    """
    Represents a GitHub repository and allows downloading its contents (or subfolders).

    Parameters
    ----------
    owner : str
        GitHub username or organisation name.
    repository : str
        Repository name.
    branch : str, optional
        Branch name. Defaults to 'main'.
    """

    def __init__(self, owner: str, repository: str, branch: str = None):
        self.owner = owner
        self.repository = repository
        self.branch = branch if branch else "main"

        self._api_url = "https://api.github.com/repos"

    @property
    def url_part_branch(self):
        return f"?ref={self.branch}"

    @property
    def url_part_content(self):
        return "contents"

    @property
    def repository_url(self):
        return f"{self._api_url}/{self.owner}/{self.repository}"

    @property
    def repository_content_url(self):
        return f"{self.repository_url}/{self.url_part_content}"

    def download(
        self,
        destination_dir: str | Path,
        subfolder: str = None,
        recursively: bool = True,
    ):
        """
        Download a subfolder or the entire repository to a local directory.

        Parameters
        ----------
        destination_dir : str or Path
            Path to the local directory where files will be saved.
        subfolder : str, optional
            Relative path to a subfolder in the repository. If None, the root of the repository is used.
        recursively : bool, optional
            If True, subdirectories will be downloaded recursively. Default is True.

        Raises
        ------
        requests.HTTPError
            If the GitHub API request fails.
        """
        # Load the correct contents json from github
        subfolder_part = f"/{subfolder}" if subfolder else ""
        api_url = f"{self.repository_content_url}{subfolder_part}{self.url_part_branch}"
        response = requests.get(api_url)
        response.raise_for_status()
        contents = response.json()

        # Make destination
        destination_dir = Path(destination_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Download (recursively if wanted)
        for item in contents:
            name = item["name"]
            if item["type"] == "file":
                download_url = item["download_url"]
                file_path = destination_dir / name
                print(f"Downloading {name}...")
                file_response = requests.get(download_url)
                file_response.raise_for_status()
                # The following line is fine, pathlib uses a proper context manager
                file_path.write_bytes(file_response.content)
            elif item["type"] == "dir" and recursively:
                new_subfolder = f"{subfolder}/{name}" if subfolder else name
                new_destination_dir = destination_dir / name
                self.download(
                    new_destination_dir,
                    subfolder=new_subfolder,
                    recursively=recursively,
                )


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
        destination_dir=destination,
        subfolder=args.subfolder,
        recursively=not args.no_recursive,
    )
