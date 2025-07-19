import logging
import traceback


# ANSI color codes
RESET = "\033[0m"  # default
COLORS = {
    logging.DEBUG: "\033[90m",  # light grey
    logging.INFO: "\033[0m",  # default
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[41m",  # red background
}


class LoggerFormatter(logging.Formatter):

    def __init__(
        self,
        *args,
        show_location: bool = False,
        show_exc_info: bool = False,
        show_stack_info: bool = False,
        show_traceback: bool = False,
        **kwargs,
    ):
        self.show_location = show_location
        self.show_exc_info = show_exc_info
        self.show_stack_info = show_stack_info
        self.show_traceback = show_traceback
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelno, RESET)
        message = record.getMessage()

        if record.levelno == logging.INFO:
            title = ""
            description = ""
        elif record.levelno == logging.WARNING:
            title = "[WARNING]"
            title = self.add_info_to_title(title, record)
            description = self.add_to_description("", record)
        elif record.levelno >= logging.ERROR:
            exc_type = record.exc_info[0].__name__ if record.exc_info else "Error"
            title = f"[ERROR] {exc_type}:"
            title = self.add_info_to_title(title, record)
            description = self.add_to_description("", record)
        else:
            title = ""
            description = super().format(record)
            description = self.add_to_description(description, record)

        return f"{color}{title}{message}{description}{RESET}"

    def add_info_to_title(self, title: str, record: logging.LogRecord) -> str:
        if self.show_location:
            loc = f"File {record.pathname}, line {record.lineno}, in {record.module}"
            title = f"{title} {loc}:"

        return f"{title} "

    def add_to_description(self, description: str, record: logging.LogRecord) -> str:
        if self.show_exc_info and (info := record.exc_info):
            description = f"{description} {info[0].__name__}: {info[1]}"
        if self.show_traceback and record.exc_info:
            tb_info = "".join(traceback.format_tb(record.exc_info[2]))
            description = f"{description}\n{tb_info}"
        if self.show_stack_info and record.stack_info:
            description = f"{description}\n{record.stack_info}"

        return f" {description.rstrip()}"


def get_logger():
    logger = logging.getLogger("pkgcreator")
    logger.setLevel(logging.INFO)

    # Add terminal outpur
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = LoggerFormatter(
        show_exc_info=False,
        show_location=False,
        show_stack_info=False,
        show_traceback=False,
    )
    console.setFormatter(formatter)

    logger.addHandler(console)

    return logger


logger = get_logger()
