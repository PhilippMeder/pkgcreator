"""
Module for file content writing.

Includes tools to write:
- Markdown (README.md)
- Toml (pyproject.toml)
"""


class BaseFileType:
    """
    Base class for generating structured text files line by line.

    Attributes
    ----------
    newline : str
        Newline character used to separate lines.
    tab : str
        Tab indentation string used in subclasses.
    content : str
        File content.
    lines : list of str
        File content line by line.
    """

    newline = "\n"
    tab = f"{'':4}"

    def __init__(self):
        self._lines = []

    def add_newline(self):
        """Add a newline to the file content."""
        self._lines.append(self.newline)

    @property
    def lines(self) -> list[str]:
        """Get the file content line by line."""
        return self._lines

    @property
    def content(self) -> str:
        """Get the file content."""
        return self.newline.join(self.lines)


class Readme(BaseFileType):
    """Generator class for creating Markdown README files."""

    tab = f"{'':2}"

    def __init__(self, *args, **kwargs):
        self._headings = []
        super().__init__(*args, **kwargs)

    def add_text(self, *lines: str, bold: bool = False):
        """
        Add one or more lines of text to the content.

        Parameters
        ----------
        *lines : str
            Text lines to add.
        bold : bool, optional
            Whether to bold the text (default is False).
        """
        for text in lines:
            final_text = self.bold(text) if bold else text
            self._lines.append(final_text)

    def add_heading(self, text: str, level: int = 0, to_toc: bool = True):
        """
        Add a heading to the content, optionally registering it for the TOC.

        Parameters
        ----------
        text : str
            Heading text.
        level : int, optional
            Heading level (default is 0, i.e., H1).
        to_toc : bool, optional
            Whether to include this heading in the table of contents (default is True).
        """
        if self._lines and not self._lines[-1].endswith(self.newline):
            _start = self.newline
        else:
            _start = ""
        self._lines.append(f'{_start}{"#"*(level+1)} {text}{self.newline}')
        if to_toc:
            self._headings.append(text)

    def add_list(self, *items: str, ordered: bool = False, level: int = 0):
        """
        Add a bulleted or numbered list to the content.

        Parameters
        ----------
        *items : str
            List items to add.
        ordered : bool, optional
            Whether to use numbered list (default is False).
        level : int, optional
            Indentation level (default is 0).
        """
        if ordered:
            for idx, item in enumerate(items):
                self._lines.append(self.listitem(item, index=idx, level=level))
        else:
            for item in items:
                self._lines.append(self.listitem(item, level=level))

    def add_named_list(
        self,
        content: dict[str],
        ordered: bool = False,
        level: int = 0,
        bold_name: bool = True,
    ):
        """
        Add a list of key-value pairs, optionally bolding the keys.

        Parameters
        ----------
        content : dict of str
            Dictionary where key-value pairs will be listed.
        ordered : bool, optional
            Whether to use numbered list (default is False).
        level : int, optional
            Indentation level (default is 0).
        bold_name : bool, optional
            Whether to bold the keys (default is True).
        """
        if bold_name:
            items = [f"{self.bold(name)}: {value}" for name, value in content.items()]
        else:
            items = [f"{name}: {value}" for name, value in content.items()]
        self.add_list(*items, ordered=ordered, level=level)

    def add_rule(self):
        """Add a horizontal rule (---) to the content."""
        self._lines.append(f"{self.newline}---{self.newline}")

    def add_codeblock(self, code: str | list[str], language: str = "bash"):
        """
        Add a fenced code block with optional language annotation.

        Parameters
        ----------
        code : str or list of str
            Code content to include in the block.
        language : str, optional
            Programming language identifier for syntax highlighting (default is `bash`).
        """
        if isinstance(code, str):
            code = [code]
        self._lines.append(f"```{language}")
        self._lines += code
        self._lines.append("```")

    def add_toc(self, here: bool = False, clear: bool = False):
        """
        Insert or mark a table of contents (TOC) placeholder.

        Parameters
        ----------
        here : bool, optional
            If True, place the TOC at the current position (default is False).
            If False, either mark the position to place the TOC later, or, if a mark is
            already present, place the TOC at the mark.
        clear : bool, optional
            If True, reset the internal heading list after insertion (default is False).
        """
        if here:
            self._lines.append(self.get_toc())
            return

        identifier = "<<MARK-FOR-TOC>>"
        try:
            idx = self.lines.index(identifier)
            toc = self.get_toc()
            try:
                if self._lines[idx + 1].startswith(self.newline):
                    toc = toc.removesuffix(self.newline)
            except IndexError:
                pass
            self._lines[idx] = toc
            if clear:
                self._headings = []
        except ValueError:
            self._lines.append(identifier)

    def get_toc(self):
        """
        Generate the table of contents as Markdown links.

        Returns
        -------
        str
            The Markdown-formatted table of contents.
        """
        toc_lines = [
            f"{idx}. {self.link(heading, self.linkname_internal(heading))}"
            for idx, heading in enumerate(self._headings)
        ]
        return self.newline.join(toc_lines) + self.newline

    @staticmethod
    def bold(text: str) -> str:
        """
        Format text as bold.

        Parameters
        ----------
        text : str
            The text to format.

        Returns
        -------
        str
            Bold-formatted Markdown string.
        """
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """
        Format text as italic.

        Parameters
        ----------
        text : str
            The text to format.

        Returns
        -------
        str
            Italic-formatted Markdown string.
        """
        return f"*{text}*"

    @staticmethod
    def link(name: str, target: str) -> str:
        """
        Create a Markdown hyperlink.

        Parameters
        ----------
        name : str
            Link text.
        target : str
            Target URL or anchor.

        Returns
        -------
        str
            Markdown link.
        """
        return f"[{name}]({target})"

    @staticmethod
    def linkname_internal(text: str) -> str:
        """
        Generate a Markdown-compatible anchor from a heading.

        Parameters
        ----------
        text : str
            Heading text.

        Returns
        -------
        str
            Anchor link for internal use.
        """
        return f'#{text.lower().replace(" ", "-").replace("_", "-")}'

    @classmethod
    def listitem(cls, text: str, index: int = None, level: int = 0) -> str:
        """
        Format a single list item with indentation.

        Parameters
        ----------
        text : str
            List item content.
        index : int, optional
            Index for ordered lists. If None, uses a bullet.
        level : int, optional
            Indentation level.

        Returns
        -------
        str
            Formatted list item.
        """
        symbol = "-" if index is None else f"{index}."
        return f"{cls.tab*level}{symbol} {text}"


