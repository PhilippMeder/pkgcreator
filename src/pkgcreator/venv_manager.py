import argparse
import subprocess
import venv
import warnings
from pathlib import Path
from sys import version_info


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

        print(f"Creating venv in {self.venv_dir} (this may take some time)...")
        builder = ConcreteEnvBuilder(creation_callback=self._process_creation_context)
        builder.create(self.venv_dir)
        print(f"Finished creating venv in {self.venv_dir}.")

    def install_packages(
        self, packages: list[str] = None, editable_packages: list[str] = None
    ) -> None:
        """
        Install normal and editable packages into the virtual environment.

        Parameters
        ----------
        packages : list of str, optional
            List of package names to install via pip.
        editable_packages : list of str, optional
            List of local package paths to install in editable mode.
        """
        if packages is None:
            packages = []
        if editable_packages is None:
            editable_packages = []

        python = str(self.python)

        for package in packages:
            try:
                subprocess.run([python, "-m", "pip", "install", package], check=True)
            except Exception as err:
                print(f"Error installing {package}: {err}")
        for package in editable_packages:
            try:
                subprocess.run(
                    [python, "-m", "pip", "install", "-e", package], check=True
                )
            except Exception as err:
                print(f"Error installing editable {package}: {err}")

    def _process_creation_context(self, context) -> None:
        """
        Stores the path to the Python executable in the venv after creation.

        Parameters
        ----------
        context : venv.EnvBuilder.Context
            The context object provided by EnvBuilder.
        """
        self._created_venv_exe = context.env_exe


def get_sys_args():
    parser = argparse.ArgumentParser(
        description="Create and manage a Python virtual environment."
    )
    parser.add_argument(
        "-c", "--create", action="store_true", help="create the virtual environment."
    )
    parser.add_argument(
        "-i", "--install", nargs="*", help="list of packages to install (via pip)."
    )
    parser.add_argument(
        "-e",
        "--editable",
        nargs="*",
        help="list of local package paths to install in editable mode (-e).",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="parent directory where the venv folder will be created (default: current directory).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=".venv",
        help="name of the virtual environment folder (default: .venv).",
    )
    parser.add_argument(
        "--version-suffix",
        action="store_true",
        help="append Python major/minor version to the venv folder name.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_sys_args()

    this_venv = VirtualEnvironment(
        parent_dir=args.path,
        venv_name=args.name,
        add_version=args.version_suffix,
    )

    if args.create:
        try:
            this_venv.create()
        except FileExistsError as err:
            warning_msg = f"Could not create virtual environment: {err}"
            warnings.warn(warning_msg, UserWarning, stacklevel=2)

    if args.install or args.editable:
        try:
            this_venv.install_packages(
                packages=args.install,
                editable_packages=args.editable,
            )
        except FileNotFoundError as err:
            warning_msg = f"Error: {err}\nIs the virtual environment already created?"
            warnings.warn(warning_msg, UserWarning, stacklevel=2)
