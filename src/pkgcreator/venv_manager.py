import argparse
import subprocess
import venv
from pathlib import Path
from sys import version_info

from pkgcreator.logging_tools import logger, logged_subprocess_run


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
        """
        Add `.gitignore` and call creation callback after venv was created..
        """
        self.create_git_ignore_file(context)
        if self.creation_callback is not None:
            self.creation_callback(context)


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
        Returns
        -------
        Path
            The path to the virtual environment directory.
        """
        return self._venv_dir

    @property
    def python(self) -> Path:
        """
        Returns
        -------
        Path
            Path to the Python executable inside the virtual environment.

        Raises
        ------
        FileNotFoundError
            If no Python executable was found in the venv directory.
        """
        if self._created_venv_exe is not None:
            return self._created_venv_exe
        elif self._venv_exe is not None:
            return self._venv_exe

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
            msg = f"No python executable found in {self.venv_dir}!"
            raise FileNotFoundError(msg)

    def create(self) -> None:
        """
        Create the virtual environment.

        Raises
        ------
        FileExistsError
            If the venv directory already exists.
        """
        if self.venv_dir.exists():
            msg = f"{self.venv_dir} already exists!"
            raise FileExistsError(msg)

        logger.info(f"Creating venv in {self.venv_dir} (this may take some time)...")
        builder = ConcreteEnvBuilder(creation_callback=self._process_creation_context)
        builder.create(self.venv_dir)
        logger.info(f"Finished creating venv in {self.venv_dir}.")

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
        Stores the path to the Python executable in the venv after creation.

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
