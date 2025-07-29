"""Tools to find issues that might break the support for lower Python versions."""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    """Class to save a found issue."""

    filepath: Path
    lineno: int
    msg: str

    def __str__(self) -> str:
        return f"{self.filepath}:{self.lineno}: {self.msg}"


def find_problematic_fstrings_in_file(filepath: Path) -> list[Issue]:
    """Find nested f-strings since newer Python version support additional syntax."""
    try:
        with filepath.open("r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
        return []

    results = []
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"SyntaxError in {filepath}: {e}")
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    expr_text = ast.get_source_segment(source, part)
                    if expr_text and ('"' in expr_text or "'" in expr_text):
                        full_fstring = ast.get_source_segment(source, node)
                        results.append(
                            Issue(filepath, node.lineno, full_fstring.strip())
                        )
                        # Count only one time
                        break
    return results


def get_problemeatic_fstrings(target: str | Path) -> list[Issue]:
    """Find nested f-strings in all files of a directory."""
    project_root = Path(target)
    python_files = list(project_root.rglob("*.py"))

    all_issues = []
    for file in python_files:
        all_issues.extend(find_problematic_fstrings_in_file(file))

    return all_issues


if __name__ == "__main__":
    target = sys.argv[1]
    issues = get_problemeatic_fstrings(target)
    for issue in issues:
        print(issue)
    print(
        f"There were {len(issues)} f-strings that might not be compatible with Python "
        "versions < 3.12 (which implements PEP 701)\n"
        "THIS SCRIPT OVERDETECTS BY DESIGN TO TAKE CARE OF HEAVILY NESTED F-STRINGS!"
    )
