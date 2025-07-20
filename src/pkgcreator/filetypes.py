class BaseFileType:

    newline = "\n"

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

    @staticmethod
    def listitem(text: str, index: int = None, level: int = 0) -> str:
        symbol = "-" if index is None else f"{index}."
        return f"{"  "*level}{symbol} {text}"


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
