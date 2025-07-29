"""
Module for the command line interface of pkgcreator.

Includes all parsers and the logic for the CLI.
"""

import argparse
from pathlib import Path
from subprocess import CalledProcessError

from pkgcreator import (
    GIT_AVAILABLE,
    FileContent,
    GithubRepository,
    GitNotAvailableError,
    GitRepository,
    GitRepositoryExistsError,
    GitRepositoryNotFoundError,
    PackageExistsError,
    ProjectSettings,
    PythonPackage,
    VirtualEnvironment,
    get_available_licenses,
    get_git_config_value,
)
from pkgcreator.cli_tools import ConsistentFormatter, get_prompt_bool
from pkgcreator.logging_tools import logger


# Define argument parsers
def get_creator_parser(
    subparsers: argparse._SubParsersAction | None = None,
    prog: str | None = None,
    formatter_class: type | None = None,
) -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for 'creator'.

    This function can either add a subparser to an existing ArgumentParser
    (via `subparsers`) or create a standalone parser when called independently.
    Useful for modular CLI designs.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction, optional
        Subparsers object from the main parser to which this parser should be added.
        If None, a standalone ArgumentParser is created instead.
    prog : str, optional
        The program name used in standalone mode. Ignored if `subparsers` is provided.
    formatter_class : type, optional
        The formatter class to be used for argument help formatting. Defaults to
        argparse.ArgumentDefaultsHelpFormatter.

    Returns
    -------
    argparse.ArgumentParser
        The configured argument parser (necessary esp. for standalone mode).
    """
    parser_options = {
        "description": (
            "Creates a Python package structure with optional license, "
            "Git repository (requires Git), and virtual environment."
        ),
        "epilog": (
            "Example: Run (or `-m auto` to prevent creation of Git repository & venv)\n"
            "  > %(prog)s NAME -l LICENSE -m yes --description TEXT "
            "--github-username USER <FORMATTER:NOPERIOD>"
        ),
        "formatter_class": formatter_class or argparse.ArgumentDefaultsHelpFormatter,
    }
    if subparsers:
        parser = subparsers.add_parser(
            "create", help=parser_options["description"], **parser_options
        )
    else:
        parser = argparse.ArgumentParser(prog=prog, **parser_options)

    parser.add_argument("name", help="name of the Python package to create")
    parser.add_argument(
        "-d",
        "--destination",
        metavar="PATH",
        default=".",
        help=(
            "destination directory for the package structure "
            "(default: current working directory)"
        ),
    )
    parser.add_argument(
        "-m",
        "--prompt-mode",
        choices=["ask", "yes", "no", "auto"],
        default="ask",
        help=(
            "control prompts for user interaction: ask, yes (always accept), "
            "no (always decline), auto (decide automatically) (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--script",
        dest="make_script",
        action="store_true",
        help=(
            "make package callable as a script, i.e. create '__main__.py' with "
            "function 'main()' and use it as entry point for script <NAME>"
        ),
    )
    reset_color = "\033[0m"
    git_color = reset_color if GIT_AVAILABLE else "\033[31m"
    parser.add_argument(
        "--git",
        dest="init_git",
        action="store_true",
        help=(
            "initialise Git repository and commit created files "
            f"({git_color}requires 'Git'{reset_color})"
        ),
    )
    parser.add_argument(
        "--venv",
        dest="init_venv",
        action="store_true",
        help="initialise a virtual environment and install package in editable mode",
    )
    parser.add_argument(
        "--list-licenses",
        action="store_true",
        help="list all available licenses and exit",
    )
    ProjectSettings.add_to_argparser(parser, ignore=("name", "make_script"))

    return parser


def get_git_parser(
    subparsers: argparse._SubParsersAction | None = None,
    prog: str | None = None,
    formatter_class: type | None = None,
) -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for 'git'.

    This function can either add a subparser to an existing ArgumentParser
    (via `subparsers`) or create a standalone parser when called independently.
    Useful for modular CLI designs.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction, optional
        Subparsers object from the main parser to which this parser should be added.
        If None, a standalone ArgumentParser is created instead.
    prog : str, optional
        The program name used in standalone mode. Ignored if `subparsers` is provided.
    formatter_class : type, optional
        The formatter class to be used for argument help formatting. Defaults to
        argparse.ArgumentDefaultsHelpFormatter.

    Returns
    -------
    argparse.ArgumentParser
        The configured argument parser (necessary esp. for standalone mode).
    """
    parser_options = {
        "description": (
            "Initialises and optionally commits to a Git repository. "
            "Provided for completeness, but using Git directly is usually more "
            "flexible and preferred."
        ),
        "formatter_class": formatter_class or argparse.ArgumentDefaultsHelpFormatter,
    }
    if subparsers:
        parser = subparsers.add_parser(
            "git", help=parser_options["description"], **parser_options
        )
    else:
        parser = argparse.ArgumentParser(prog=prog, **parser_options)

    parser.add_argument(
        "path",
        type=str,
        help="path to the directory where the Git repository should be initialised",
    )
    parser.add_argument(
        "-b",
        "--branch",
        type=str,
        default="main",
        help="initial branch name (default: 'main')",
    )
    parser.add_argument(
        "-c",
        "--commit",
        action="store_true",
        help="make an initial commit after initialising the repository",
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Created repository and initial commit",
        help="commit message (used only if --commit is specified).",
    )

    return parser


