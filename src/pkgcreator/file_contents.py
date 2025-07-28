"""
Module for creating the file content for the important files of a Python package.

Includes tools to:
- List and download available license from 'choosealicense.com'.
- Create the file content according to the project seetings for:
    - pyproject.toml
    - README.md
    - __main__.py
    - .gitignore
"""

from datetime import datetime
from pathlib import Path
from sys import version_info

from pkgcreator import ProjectSettings
from pkgcreator.filetypes import Readme, Toml
from pkgcreator.logging_tools import logger

# There is a soft dependency on "requests" for get_available_licenses()/get_license()


class FileContent(dict):
    """
    Provides file contents for standard package files based on project settings.

    Acts like a dictionary, where filenames are keys and their contents are values.
    Use keyword arguments to override default content or add custom files.

    Examples
    --------
    To override the default content of, e.g. `.gitignore`:
        FileContent(project_settings, ".gitignore": new_content, ...)

    To add a new file such as `CHANGELOG.md`:
        FileContent(project_settings, "CHANGELOG.md": changelog_content, ...)

    Parameters
    ----------
    project_settings : ProjectSettings
        Settings used to generate default file contents.
    kwargs : dict of str
        Optional custom file contents. Keys are filenames, values are content strings.

    Notes
    -----
    Default files include:
        `.gitignore`, `LICENSE`, `pyproject.toml`, `README.md`, and `__main__.py`.
    """

    def __init__(self, project_settings: ProjectSettings, **kwargs):
        self.project_settings = project_settings
        kwargs.setdefault(".gitignore", self.get_gitignore())
        kwargs.setdefault("LICENSE", self.get_license())
        try:
            self.license_name = kwargs["LICENSE"].splitlines()[0]
        except Exception as _err:
            self.license_name = "LICENSENAME"
        kwargs.setdefault("pyproject.toml", self.get_pyproject_toml())
        kwargs.setdefault("README.md", self.get_readme())
        kwargs.setdefault("__main__.py", self.get_main_py())
        super().__init__(**kwargs)

    @staticmethod
    def get_gitignore():
        """Return default content for '.gitignore'."""
        return (
            "__pycache__\n"
            "#.gitignore\n"
            ".env\n"
            ".venv\n"
            ".vscode\n"
            ".draft*\n"
            ".playground*\n"
            "*.egg-info"
        )

    def get_license(self):
        """Return license text according to 'project_settings.license_id'."""
        project = self.project_settings
        if project.license_id is None:
            return ""
        logger.info(f"Try to get license {project.license_id}")
        try:
            license_text = get_license(project.license_id)
        except Exception as err:
            msg = f"Could not download license '{project.license_id}'"
            logger.error(err, exc_info=True)
            logger.warning(msg, exc_info=True)
            return ""

        try:
            license_text = license_text.replace("[fullname]", project.author_name)
            license_text = license_text.replace("[year]", str(datetime.today().year))
        except Exception as err:
            logger.error(err, exc_info=True)
            logger.warning("Could not set author/year in license text", exc_info=True)

        return license_text

    def get_pyproject_toml(self):
        """Return default value for 'pyproject.toml' according to 'project_settings'."""
        project = self.project_settings
        try:
            min_python = f"{version_info.major}.{version_info.minor:02}"
        except Exception as err:
            min_python = "3.00"
            logger.warning(err, exc_info=True)

        content = {
            "name": project.name,
            "version": "0.1.0",
            "license": {"file": "LICENSE"},
            "description": project.description,
            "readme": "README.md",
            "authors": [{"name": project.author_name, "email": project.author_mail}],
            "maintainers": [
                {"name": project.author_name, "email": project.author_mail}
            ],
            "requires-python": f">={min_python}",
            "dependencies": project.dependencies,
            "classifiers": project.classifiers,
        }

        toml = Toml()
        toml.add_heading("project")
        toml.add_easy(content)
        toml.add_heading("project.urls")
        toml.add_easy(project.urls)
        if project.make_script:
            toml.add_heading("project.scripts")
            toml.add_variable(project.name, f"{project.name}.__main__:main")
        if project.optional_dependencies:
            toml.add_heading("project.optional-dependencies")
            toml.add_list("full", project.optional_dependencies)

        return toml.content

    def get_readme(self):
        """Return default value for 'README' according to 'project_settings'."""
        project = self.project_settings
        # Create Readme object and define the links needed later
        file = Readme()
        author_link = file.link(project.author_name, project.github_owner)
        links = {"Source code": project.source, "Report bugs": project.issues}
        license_link = file.link(self.license_name, "./LICENSE")

        # General information about the package
        file.add_heading(project.name, to_toc=False)
        file.add_text(project.description, bold=True)
        file.add_text(f"\nDeveloped and maintained by {author_link}.\n")
        file.add_named_list(links)

        # License information
        file.add_heading("License", level=1, to_toc=False)
        file.add_text(f"Distributed under the {license_link}.")

        # Add example call if package is callable
        if project.make_script:
            file.add_heading("Usage", level=1, to_toc=False)
            file.add_text("You may directly call one of the two following lines:")
            file.add_codeblock(
                [f"{project.name} [OPTIONS]", f"python -m {project.name} [OPTIONS]"]
            )

        # List of features
        file.add_heading("Features", level=1, to_toc=False)
        file.add_toc()
        for feature in [f"Feature {idx}" for idx in range(5)]:
            file.add_heading(feature, level=2)
            file.add_text(f"Description for feature {feature}")
        file.add_toc(clear=True)

        # Requirements
        file.add_heading("Requirements", level=1, to_toc=False)
        file.add_list(*[f"required-package-{idx}" for idx in range(5)])

        return file.content

    def get_main_py(self):
        """Get basic content for __main__.py."""
        name = self.project_settings.name
        tab = f"{'':4}"
        return "\n".join(
            [
                "def main():",
                f'{tab}"""Entry point for "{name}"and "python -m {name}"."""',
                "",
                "",
                'if __name__ == "__main__":',
                f"{tab}main()",
                "",
            ]
        )


def get_available_licenses(api_url: str = None):
    """
    Get available license form the 'choosealicense.com' repository.

    You may specify a different GitHub repository by changing the 'api_url'.
    """
    import requests  # Soft dependency (violates PEP 8 on purpose)

    if api_url is None:
        api_url = (
            "https://api.github.com/repos/github/choosealicense.com/contents/_licenses"
        )

    response = requests.get(api_url)
    response.raise_for_status()
    contents = response.json()

    return {
        str(Path(item["name"]).with_suffix("")): item["download_url"]
        for item in contents
        if item["type"] == "file"
    }


def get_license(name: str, licenses: dict = None):
    """Download the chosen licenses."""
    import requests  # Soft dependency (violates PEP 8 on purpose)

    if licenses is None:
        licenses = get_available_licenses()
    download_url = licenses[name]
    response = requests.get(download_url)
    response.raise_for_status()

    text = response.text
    try:
        return text.split("\n---\n")[1].lstrip("\n")
    except IndexError:
        return text
