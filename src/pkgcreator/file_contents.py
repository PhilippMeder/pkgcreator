from pathlib import Path
from sys import version_info

from pkgcreator import ProjectSettings
from pkgcreator.filetypes import Readme
from pkgcreator.logging_config import logger

# There is a soft dependency on "requests" for get_available_licenses()/get_license()


class FileContent(dict):

    def __init__(self, project_settings: ProjectSettings, **kwargs):
        self.project_settings = project_settings
        kwargs.setdefault(".gitignore", self.get_gitignore())
        kwargs.setdefault("LICENSE", self.get_license())
        try:
            self.license_name = kwargs["LICENSE"].splitlines()[0]
        except Exception as err:
            self.license_name = "LICENSENAME"
        kwargs.setdefault("pyproject.toml", self.get_pyproject_toml())
        kwargs.setdefault("README.md", self.get_readme())
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
        if self.project_settings.license_id is None:
            return ""
        try:
            return get_license(self.project_settings.license_id)
        except Exception as err:
            msg = f"Could not download license '{self.project_settings.license_id}'"
            logger.error(err, exc_info=True)
            logger.warning(msg, exc_info=True)
            return ""

    def get_pyproject_toml(self):
        """Return default value for 'pyproject.toml' according to 'project_settings'."""
        project = self.project_settings
        author_str = f"""name="{project.author_name}", email="{project.author_mail}" """
        url_str = "".join(
            [
                f"""{name.capitalize()} = "{_url}"\n"""
                for name, _url in project.urls.items()
            ]
        )
        try:
            min_python = f"{version_info.major}.{version_info.minor:02}"
        except Exception as err:
            min_python = "3.00"
            logger.warning(err, exc_info=True)
        return (
            f"""[project]\nname = "{project.name}"\nversion = "0.1"\n"""
            f"""authors = [{{ {author_str} }},]\n"""
            f"""description = "{project.description}"\nreadme = "README.md"\n"""
            """license = { file = "LICENSE" }\n"""
            f"""requires-python = ">={min_python}"\n"""
            """dependencies = []\n"""
            """classifiers=[\n    "Programming Language :: Python :: 3",\n    """
            """"Operating System :: OS Independent",\n]"""
            f"""\n\n[project.urls]\n{url_str}"""
        )

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
