import argparse
from pathlib import Path

from pkgcreator import (
    FileContent,
    PackageExistsError,
    ProjectSettings,
    PythonPackage,
    GitRepository,
    VirtualEnvironment,
    GIT_AVAILABLE,
    get_available_licenses,
    get_git_config_value,
    subprocess_output_to_logger,
)
from pkgcreator.logging_config import logger


def get_prompt_bool(message: str, mode: str, auto_decision: bool = False) -> bool:
    """Return True/False for a prompt according to mode or user input."""
    match mode:
        case "yes":
            return True
        case "no":
            return False
        case "auto":
            return auto_decision
        case "ask" | _:
            user_input = input(f"{message} (Y/n): ")
            return user_input == "Y"


def patch_default_settings(project_settings: ProjectSettings, args: argparse.Namespace):
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


def creation_mode(args: argparse.Namespace):
    """Run the creation process."""
    # Setup the project settings
    project_settings = ProjectSettings.from_argparser(args)
    project_settings.license_id = args.license
    destination_path = Path(args.destination)

    builder = PythonPackage(destination_path, args.name)
    if builder.project_path.exists():
        msg = f"The project path '{builder.project_path}' already exists!"
        raise PackageExistsError(msg)

    # Ask for some settings if not specified
    patch_default_settings(project_settings, args)

    # Check and return if creation is aborted, but ignore the "no" mode this time!
    msg = (
        f"Settings:\n{project_settings.nice_str}\n"
        f"Create package '{builder.name}' at '{builder.project_path.resolve()}'?"
    )
    if (
        not get_prompt_bool(msg, args.prompt_mode, auto_decision=True)
        and args.prompt_mode != "no"
    ):
        logger.info(f"Creation aborted")
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
            git_repository = GitRepository(builder.project_path)
            result = git_repository.init()
            subprocess_output_to_logger(result)
            result = git_repository.add()
            subprocess_output_to_logger(result)
            result = git_repository.commit("Created repository and initial commit")
            subprocess_output_to_logger(result)

    # Create ven and install package in editable mode if wanted
    msg = "Initalise venv and install package in editable mode?"
    if args.init_venv or get_prompt_bool(msg, args.prompt_mode, auto_decision=False):
        virtual_env = VirtualEnvironment(builder.project_path)
        virtual_env.create()
        virtual_env.install_packages(
            editable_packages=[str(builder.project_path.resolve())]
        )


def list_licenses_mode():
    available_licenses = get_available_licenses()
    licenses_str = ", ".join(available_licenses.keys())
    logger.info(f"Available licenses are:\n{licenses_str}")


def get_sys_args():
    """Get the settings."""
    parser = argparse.ArgumentParser(
        description="Create a new Python package structure with optional license."
    )

    parser.add_argument("name", help="name of the Python package to create")
    parser.add_argument(
        "-d",
        "--destination",
        default=".",
        help="destination directory for the package structure",
    )
    parser.add_argument(
        "-m",
        "--prompt-mode",
        choices=["ask", "yes", "no", "auto"],
        default="ask",
        help=(
            "control prompts for user interaction: ask (default), yes (always accept), "
            "no (always decline), auto (decide automatically)"
        ),
    )
    parser.add_argument(
        "-i",
        "--init-git",
        action="store_true",
        help="initialise Git repository and commit created files (requires 'Git')",
    )
    parser.add_argument(
        "-v",
        "--init-venv",
        action="store_true",
        help="initialise a virtual environment and install package in editable mode",
    )
    parser.add_argument(
        "-l",
        "--license",
        default=None,
        help="optional license to include in the package",
    )
    parser.add_argument(
        "--list-licenses",
        action="store_true",
        help="list all available licenses and exit",
    )
    ProjectSettings.add_to_argparser(parser, ignore=("license_id", "name"))

    return parser.parse_args()


def main():
    args = get_sys_args()
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


if __name__ == "__main__":
    main()
