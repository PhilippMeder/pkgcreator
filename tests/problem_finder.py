"""Tools to find issues that might break the support for lower Python versions."""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    """Class to save a found issue."""

    issuetype: int
    filepath: Path
    lineno: int
    msg: str

    @staticmethod
    def resolve(issuetype: int) -> int:
        """
        Resolve synonyms for an issuetype.

        - 484 = 604
        """
        match issuetype:
            case 604:
                return 484
            case _:
                return issuetype

    def __eq__(self, issuetype: int) -> bool:
        """
        Check if issue is equal to a certain issuetype.

        Note that 484 and 604 are treated as equal since both PEPs are covering the same
        issue and are treated like that in the checks.
        """
        return self.issuetype == self.resolve(issuetype)

    def __lt__(self, other) -> bool:
        """
        Check if issue is less than a certain issuetype.

        Makes Issue sortable.
        """
        if isinstance(other, int):
            return self.issuetype < self.resolve(other)
        else:
            return self.issuetype < other.issuetype

    def __str__(self) -> str:
        """Return a string representation of the issue."""
        return f"[PEP {self.issuetype}] {self.filepath}:{self.lineno}: {self.msg}"


class FileChecker:
    """
    Provide checks for a file.

    Raises an error on initialisation if the file could not be read or parsed to ast.
    """

    def __init__(self, filepath: str | Path) -> None:
        self._load_from(filepath)

    def _load_from(self, filepath: str | Path) -> None:
        """Load source and ast tree from filepath and set attributes of the object."""
        self._filepath = Path(filepath)
        self._source = filepath.read_text(encoding="utf-8")
        self._tree = ast.parse(self.source, filename=str(filepath))

    @property
    def filepath(self) -> Path:
        """Return the path to the inspected file."""
        return self._filepath

    @property
    def source(self) -> str:
        """Return the source content of the inspected file."""
        return self._source

    @property
    def tree(self) -> ast.Module:
        """Return the ast tree of the inspected file."""
        return self._tree

    def check_nested_fstrings(self) -> list[Issue]:
        """
        Find nested f-strings since newer Python version support additional syntax.

        PEP 701 allows f"{",":4}" which, for Python < 3.12 has to be f"{',':4}" instead.
        Therefore, all nested f-strings are listed as a POSSIBLE issue.

        Returns
        -------
        list of Issue
            List of possible issues.
        """
        issues = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.JoinedStr):
                for part in node.values:
                    if isinstance(part, ast.FormattedValue):
                        expr_text = ast.get_source_segment(self.source, part)
                        if expr_text and ('"' in expr_text or "'" in expr_text):
                            full_fstring = ast.get_source_segment(self.source, node)
                            issues.append(
                                Issue(
                                    issuetype=701,
                                    filepath=self.filepath,
                                    lineno=node.lineno,
                                    msg=(
                                        "Works for Python < 3.12?: "
                                        f"{full_fstring.strip()}"
                                    ),
                                )
                            )
                            # Count only one time
                            break
        return issues

    def check_kwarg_none_typing(self) -> list[Issue]:
        """
        Check parameters with default None but missing Optional[Type] or `| None`.

        PEP 484 and PEP 604 recommend to always include the default value when it
        differs from the type annotation.

        Returns
        -------
        list of Issue
            List of issues.
        """
        issues = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                defaults = node.args.defaults
                args = node.args.args[-len(defaults) :] if defaults else []
                for arg, default in zip(args, defaults, strict=True):
                    if isinstance(default, ast.Constant) and default.value is None:
                        if arg.annotation:
                            ann_str = ast.unparse(arg.annotation)
                            if "None" not in ann_str and "Optional" not in ann_str:
                                issues.append(
                                    Issue(
                                        issuetype=484,
                                        filepath=self.filepath,
                                        lineno=node.lineno,
                                        msg=(
                                            f"Param '{arg.arg}' default None, but hint "
                                            f"is '{ann_str}'"
                                        ),
                                    )
                                )
        return issues

    def check(self, checks: list[str] | None = None) -> list[Issue]:
        """
        Check the file for known issues.

        Parameters
        ----------
        checks : list of str
            List of function names to check the file content with (default: all).

        Returns
        -------
        list of Issue
            List of (possible) issues.
        """
        checks = ["check_nested_fstrings", "check_kwarg_none_typing"]

        all_issues = []
        for name in checks:
            try:
                check_func = getattr(self, name)
            except AttributeError as _err:
                print(f"Could not find check function '{name}'!")
                continue
            all_issues.extend(check_func())

        return all_issues


class ProblemFinder:
    """Find possible problems in all Python files in a directory."""

    def __init__(self, path: str | Path, pattern: str = "*.py") -> None:
        self._path = Path(path)
        self._pattern = pattern

    def check(self) -> list[Issue]:
        """Check all files in the directory recursively."""
        all_issues = []
        for file in self._path.rglob(self._pattern):
            checker = FileChecker(file)
            all_issues.extend(checker.check())

        return all_issues


if __name__ == "__main__":
    try:
        target = sys.argv[1]
    except IndexError:
        target = "./src"
    finder = ProblemFinder(target)
    issues = finder.check()
    issues.sort()
    for issue in issues:
        print(issue)