def get_github_download_parser(
    subparsers: argparse._SubParsersAction | None = None,
    prog: str | None = None,
    formatter_class: type | None = None,
) -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for 'github-download'.

    This function can either add a subparser to an existing ArgumentParser
    (via `subparsers`) or create a standalone parser when called independently.
    Useful for modular CLI designs.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction, optional
        Subparsers object from the main parser to which this parser should be added.
        If None, a standalone ArgumentParser is created instead.
    prog : str, optional
        The program name used in standalone mode. Ignored if `subparsers` is provided.
    formatter_class : type, optional
        The formatter class to be used for argument help formatting. Defaults to
        argparse.ArgumentDefaultsHelpFormatter.

    Returns
    -------
    argparse.ArgumentParser
        The configured argument parser (necessary esp. for standalone mode).
    """
    parser_options = {
        "description": (
            "Downloads files or folders from a GitHub repository without performing a "
            "full Git clone."
        ),
        "formatter_class": formatter_class or argparse.ArgumentDefaultsHelpFormatter,
    }
    if subparsers:
        parser = subparsers.add_parser(
            "github-download", help=parser_options["description"], **parser_options
        )
    else:
        parser = argparse.ArgumentParser(prog=prog, **parser_options)

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
        help="local destination directory (default: ./downloaded_<REPOSITORY>)",
    )
    parser.add_argument(
        "-n",
        "--no-recursive",
        action="store_true",
        help="do not download folders recursively",
    )
    parser.add_argument(
        "--list",
        dest="list_content",
        action="store_true",
        help="list content of repository (or subfolder) and exit",
    )

    return parser


def get_venv_parser(
    subparsers: argparse._SubParsersAction | None = None,
    prog: str | None = None,
    formatter_class: type | None = None,
) -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for 'venv'.

    This function can either add a subparser to an existing ArgumentParser
    (via `subparsers`) or create a standalone parser when called independently.
    Useful for modular CLI designs.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction, optional
        Subparsers object from the main parser to which this parser should be added.
        If None, a standalone ArgumentParser is created instead.
    prog : str, optional
        The program name used in standalone mode. Ignored if `subparsers` is provided.
    formatter_class : type, optional
        The formatter class to be used for argument help formatting. Defaults to
        argparse.ArgumentDefaultsHelpFormatter.

    Returns
    -------
    argparse.ArgumentParser
        The configured argument parser (necessary esp. for standalone mode).
    """
    parser_options = {
        "description": (
            "Manages a virtual environment for the project, including creation and "
            "package installation."
        ),
        "formatter_class": formatter_class or argparse.ArgumentDefaultsHelpFormatter,
    }
    if subparsers:
        parser = subparsers.add_parser(
            "venv", help=parser_options["description"], **parser_options
        )
    else:
        parser = argparse.ArgumentParser(prog=prog, **parser_options)

    parser.add_argument(
        "-d",
        "--destination",
        dest="path",
        metavar="PATH",
        default=".",
        help=(
            "parent directory where the venv folder will be created "
            "(default: current working directory)"
        ),
    )
    parser.add_argument(
        "-c", "--create", action="store_true", help="create the virtual environment."
    )
    parser.add_argument(
        "-i",
        "--install",
        metavar="PACKAGE",
        nargs="+",
        help="list of packages to install (via pip).",
    )
    parser.add_argument(
        "-e",
        "--editable",
        metavar="PACKAGE",
        nargs="+",
        help="list of packages/local package paths to install in editable mode (-e).",
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

    return parser


# Define run modes
def patch_creator_default_settings(
    project_settings: ProjectSettings, args: argparse.Namespace
) -> None:
    """Ask or decide how a few settings should behave when not set explicitly."""
    if project_settings.is_default("github_repositoryname"):
        if get_prompt_bool(
            f"'--github-repositoryname' was not set. Set to {args.name}?",
            args.prompt_mode,
            auto_decision=True,
        ):
            project_settings.github_repositoryname = args.name
            logger.info(f"Set '--github-repositoryname' to {args.name}")

    if GIT_AVAILABLE and project_settings.is_default("author_name"):
        if git_user := get_git_config_value("user.name"):
            if get_prompt_bool(
                f"'--author-name' was not set. Set to {git_user} (from 'git config')?",
                args.prompt_mode,
                auto_decision=True,
            ):
                project_settings.author_name = git_user
                logger.info(f"Set '--author-name' to {git_user}")

    if GIT_AVAILABLE and project_settings.is_default("author_mail"):
        if git_mail := get_git_config_value("user.email"):
            if get_prompt_bool(
                f"'--author-mail' was not set. Set to {git_mail} (from 'git config')?",
                args.prompt_mode,
                auto_decision=True,
            ):
                project_settings.author_mail = git_mail
                logger.info(f"Set '--author-mail' to {git_mail}")


def creation_mode(args: argparse.Namespace) -> None:
    """Run the creation process."""
    # Setup the project settings
    project_settings = ProjectSettings.from_argparser(args)
    project_settings.make_script = args.make_script
    destination_path = Path(args.destination)

    builder = PythonPackage(destination_path, args.name, add_main=args.make_script)
    if builder.project_path.exists():
        msg = f"The project path '{builder.project_path}' already exists!"
        raise PackageExistsError(msg)

    # Ask for some settings if not specified
    patch_creator_default_settings(project_settings, args)

    # Check and return if creation is aborted, but ignore the "no" mode this time!
    msg = (
        f"Settings:\n{project_settings.nice_str}\n"
        f"Create package '{builder.name}' at '{builder.project_path.resolve()}'?"
    )
    if (
        not get_prompt_bool(msg, args.prompt_mode, auto_decision=True)
        and args.prompt_mode != "no"
    ):
        logger.info("Creation aborted")
        return

    # Create the package structure with file content
    file_content = FileContent(project_settings)
    builder.create(file_content=file_content)
    logger.info(f"Created project '{builder.name}' at '{builder.project_path}'")

    # Create git repository if wanted
    if GIT_AVAILABLE:
        git_msg = "Initalise Git repository and commit?"
        if args.init_git or get_prompt_bool(
            git_msg, args.prompt_mode, auto_decision=False
        ):
            git_repository = GitRepository(builder.project_path, logger=logger)
            git_repository.init()
            try:
                git_repository.add()
                git_repository.commit("Created repository and initial commit")
            except Exception as err:
                logger.error(err, exc_info=True)

    # Create ven and install package in editable mode if wanted
    msg = "Initalise venv and install package in editable mode?"
    if args.init_venv or get_prompt_bool(msg, args.prompt_mode, auto_decision=False):
        virtual_env = VirtualEnvironment(builder.project_path)
        virtual_env.create()
        virtual_env.install_packages(
            editable_packages=[str(builder.project_path.resolve())]
        )


def list_licenses_mode() -> None:
    """Show available licenses."""
    available_licenses = get_available_licenses()
    licenses_str = ", ".join(available_licenses.keys())
    logger.info(f"Available licenses are:\n{licenses_str}")


def git_mode(args: argparse.Namespace) -> None:
    """Run the git subcommand."""
    try:
        repository = GitRepository(args.path, logger=logger)
    except GitNotAvailableError as err:
        logger.error(err, exc_info=True)
    try:
        repository.init(branch=args.branch)
    except GitRepositoryExistsError as err:
        logger.error(err, exc_info=True)
    try:
        if args.commit:
            repository.add()
            repository.commit(args.message)
    except GitRepositoryNotFoundError as err:
        logger.error(err, exc_info=True)
    except CalledProcessError as err:
        msg = f"Probably nothing to commit: {err}"
        logger.warning(msg, exc_info=True)


def github_download_mode(args: argparse.Namespace) -> None:
    """Run the GitHub download mode."""
    repository = GithubRepository(
        owner=args.owner, repository=args.repository, branch=args.branch
    )

    if args.list_content:
        logger.info("Getting content (this may take some time)...")
        content_str = repository.get_contents_str(
            subfolder=args.subfolder,
            branch=args.branch,
            recursively=not args.no_recursive,
        )
        logger.info(f"Found content:\n{content_str}")
        return

    if args.destination is None:
        destination = f"downloaded_{args.repository}"
    else:
        destination = args.destination

    try:
        repository.download(
            destination=destination,
            subfolder=args.subfolder,
            branch=args.branch,
            recursively=not args.no_recursive,
        )
    except ImportError as err:
        logger.error(err, exc_info=True)


def venv_mode(args: argparse.Namespace) -> None:
    """Run the venv mode."""
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
            logger.error(warning_msg, exc_info=True)

    # Check for existence of the virtual environment
    try:
        if this_venv.exists():
            if not args.create:  # No message if it was just created
                logger.info(f"Found a virtual environment in '{this_venv.venv_dir}'...")
        else:
            logger.warning(f"Found no virtual environment '{this_venv.venv_dir}'!")
    except Exception as err:
        logger.error(err, exc_info=True)

    if args.install or args.editable:
        try:
            this_venv.install_packages(
                packages=args.install,
                editable_packages=args.editable,
            )
        except FileNotFoundError as err:
            logger.error(err, exc_info=True)


def main() -> None:
    """
    Run main CLI tool.

    To create a new subparser with name <NAME>, use the template generator:
        > from pkgcreator.cli_tools import generate_parser_template
        > generate_parser_template(<NAME>, {})
    """
    formatter_class = ConsistentFormatter
    parser = argparse.ArgumentParser(
        prog="pkgcreator",
        description=(
            "create a python package structure, initalise a Git repository or a "
            "virtual environment (venv), or download files from GitHub"
        ),
        formatter_class=formatter_class,
    )
    subparsers = parser.add_subparsers(dest="feature")

    feature_parsers = (
        get_creator_parser,
        get_git_parser,
        get_github_download_parser,
        get_venv_parser,
    )
    for feature_parser in feature_parsers:
        feature_parser(subparsers, formatter_class=formatter_class)

    args = parser.parse_args()
    match args.feature:
        case "create":
            if args.list_licenses:
                try:
                    list_licenses_mode()
                except ImportError as err:
                    logger.error(err, exc_info=True)
            else:
                try:
                    creation_mode(args)
                except OSError as err:
                    logger.error(err, exc_info=True)
        case "git":
            git_mode(args)
        case "github-download":
            github_download_mode(args)
        case "venv":
            venv_mode(args)
        case _:
            parser.print_help()
            parser.exit(message="Run again and specify a supported command.")


if __name__ == "__main__":
    main()
