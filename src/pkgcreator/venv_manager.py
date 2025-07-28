"""
Module for working with virtual environments.

Includes tools to:
- Create or access a virtual environment with `venv`.
- Get the Python executable of a virtual environment.
- Install Python packages into a virtual environment.
"""

import subprocess
import venv
from pathlib import Path
from sys import version_info

from pkgcreator.logging_tools import logger, logged_subprocess_run


class VirtualEnvironmentNotFoundError(FileNotFoundError):
    """Exception raised when virtual environment was not found."""


class InconsistentStateError(Exception):
    """Exception raised when a logical inconsistency occurs."""


class ConcreteEnvBuilder(venv.EnvBuilder):
    """
    Custom EnvBuilder that enforces pip and calls a post-creation callback.

    Parameters
    ----------
    creation_callback : callable, optional
        A function that is called with the context after venv creation.
    """

    def __init__(self, *args, creation_callback: callable = None, **kwargs) -> None:
        kwargs["with_pip"] = True
        self.creation_callback = creation_callback
        super().__init__(*args, **kwargs)

    def post_setup(self, context) -> None:
        """Add `.gitignore` and call creation callback after venv was created."""
        self.create_git_ignore_file(context)
        if self.creation_callback is not None:
            self.creation_callback(context)

    def create_git_ignore_file(self, context):
        """
        Create a `.gitignore` file in the environment directory.

        This method is calls the default implementation if available (Python >= 3.13).
        """
        try:
            super().create_git_ignore_file(context)
        except AttributeError:
            filepath = Path(context.env_dir) / ".gitignore"
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("# Created by venv managment of pkgcreator\n*\n")


