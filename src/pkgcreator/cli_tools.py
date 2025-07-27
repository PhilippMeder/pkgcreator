import argparse


class ConsistentFormatter(argparse.HelpFormatter):
    """
    Provides a argparse formatter that aims for a consistent appearence.

    - metavars are always shown as "<METAVAR>" (uppercase enforced)
    - choices are always shown together with the metavar
    - text always starts with a capital letter and ends with a punctuation mark
      (to prevent the final punctuation add "<FORMATTER:NOPERIOD>")
    - keep custom formatting of description/epilog, but take care of line length
    """

    def _metavar_formatter(self, action, default_metavar):
        """
        Format the metavar as "<METAVAR>".

        Contrary to the usual argparse formatters, present choices will always be shown!
        """
        # Handle subparser and subcommands (do not change their appearence)
        if isinstance(
            action,
            argparse._SubParsersAction
            | argparse._SubParsersAction._ChoicesPseudoAction,
        ):
            return lambda tuple_size: (action.metavar or default_metavar,) * tuple_size
        # Different than usual argparse formatters: choices are always next to metavar
        result = action.metavar if action.metavar is not None else default_metavar

        if action.choices is not None:
            choices = f'={{{",".join(map(str, action.choices))}}}'
        else:
            choices = ""

        def format(tuple_size):
            # Do the format, but take care if a value is not a string (i.e. None)
            if isinstance(result, tuple):
                final = [
                    (
                        f"<{value.upper()}{choices}>"
                        if isinstance(value, str)
                        else f"<{value}{choices}>"
                    )
                    for value in result
                ]
                return tuple(final)  # this is necessary
            elif isinstance(result, str):
                return (f"<{result.upper()}{choices}>",) * tuple_size
            else:
                return (f"<{result}{choices}>",) * tuple_size

        return format

    def _get_default_metavar_for_optional(self, action):
        """Make optional metavar defaults uppercase."""
        return super()._get_default_metavar_for_optional(action).upper()

    def _get_default_metavar_for_positional(self, action):
        """Make positional metavar defaults uppercase."""
        return super()._get_default_metavar_for_positional(action).upper()

    def _expand_help(self, action):
        """Get help and enforce sentence style."""
        help_text = super()._expand_help(action)

        return self._make_sentence_style(help_text)

    def _fill_text(self, text, width, indent):
        """
        Format the text (esp. line length), but keep custom formatting like linebreaks.

        This is a mixture between argparse.HelpFormatter and
        argparse.RawDescriptionHelpFormatter.
        """
        import textwrap

        return textwrap.fill(
            self._make_sentence_style(text),
            width,
            initial_indent=indent,
            subsequent_indent=indent,
            drop_whitespace=False,
            replace_whitespace=False,
            break_on_hyphens=False,
        )

    @staticmethod
    def _make_sentence_style(text: str):
        """Enforce a capital letter at the beginning and a punctuation at the end."""
        if text:
            # Cannot use `.capitalize()` since it deletes uppercase words
            text = text[0].upper() + text[1:]

        if not text.endswith((".", "!", "?")):
            if text.endswith("<FORMATTER:NOPERIOD>"):
                text = text.removesuffix("<FORMATTER:NOPERIOD>").rstrip()
            else:
                text += "."

        return text


def generate_parser_template(feature_name: str, groups: dict, n_tab: int = 4):
    """
    Generate a template for an argparse-based feature parser with grouped arguments.

    Parameters
    ----------
    feature_name : str
        The name of the CLI feature, e.g., "examplefeature".
    groups : dict
        A dictionary mapping group names to argument dictionaries.
        Example:
        {
            "Group 1": {"-a": "Alpha option", ("-b", "--beta"): "Beta option"},
            "Group 2": {"--config": "Path to config"}
        }
    n_tab : int
        Number of spaces that represent code indentation (Default: 4).

    Returns
    -------
    str
        The full Python code string for the feature parser.
    """
    import textwrap

    # Define indentation
    tab = f"{'':{n_tab}}"

    # Header
    func_name = f"get_{feature_name}_parser"
    description = f"{feature_name.capitalize()} does something useful"

    # Docstring (do not indent the code here since this breaks the final string result)
    docstring = f'''"""
Create and configure the argument parser for '{feature_name}'.

This function can either add a subparser to an existing ArgumentParser
(via `subparsers`) or create a standalone parser when called independently.
Useful for modular CLI designs.

Parameters
----------
subparsers : argparse._SubParsersAction, optional
    Subparsers object from the main parser to which this parser should be added.
    If None, a standalone ArgumentParser is created instead.
prog : str, optional
    The program name used in standalone mode. Ignored if `subparsers` is provided.
formatter_class : type, optional
    The formatter class to be used for argument help formatting. Defaults to
    argparse.ArgumentDefaultsHelpFormatter.

Returns
-------
argparse.ArgumentParser
    The configured argument parser (necessary esp. for standalone mode).
"""'''

    # Body
    body_lines = [
        f"def {func_name}(",
        f"{tab}subparsers: argparse._SubParsersAction = None,",
        f"{tab}prog: str = None,",
        f"{tab}formatter_class: type = None,",
        ") -> argparse.ArgumentParser:",
        textwrap.indent(docstring, tab),
        f'{tab}parser_options = {"{"}',
        f'{tab*2}"description": "{description}",',
        f'{tab*2}"epilog": "Some epilog",',
        f'{tab*2}"formatter_class": formatter_class or '
        "argparse.ArgumentDefaultsHelpFormatter,",
        f'{tab}{"}"}',
        f"{tab}if subparsers:",
        f"{tab*2}parser = subparsers.add_parser(",
        f'{tab*3}"{feature_name}", help=parser_options["description"], **parser_options',
        f"{tab*2})",
        f"{tab}else:",
        f"{tab*2}parser = argparse.ArgumentParser(prog=prog, **parser_options)",
        "",
        f"{tab}# Add argument groups",
    ]

    for group_name, args in groups.items():
        body_lines.append(f'{tab}group = parser.add_argument_group("{group_name}")')
        for arg, help_text in args.items():
            if isinstance(arg, str):
                arg_str = f'"{arg}"'
            else:
                arg_str = ", ".join([f'"{this_arg}"' for this_arg in arg])
            body_lines.append(f'{tab}group.add_argument({arg_str}, help="{help_text}")')
        body_lines.append("")

    body_lines.append(f"{tab}return parser")

    return "\n".join(body_lines)


def get_prompt_bool(message: str, mode: str, auto_decision: bool = False) -> bool:
    """Return True/False for a prompt according to mode or user input."""
    match mode:
        case "yes":
            return True
        case "no":
            return False
        case "auto":
            return auto_decision
        case "ask" | _:
            user_input = input(f"{message} (Y/n): ")
            return user_input == "Y"
