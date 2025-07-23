import argparse
import subprocess
from pathlib import Path

from pkgcreator.logging_tools import logger, logged_subprocess_run


class GitNotAvailableError(OSError):
    """Exception class when no Git installation was not found."""

    pass


class GitRepositoryExistsError(FileExistsError):
    """Exception class when Git repository already exists."""

    pass


class GitRepositoryNotFoundError(FileNotFoundError):
    """Exception class when Git repository was not found."""

    pass


def run_git_command(
    *args, silent: bool = False, logger=None, **kwargs
) -> subprocess.CompletedProcess:
    """
    Run a Git command.

    Parameters
    ----------
    *args : str
        Git command arguments (e.g., "status", "add", etc.).
    silent : bool, optional
        If True, suppress stdout and stderr (default is False).
    logger : logging.Logger, optional
        If provided, stream the subprocess output live to the logger.
    **kwargs
        Additional keyword arguments passed to `subprocess.run`.

    Returns
    -------
    subprocess.CompletedProcess
        The result of the subprocess execution.

    Raises
    ------
    subprocess.CalledProcessError
        If the Git command fails and `check=True`.
    """
    kwargs.setdefault("check", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("stdout", subprocess.PIPE)
    kwargs.setdefault("stderr", subprocess.PIPE)

    if silent:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    if logger and not silent:
        return logged_subprocess_run(["git", *args], logger=logger, **kwargs)
    else:
        return subprocess.run(["git", *args], **kwargs)


def get_git_config_value(key: str) -> str | None:
    """
    Get a Git configuration value by key.

    Parameters
    ----------
    key : str
        Configuration key to query (e.g., 'user.name').

    Returns
    -------
    str or None
        Value of the config key, or None if not found.
    """
    try:
        result = run_git_command(
            *["config", "--get", key],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def _is_git_available():
    """
    Check if Git is available on the system.

    Returns
    -------
    bool
        True if Git is installed, False otherwise.
    """
    try:
        run_git_command("--version", silent=True)
        return True
    except Exception as err:
        return False


GIT_AVAILABLE = _is_git_available()


class GitRepository:
    """
    Class for managing Git repositories.

    Parameters
    ----------
    path : str or Path
        Path to the target Git repository directory.
    logger : logging.Logger, optional
        If provided, stream the git command output live to the logger.

    Raises
    ------
    GitNotAvailableError (OSError)
        If Git is not available on the system.
    """

    def __init__(self, path: str | Path, logger=None):
        if not GIT_AVAILABLE:
            msg = "'Git' is not available on this system!"
            raise GitNotAvailableError(msg)
        self._path = Path(path)
        self.logger = logger

    @property
    def path(self) -> Path:
        """Path: The repository path."""
        return self._path

    def run_command(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """Run a Git command in the context of the repository."""
        return run_git_command(*args, cwd=self.path, logger=self.logger, **kwargs)

    def exists(self) -> bool:
        """
        Check whether a Git repository exists at the target path.

        Returns
        -------
        bool
            True if a repository exists, False otherwise.
        """
        try:
            self.run_command("status", silent=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def init(
        self,
        *git_init_options: str,
        branch: str = "main",
    ) -> subprocess.CompletedProcess:
        """
        Initialize a new Git repository.

        Parameters
        ----------
        *git_init_options : str
            Additional options for `git init`.
        branch : str, optional
            Initial branch name (default is "main").

        Returns
        -------
        subprocess.CompletedProcess
            Result of the `git init` command.

        Raises
        ------
        GitRepositoryExistsError (FileExistsError)
            If a repository exists and `raise_err=True`.
        """
        if self.exists():
            msg = f"A Git repository already exists in {self.path.resolve()}!"
            raise GitRepositoryExistsError(msg)

        return self.run_command("init", "-b", branch, *git_init_options)

    def add(
        self, *git_add_options: str, files: list[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Add files to the Git staging area.

        Parameters
        ----------
        *git_add_options : str
            Additional options for `git add`.
        files : list of str, optional
            Files to add. If None, all files are added.

        Returns
        -------
        subprocess.CompletedProcess
            Result of the `git add` command.

        Raises
        ------
        GitRepositoryNotFoundError (FileNotFoundError)
            If no repository was found.
        """
        if not self.exists():
            msg = f"There is no Git repository to add to in {self.path}!"
            raise GitRepositoryNotFoundError(msg)

        files = files or ["-A"]

        return self.run_command("add", *files, *git_add_options)

    def commit(self, msg: str, *git_commit_options: str) -> subprocess.CompletedProcess:
        """
        Commit staged changes to the repository.

        Parameters
        ----------
        msg : str
            Commit message.
        *git_commit_options : str
            Additional options for `git commit`.

        Returns
        -------
        subprocess.CompletedProcess
            Result of the `git commit` command.

        Raises
        ------
        GitRepositoryNotFoundError (FileNotFoundError)
            If no repository was found.
        """
        if not self.exists():
            msg = f"There is no Git repository to commit to in {self.path}!"
            raise GitRepositoryNotFoundError(msg)

        return self.run_command("commit", "-m", msg, *git_commit_options)
