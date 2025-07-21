class BaseFileType:

    newline = "\n"
    tab = f"{'':4}"

    def __init__(self):
        self._lines = []

    def add_newline(self):
        self._lines.append(self.newline)

    @property
    def lines(self):
        return self._lines

    @property
    def content(self):
        return self.newline.join(self.lines)


class Readme(BaseFileType):

    tab = f"{'':2}"

    def __init__(self, *args, **kwargs):
        self._headings = []
        super().__init__(*args, **kwargs)

    def add_text(self, *lines: str, bold: bool = False):
        for text in lines:
            if bold:
                text = self.bold(text)
            self._lines.append(text)

    def add_heading(self, text: str, level: int = 0, to_toc: bool = True):
        if self._lines and not self._lines[-1].endswith(self.newline):
            _start = self.newline
        else:
            _start = ""
        self._lines.append(f"{_start}{"#"*(level+1)} {text}{self.newline}")
        if to_toc:
            self._headings.append(text)

    def add_list(self, *items: str, ordered: bool = False, level: int = 0):
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
        if bold_name:
            items = [f"{self.bold(name)}: {value}" for name, value in content.items()]
        else:
            items = [f"{name}: {value}" for name, value in content.items()]
        self.add_list(*items, ordered=ordered, level=level)

    def add_rule(self):
        self._lines.append(f"{self.newline}---{self.newline}")

    def add_codeblock(self, code: str | list[str], language: str = "bash"):
        if isinstance(code, str):
            code = [code]
        self._lines.append(f"```{language}")
        self._lines += code
        self._lines.append("```")

    def add_toc(self, here: bool = False, clear: bool = False):
        """If 'here', place toc here, otherwise place at mark or make mark."""
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
        toc_lines = [
            f"{idx}. {self.link(heading, self.linkname_internal(heading))}"
            for idx, heading in enumerate(self._headings)
        ]
        return self.newline.join(toc_lines) + self.newline

    @staticmethod
    def bold(text: str) -> str:
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        return f"*{text}*"

    @staticmethod
    def link(name: str, target: str) -> str:
        return f"[{name}]({target})"

    @staticmethod
    def linkname_internal(text: str) -> str:
        return f"#{text.lower().replace(" ", "-").replace("_", "-")}"

    @classmethod
    def listitem(cls, text: str, index: int = None, level: int = 0) -> str:
        symbol = "-" if index is None else f"{index}."
        return f"{cls.tab*level}{symbol} {text}"


class Toml(BaseFileType):

    def add_heading(self, text: str):
        if self.lines:
            self._lines.append(f"{self.newline}[{text}]")
        else:
            self._lines.append(f"[{text}]")

    def add_dictionary(self, name: str, items: dict):
        self._lines.append(self.variable(name, self.dictionary(items), bare_value=True))

    def add_list(self, name: str, items: list):
        content = [
            self.dictionary(item) if isinstance(item, dict) else f'"{item}"'
            for item in items
        ]
        if not content:
            self._lines.append(self.variable(name, "[]", bare_value=True))
            return
        if len(content) < 2:
            self._lines.append(self.variable(name, f"[{content[0]}]", bare_value=True))
            return
        # Multinline list
        self._lines.append(self.variable(name, "[", bare_value=True))
        self._lines += [f"{self.tab}{item}," for item in content]
        self._lines.append("]")

    def add_variable(self, name: str, value: str):
        self._lines.append(self.variable(name, value))

    def add_easy(self, content: dict):
        for name, value in content.items():
            if isinstance(value, list):
                self.add_list(name, value)
            elif isinstance(value, dict):
                self.add_dictionary(name, value)
            else:
                self.add_variable(name, value)

    @classmethod
    def dictionary(cls, items: dict) -> str:
        content = [cls.variable(name, value) for name, value in items.items()]
        return "{" + ", ".join(content) + "}"

    @staticmethod
    def variable(name: str, value: str, bare_value: bool = False) -> str:
        if " " in name:
            name = f'"{name}"'
        if bare_value:
            return f"{name} = {value}"
        else:
            return f'{name} = "{value}"'


if __name__ == "__main__":
    file = Readme([])
    file.add_heading("Heading")
    file.add_toc()
    file.add_heading("Subheading 1", level=1)
    file.add_heading("Subheading 2", level=1)
    file.add_list("entry a", "entry b", "entry c")
    file.add_named_list({"Source code": "some link", "Report bugs": "some other link"})
    file.add_toc()
    print(file.content)