class Toml(BaseFileType):
    """Generator class for creating TOML configuration files."""

    def add_heading(self, text: str):
        """
        Add a section header to the TOML file.

        Parameters
        ----------
        text : str
            Section name.
        """
        if self.lines:
            self._lines.append(f"{self.newline}[{text}]")
        else:
            self._lines.append(f"[{text}]")

    def add_dictionary(self, name: str, items: dict):
        """
        Add a named dictionary as a TOML object.

        Parameters
        ----------
        name : str
            Variable name.
        items : dict
            Dictionary to serialize as TOML.
        """
        self._lines.append(self.variable(name, self.dictionary(items), bare_value=True))

    def add_list(self, name: str, items: list):
        """
        Add a variable containing a list.

        Parameters
        ----------
        name : str
            Variable name.
        items : list
            List content (can include dicts or strings).
        """
        content = [
            self.dictionary(item) if isinstance(item, dict) else f'"{item}"'
            for item in items
        ]
        if not content:
            self._lines.append(self.variable(name, "[]", bare_value=True))
            return
        if len(content) == 1:
            self._lines.append(self.variable(name, f"[{content[0]}]", bare_value=True))
            return
        # Multinline list
        self._lines.append(self.variable(name, "[", bare_value=True))
        self._lines += [f"{self.tab}{item}," for item in content]
        self._lines.append("]")

    def add_variable(self, name: str, value: str):
        """
        Add a basic key-value variable to the TOML.

        Parameters
        ----------
        name : str
            Variable name.
        value : str
            Variable value.
        """
        self._lines.append(self.variable(name, value))

    def add_easy(self, content: dict):
        """
        Add variables, lists, or dictionaries from a single dictionary.

        Parameters
        ----------
        content : dict
            Dictionary of variables to insert, type inferred.
        """
        for name, value in content.items():
            if isinstance(value, list):
                self.add_list(name, value)
            elif isinstance(value, dict):
                self.add_dictionary(name, value)
            else:
                self.add_variable(name, value)

    @classmethod
    def dictionary(cls, items: dict) -> str:
        """
        Convert a dictionary to TOML dictionary string.

        Parameters
        ----------
        items : dict
            Dictionary to convert.

        Returns
        -------
        str
            TOML dictionary.
        """
        content = [cls.variable(name, value) for name, value in items.items()]
        return "{" + ", ".join(content) + "}"

    @staticmethod
    def variable(name: str, value: str, bare_value: bool = False) -> str:
        """
        Format a TOML key-value pair.

        Parameters
        ----------
        name : str
            Variable name.
        value : str
            Variable value.
        bare_value : bool, optional
            If True, value is assumed to already be in correct format.

        Returns
        -------
        str
            TOML key-value assignment.
        """
        if " " in name:
            name = f'"{name}"'
        if bare_value:
            return f"{name} = {value}"
        else:
            return f'{name} = "{value}"'
