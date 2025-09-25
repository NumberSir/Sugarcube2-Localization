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
    PassageHead = re.compile(r""":: *(.*?)(\[.*?]\s*)?(\{([^\n]*?)}\s*)?\n""")
    Comment = re.compile(r"""(?:/\*)([\s\S]+?)(?:\*/)|(?:<!--)([\s\S]+?)(?:-->)""")
    Macro = re.compile(r"""<<(/?[A-Za-z][\w-]*|[=-])(?:\s*((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
    Tag = re.compile(r"""(?<!<)<(/?[A-Za-z](?:(?:[\x2D.0-9A-Z_a-z\xB7\xC0-\xD6\xD8-\xF6\xF8-\u037D\u037F-\u1FFF\u200C\u200D\u203F\u2040\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD]|[\uD800-\uDB7F][\uDC00-\uDFFF])*-(?:[\x2D.0-9A-Z_a-z\xB7\xC0-\xD6\xD8-\xF6\xF8-\u037D\u037F-\u1FFF\u200C\u200D\u203F\u2040\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD]|[\uD800-\uDB7F][\uDC00-\uDFFF])*|[0-9A-Za-z]*))(?:\s+[^\u0000-\u001F\u007F-\u009F\s"'>\/=]+(?:\s*=\s*(?:"[^"]*?"|'[^']*?'|[^\s"'=<>`]+))?)*\s*\/?>""")
    PlainText = auto()          # TODO
    JavaScript = auto()    # TODO

    # NakedVariable = re.compile(r"""(?<![$0-9A-Z_a-z])[$_][$A-Z_a-z][$0-9A-Z_a-z]*(?:(?:\.[$A-Z_a-z][$0-9A-Z_a-z]*)|(?:\[\d+\])|(?:\["(?:\\.|[^"\\])+"\])|(?:\['(?:\\.|[^'\\])+'\])|(?:\[[$_][$A-Z_a-z][$0-9A-Z_a-z]*\]))*""")

    """ Special """
    MacroWidget = re.compile(r"""<<widget(?:\s*((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")

    # """ Fragment """
    # Variable = re.compile(r"""[$_][$A-Z_a-z][$0-9A-Z_a-z]*""")
    # Space = re.compile(r'[\s\u0020\f\n\r\t\v\u00a0\u1680\u180e\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]')
    # NotSpace = re.compile(r'[^\s\u0020\f\n\r\t\v\u00a0\u1680\u180e\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]')

    # """ Utils """
    # Desugar = re.compile(
    #     r'(?:""|\'\'|``)'                                       #    Empty quotes (incl. template literal)
    #     '|'
    #     r'(?:"(?:\\.|[^"\\])+")'                                #    Double-quoted, non-empty
    #     '|'
    #     r"(?:'(?:\\.|[^'\\])+')"                                #    Single quoted, non-empty
    #     '|'
    #     r'(`(?:\\.|[^`\\])+`)'                                  #  1=Template literal, non-empty
    #     '|'
    #     r'(?:[=+\-*/%<>&|^~!?:,;()\[\]{}]+)'                    #    Operator characters
    #     '|'
    #     r'(?:\.{3})'                                            #    Spread/rest syntax
    #     '|'
    #     r'([^"\'=+\-*/%<>&|^~!?:,;()\[\]{}\s]+)'                #  2=Barewords
    # )
    #
    # TemplateGroupStart = re.compile("\$\{")
    # TemplateGroupParse = re.compile(
    #     r'(?:""|\'\')'              #   Empty quotes
    #     '|'
    #     r'(?:"(?:\\.|[^"\\])+")'    #   Double quoted, non-empty
    #     '|'
    #     r"(?:'(?:\\.|[^'\\])+')"    #   Single quoted, non-empty
    #     '|'
    #     r'(\{)'                     # 1=Opening curly brace
    #     '|'
    #     r'(})'                      # 2=Closing curly brace
    # )


# class Mappings(Enum):
#     """
#     Mappings
#
#     https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/scripting.js
#     """
#     Token = {
#         # Story $variable sigil-prefix.
#         '$': 'State.variables.',
#         # Temporary _variable sigil-prefix.
#         '_': 'State.temporary.',
#         # Assignment operator.
#         'to': '=',
#         # Equality operators.
#         'eq': '==',
#         'neq': '!=',
#         'is': '===',
#         'isnot': '!==',
#         # Relational operators.
#         'gt': '>',
#         'gte': '>=',
#         'lt': '<',
#         'lte': '<=',
#         # Logical operators.
#         'and': '&&',
#         'or': '||',
#         # Unary operators.
#         'not': '!',
#         'def': '"undefined" !== typeof',
#         'ndef': '"undefined" === typeof',
#     }


# class LexerItem(Enum):
#     """
#     Lex item types object.
#
#     https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/wikifier-util.js
#     """
#     Error = auto()      # error
#     DelimLTR = auto()   # '|' or '->'
#     DelimRTL = auto()   # '<-'
#     InnerMeta = auto()  # ']['
#     ImageMeta = auto()  # '[img[', '[<img[', or '[>img['
#     LinkMeta = auto()   # '[['
#     Link = auto()       # link destination
#     RightMeta = auto()  # ']]'
#     Setter = auto()     # setter expression
#     Source = auto()     # image source
#     Text = auto()       # link text or image alt text


# class Delimiter(Enum):
#     """
#     Delimiter state object.
#
#     https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/wikifier-util.js
#     """
#     None_ = auto()  # no delimiter encountered
#     LTR = auto()   # '|' or '->'
#     RTL = auto()   # '<-'


# class MacroArgumentParserItem(Enum):
#     """
#     Lex item types object.
#
#     https://github.com/tmedwards/sugarcube-2/blob/develop/src/markup/parserlib.js
#     """
#     Error = auto()
#     Bareword = auto()
#     Expression = auto()
#     String = auto()
#     SquareBracket = auto()


class ModelField(Enum):
    MacroBlockHead = auto()
    MacroBlockTail = auto()
    TagBlockHead = auto()
    TagBlockTail = auto()


__all__ = [
    "Patterns",
    "ModelField",
]