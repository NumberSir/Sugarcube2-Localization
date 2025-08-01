import re

from enum import Enum


class Patterns(Enum):
    """
    Regexes

    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/parserlib.js
    """
    PASSAGE_HEAD = re.compile(r""":: ?([\-\w.\'\"/& ]+) ?(\[[\S ]+])?\n""")
    COMMENT = re.compile(r"""(?:/\*|<!--)[\s\S]+?(?:\*/|-->)""")
    MACRO = re.compile(r"""<</?([\w=\-]+)(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
    TAG = re.compile(r"""(?<!<)<(?![<!])/?(\w+)\s*[\s\S]*?(?<!>)>(?!>)""")

    """ SPECIAL """
    MACRO_WIDGET = re.compile(r"""<<widget(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")


__all__ = [
    "Patterns",
]