class VirtualEnvironment:
    """
    Class to manage the creation and usage of a Python virtual environment.

    Parameters
    ----------
    parent_dir : str or Path
        The directory where the `.venv` folder should be created.
    venv_name : str, optional
        Name of the `.venv` folder (default is ".venv").
    add_version : bool, optional
        Whether to add the python version to the `.venv` folder name (default: False).
    """

    def __init__(
        self,
        parent_dir: str | Path,
        venv_name: str = None,
        add_version: bool = False,
    ):
        dir_name = ".venv" if venv_name is None else venv_name
        if add_version:
            dir_name = f"{dir_name}_{version_info.major}_{version_info.minor:02}"

        self._parent_dir = Path(parent_dir)
        self._venv_dir = self._parent_dir / dir_name
        self._created_venv_exe = None
        self._venv_exe = None

    @property
    def venv_dir(self) -> Path:
        """
        Return path to the virtual environment directory.

        Returns
        -------
        Path
            The path to the virtual environment directory.
        """
        return self._venv_dir

    @property
    def python(self) -> Path:
        """
        Return path to the Python executable of the virtual environment (if available).

        Returns
        -------
        Path
            Path to the Python executable inside the virtual environment.

        Raises
        ------
        VirtualEnvironmentNotFoundError(FileNotFoundError)
            If no Python executable was found in the venv directory.
        """
        if self._created_venv_exe is not None:
            return self._created_venv_exe
        elif self._venv_exe is not None:
            return self._venv_exe

        if not self.venv_dir.exists():
            msg = (
                f"No python executable found in '{self.venv_dir}' since this directory "
                "does not exist!"
            )
            raise VirtualEnvironmentNotFoundError(msg)

        possible_paths = (
            self.venv_dir / "bin" / "python.exe",
            self.venv_dir / "Scripts" / "python.exe",
            self.venv_dir / "bin" / "python",
        )

        for path in possible_paths:
            if path.exists():
                self._venv_exe = path
                return path
        else:
            msg = f"No python executable found in '{self.venv_dir}'!"
            raise VirtualEnvironmentNotFoundError(msg)

    def create(self) -> None:
        """
        Create the virtual environment.

        Raises
        ------
        FileExistsError
            If the venv directory already exists.
        InconsistentStateError
            If only one of the expected venv directory/file pair exists.
        """
        if self.exists():
            msg = f"Virtual environment in '{self.venv_dir}' already exists!"
            raise FileExistsError(msg)

        logger.info(f"Creating venv in '{self.venv_dir}' (this may take some time)...")
        builder = ConcreteEnvBuilder(creation_callback=self._process_creation_context)
        builder.create(self.venv_dir)
        logger.info(f"Finished creating venv in '{self.venv_dir}'.")

    def exists(self, ensure_logic: bool = True) -> bool:
        """
        Check whether the virtual environment already exists.

        Parameters
        ----------
        ensure_logic : bool, optional
            Whether to raise an error if only one of the expected directory/file pair
            exists (default: True).

        Returns
        -------
        bool
            Whether the virtual environment exists or not.

        Raises
        ------
        InconsistentStateError
            If only one of the expected directory/file pair exists and 'ensure_logic'.
        """
        dir_exists = self.venv_dir.exists()
        try:
            _python = self.python
            python_exists = True
        except FileNotFoundError:
            python_exists = False

        if dir_exists and python_exists:
            return True
        elif not dir_exists and not python_exists:
            return False
        elif ensure_logic:
            true_str = "exists"
            false_str = "does not exist"
            msg = (
                f"Found inconsistency while checking for the existence of a "
                f"virtual environment in '{self.venv_dir}': "
                f"the directory {true_str if dir_exists else false_str}, but "
                f"the Python interpreter {true_str if python_exists else false_str}!"
            )
            raise InconsistentStateError(msg)
        else:
            return python_exists

    def install_packages(
        self, packages: list[str] = None, editable_packages: list[str] = None, **kwargs
    ) -> None:
        """
        Install normal and editable packages into the virtual environment.

        Parameters
        ----------
        packages : list of str, optional
            List of package names to install via pip.
        editable_packages : list of str, optional
            List of local package paths to install in editable mode.
        **kwargs
            Additional keyword arguments passed to `subprocess.run`.
        """
        if packages is None:
            packages = []
        if editable_packages is None:
            editable_packages = []
        kwargs.setdefault("check", True)
        kwargs.setdefault("text", True)
        kwargs.setdefault("stdout", subprocess.PIPE)
        kwargs.setdefault("stderr", subprocess.PIPE)

        python = str(self.python)

        for package in packages:
            try:
                pip_install(python, package, logger=logger, **kwargs)
            except Exception as err:
                logger.error(f"Did not install package {package}: {err}", exc_info=True)

        for package in editable_packages:
            try:
                pip_install(python, package, "-e", logger=logger, **kwargs)
            except Exception as err:
                logger.error(
                    f"Did not install editable package {package}: {err}", exc_info=True
                )

    def _process_creation_context(self, context) -> None:
        """
        Store the path to the Python executable in the venv after creation.

        Parameters
        ----------
        context : venv.EnvBuilder.Context
            The context object provided by EnvBuilder.
        """
        self._created_venv_exe = context.env_exe


def pip_install(
    python: str, package: str, *pip_args, silent: bool = False, logger=None, **kwargs
):
    """
    Install a Python package using `pip` via a given Python interpreter.

    This function constructs and runs a pip install command like:
    `[python, -m, pip, install, *pip_args, package]`.

    If a logger is provided and `silent` is False, output is streamed
    in real time using `logged_subprocess_run`. Otherwise, `subprocess.run`
    is used directly.

    Parameters
    ----------
    python : str
        Path to the Python interpreter to use for the pip command.
    package : str
        The name of the package to install.
    *pip_args : str
        Additional arguments passed to `pip install` (e.g., `--upgrade`, `--no-cache-dir`).
    silent : bool, optional
        If True, disables logging even if a logger is provided. Default is False.
    logger : logging.Logger, optional
        Logger used to stream real-time output of the install command. If None, no logging is used.
    **kwargs : dict
        Additional keyword arguments passed to `subprocess.run()` or `logged_subprocess_run()`.

    Returns
    -------
    subprocess.CompletedProcess
        The result of the subprocess call, containing the exit code and (if captured) output.
    """
    command = [python, "-m", "pip", "install", *pip_args, package]
    if logger and not silent:
        return logged_subprocess_run(command, logger=logger, **kwargs)
    else:
        return subprocess.run(command, **kwargs)
