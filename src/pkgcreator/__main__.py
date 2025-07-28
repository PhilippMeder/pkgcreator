"""
Entry point for the pkgcreator command-line interface.

When run as a script or module, this file delegates to the CLI logic
defined in `pkgcreator.cli.main`.
"""

from pkgcreator.cli import main as cli_mode


def main():
    """
    Run the CLI mode of the package creator.

    This function serves as the entry point when the module is executed directly
    via the command line. It delegates to the main CLI logic defined in
    `pkgcreator.cli.main`.
    """
    cli_mode()


if __name__ == "__main__":
    main()
