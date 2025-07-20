import logging
import os
import subprocess
import threading
import traceback


class LoggerPipe:
    """
    A file-like object with a valid file descriptor (fileno()) that can be passed
    to subprocess stdout or stderr. It captures the subprocess output and streams
    it line-by-line into a Python logger, optionally storing the lines.

    This class is platform-compatible and works on Windows, Linux, and macOS.

    Parameters
    ----------
    logger : logging.Logger
        The logger instance that receives the subprocess output.
    level : int, optional
        Logging level (e.g., logging.INFO, logging.ERROR). Default is logging.INFO.
    encoding : str, optional
        Encoding used to decode bytes from the subprocess output. Default is "utf-8".
    errors : str, optional
        Error handling strategy for decoding. Default is "replace".
    prefix : str, optional
        Optional string prefix prepended to every logged line. Default is None.
    save : bool, optional
        Whether the logged lines should be stored and accessible after execution.
        Default is True.
    """

    def __init__(
        self,
        logger: logging.Logger,
        level: int = logging.INFO,
        encoding: str = "utf-8",
        errors: str = "replace",
        prefix: str = None,
        save: bool = True,
    ):
        self.logger = logger
        self.level = level
        self.encoding = encoding
        self.errors = errors
        self.prefix = prefix or ""
        self.save = save
        self._rfd, self._wfd = os.pipe()
        self._collected_lines = []
        self._thread = threading.Thread(target=self._reader_thread, daemon=True)
        self._thread.start()

    def fileno(self) -> int:
        """
        Returns the OS-level writable file descriptor to be used by subprocess.

        Returns
        -------
        int
            The writable file descriptor (used for stdout/stderr in subprocess).
        """
        return self._wfd

    def _reader_thread(self) -> None:
        """
        Internal thread that reads from the pipe and logs each line.
        """
        with os.fdopen(
            self._rfd, "r", encoding=self.encoding, errors=self.errors
        ) as reader:
            for line in reader:
                line = line.rstrip("\r\n")
                if line:
                    if self.save:
                        self._collected_lines.append(line)
                    self.logger.log(self.level, f"{self.prefix}{line}")

    def close(self) -> None:
        """
        Closes the writable pipe end and waits for the reader thread to finish.
        """
        try:
            os.close(self._wfd)
        except OSError:
            pass
        self._thread.join()

    @property
    def lines(self) -> list[str] | None:
        """
        Returns the collected output lines, if saving is enabled.

        Returns
        -------
        list of str or None
            Collected lines from the subprocess output, or None if `save` is False.
        """
        return self._collected_lines if self.save else None

    def __enter__(self) -> "LoggerPipe":
        """
        Enters the context manager.

        Returns
        -------
        LoggerPipe
            The current instance.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exits the context manager and cleans up resources.
        """
        self.close()


def logged_subprocess_run(
    *popenargs,
    logger: logging.Logger,
    log_level_stdout: int = logging.INFO,
    log_level_stderr: int = logging.ERROR,
    encoding: str = "utf-8",
    errors: str = "replace",
    timeout: float = None,
    check: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Runs a subprocess, streams stdout and stderr to a logger in real-time,
    and returns a CompletedProcess object including captured output.

    Parameters
    ----------
    logger : logging.Logger
        Logger instance to which output is streamed.
    log_level_stdout : int, optional
        Log level for stdout. Default is logging.INFO.
    log_level_stderr : int, optional
        Log level for stderr. Default is logging.ERROR.
    encoding : str, optional
        Encoding for decoding output. Default is "utf-8".
    errors : str, optional
        Error strategy during decoding. Default is "replace".
    timeout : float, optional
        Timeout in seconds for the subprocess. Default is None.
    check : bool, optional
        Whether to raise CalledProcessError on non-zero exit code. Default is False.
    **kwargs : dict
        Additional keyword arguments passed to `subprocess.run()`.

    Returns
    -------
    subprocess.CompletedProcess
        CompletedProcess object containing args, returncode, stdout, and stderr.

    Raises
    ------
    subprocess.CalledProcessError
        If `check` is True and the subprocess returns a non-zero exit code.
    """
    with (
        LoggerPipe(logger, log_level_stdout, encoding, errors) as lp_out,
        LoggerPipe(logger, log_level_stderr, encoding, errors) as lp_err,
    ):
        kwargs["stdout"] = lp_out
        kwargs["stderr"] = lp_err
        kwargs["text"] = True

        logger.debug(f"Run subprocess {popenargs}")
        process = subprocess.run(*popenargs, timeout=timeout, check=False, **kwargs)

        result = subprocess.CompletedProcess(
            args=process.args,
            returncode=process.returncode,
            stdout=lp_out.lines,
            stderr=lp_err.lines,
        )

        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                process.args,
                output=result.stdout,
                stderr=result.stderr,
            )

        return result


# ANSI color codes
RESET = "\033[0m"  # default
COLORS = {
    logging.DEBUG: "\033[90m",  # light grey
    logging.INFO: "\033[0m",  # default
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[41m",  # red background
    "SUCCESS": "\033[92m",  # green
}


class LoggerFormatter(logging.Formatter):
    """
    Custom logging formatter with optional ANSI coloring and enhanced formatting options.

    Parameters
    ----------
    show_location : bool, optional
        Whether to include file/module/line number in the title.
    show_exc_info : bool, optional
        Whether to include the exception type and message in the description.
    show_stack_info : bool, optional
        Whether to include stack info if available.
    show_traceback : bool, optional
        Whether to include full traceback if exception info is set.
    """

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
            title = f"{COLORS.get("SUCCESS", RESET)}[INFO]{RESET} "
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


def get_logger() -> logging.Logger:
    """
    Creates and returns a logger configured for colored terminal output.

    Returns
    -------
    logging.Logger
        Configured logger instance with colored output and default INFO level.
    """
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
