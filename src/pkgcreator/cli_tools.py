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
        # Different than usual argparse formatters: choices are always next to metavar
        if action.metavar is not None:
            result = action.metavar
        else:
            result = default_metavar

        if action.choices is not None:
            choices = f"={{{",".join(map(str, action.choices))}}}"
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
            else:
                if isinstance(result, str):
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
                text = text.rstrip("<FORMATTER:NOPERIOD>").rstrip()
            else:
                text += "."

        return text
