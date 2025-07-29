"""Test the additional tools (logging, CLI)."""

import argparse
import io
import logging
import re

from pkgcreator.cli_tools import ConsistentFormatter
from pkgcreator.logging_tools import LoggerFormatter


def get_example_parsers() -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:
    """Get an example pair of argparse (ArgumentParser, SubParser)."""
    parent_parser = argparse.ArgumentParser(
        prog="test", description="some description", formatter_class=ConsistentFormatter
    )

    subparsers = parent_parser.add_subparsers(dest="subcommands")
    parser = subparsers.add_parser(
        "command1",
        description="command description without PERIOD <FORMATTER:NOPERIOD>",
        help="call command 1",
        formatter_class=ConsistentFormatter,
    )
    parser.add_argument("name", help="set name")
    parser.add_argument(
        "-p",
        "--some-path",
        metavar="PATH",
        default=".",
        help="set some path",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["ask", "yes", "no", "auto"],
        default="ask",
        help="set mode",
    )

    return parent_parser, parser


def test_argparse_formatter() -> None:
    """Test the custom argparse formatter."""
    parent_parser, parser = get_example_parsers()

    # Test main parser
    help_text = parent_parser.format_help()
    help_text_lines = [line.strip() for line in help_text.splitlines()]
    important_lines = [
        "usage: test [-h] SUBCOMMANDS ...",
        "Some description.",
        "SUBCOMMANDS",
        "command1   Call command 1.",
        "-h, --help   Show this help message and exit.",
    ]
    for line in important_lines:
        assert line in help_text_lines

    # Test subparser
    help_text = parser.format_help()
    help_text_lines = [line.strip() for line in help_text.splitlines()]
    important_lines = [
        "usage: test command1 [-h] [-p <PATH>] [-m <MODE={ask,yes,no,auto}>] <NAME>",
        "Command description without PERIOD",
        "<NAME>                Set name.",
    ]
    for line in important_lines:
        assert line in help_text_lines

    alternatives = [
        "-p, --some-path <PATH>",
        "-p <PATH>, --some-path <PATH>",  # Python < 3.13
    ]
    assert alternatives[0] in help_text_lines or alternatives[1] in help_text_lines

    alternatives = [
        "-m, --mode <MODE={ask,yes,no,auto}>",
        "-m <MODE={ask,yes,no,auto}>, --mode <MODE={ask,yes,no,auto}>",  # Python < 3.13
    ]
    assert alternatives[0] in help_text_lines or alternatives[1] in help_text_lines


def remove_ansi_codes(text: str) -> str:
    """Delete all ansi codes from a text."""
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


def test_logger_formatter() -> None:
    """Test the custom logger formatter."""
    # Create logger with the formatter we want to test and set the ouput to a StringIO
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Add terminal output
    formatter = LoggerFormatter(
        show_exc_info=False,
        show_location=False,
        show_stack_info=False,
        show_traceback=False,
    )

    log_stream = io.StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Do some test logging
    logger.info("some info")
    try:
        raise ValueError("something went wrong")
    except ValueError as err:
        logger.warning(err, exc_info=True)
        logger.error(err, exc_info=True)

    # Get the logger text
    stream_handler.flush()
    raw_log = log_stream.getvalue()
    clean_log = remove_ansi_codes(raw_log)

    # Test if the logged lines have the wanted format
    assert "[INFO] some info" in clean_log
    assert "[WARNING] something went wrong" in clean_log
    assert "[ERROR] ValueError: something went wrong" in clean_log
