import re

from enum import Enum, auto


class Patterns(Enum):
    """
    Regexes

    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/parserlib.js
    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/scripting.js
    https://github.com/tmedwards/sugarcube-2/blob/develop/src/lib/patterns.js
    """
    # PASSAGE_HEAD = re.compile(r""":: ?([\-\w.\'\"/& ]+) ?(\[[\S ]+])?\n""")
    PASSAGE_HEAD = re.compile(r"""::\s*(.*?)(\[.*?]\s*)?(\{(.*?)}\s*)?\n""")
    COMMENT = re.compile(r"""(?:/\*|<!--)([\s\S]+?)(?:\*/|-->)""")
    MACRO = re.compile(r"""<<(/?[A-Za-z][\w-]*|[=-])(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
    TAG = re.compile(r"""(?<!<)<(?![<!])(/?\w+)\s*([\s\S]*?)(?<!>)>(?!>)""")
    TEXT = auto()          # TODO
    JAVASCRIPT = auto()    # TODO

    NAKED_VARIABLE = re.compile(r"""[$_][$A-Z_a-z][$0-9A-Z_a-z]*(?:(?:\.[$A-Z_a-z][$0-9A-Z_a-z]*)|(?:\[\d+\])|(?:\["(?:\\.|[^"\\])+"\])|(?:\['(?:\\.|[^'\\])+'\])|(?:\[[$_][$A-Z_a-z][$0-9A-Z_a-z]*\]))*""")

    """ Special """
    MACRO_WIDGET = re.compile(r"""<<widget(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")

    """ Fragment """
    VARIABLE = re.compile(r"""[$_][$A-Z_a-z][$0-9A-Z_a-z]*""")

    """ Utils """
    DESUGAR = re.compile(
        r'(?:""|\'\'|``)'                                       #    Empty quotes (incl. template literal)
        '|'
        r'(?:"(?:\\.|[^"\\])+")'                                #    Double-quoted, non-empty
        '|'
        r"(?:'(?:\\.|[^'\\])+')"                                #    Single quoted, non-empty
        '|'
        r'(`(?:\\.|[^`\\])+`)'                                  #  1=Template literal, non-empty
        '|'
        r'(?:[=+\-*/%<>&|^~!?:,;()\[\]{}]+)'                    #    Operator characters
        '|'
        r'(?:\.{3})'                                            #    Spread/rest syntax
        '|'
        r'([^"\'=+\-*/%<>&|^~!?:,;()\[\]{}\s]+)'                #  2=Barewords
    )

    TEMPLATE_GROUP_START = re.compile("\$\{")
    TEMPLATE_GROUP_PARSE = re.compile(
        r'(?:""|\'\')'              #   Empty quotes
        '|'
        r'(?:"(?:\\.|[^"\\])+")'    #   Double quoted, non-empty
        '|'
        r"(?:'(?:\\.|[^'\\])+')"    #   Single quoted, non-empty
        '|'
        r'(\{)'                     # 1=Opening curly brace
        '|'
        r'(})'                      # 2=Closing curly brace
    )


class Mappings(Enum):
    """
    Mappings

    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/scripting.js
    """
    TOKEN = {
        # Story $variable sigil-prefix.
        '$': 'State.variables.',
        # Temporary _variable sigil-prefix.
        '_': 'State.temporary.',
        # Assignment operator.
        'to': '=',
        # Equality operators.
        'eq': '==',
        'neq': '!=',
        'is': '===',
        'isnot': '!==',
        # Relational operators.
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        # Logical operators.
        'and': '&&',
        'or': '||',
        # Unary operators.
        'not': '!',
        'def': '"undefined" !== typeof',
        'ndef': '"undefined" === typeof',
    }


class LexerItem(Enum):
    """
    Lex item types object.

    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/wikifier-util.js
    """
    Error = auto()      # error
    DelimLTR = auto()   # '|' or '->'
    DelimRTL = auto()   # '<-'
    InnerMeta = auto()  # ']['
    ImageMeta = auto()  # '[img[', '[<img[', or '[>img['
    LinkMeta = auto()   # '[['
    Link = auto()       # link destination
    RightMeta = auto()  # ']]'
    Setter = auto()     # setter expression
    Source = auto()     # image source
    Text = auto()       # link text or image alt text


class Delimiter(Enum):
    """
    Delimiter state object.

    https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/wikifier-util.js
    """
    None_ = auto()  # no delimiter encountered
    LTR = auto()   # '|' or '->'
    RTL = auto()   # '<-'


__all__ = [
    "Patterns",
    "Mappings",
    "LexerItem",
    "Delimiter",
]