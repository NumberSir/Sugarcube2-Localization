from collections.abc import Callable
from unittest import case

from core.parser.lexer import Lexer
from core.schema.enum import Delimiter, LexerItem


def slurp_quote(lexer: Lexer, end_quote: str) -> int:
    while True:
        ch = lexer.next()
        if ch == "\\":
            next_ch = lexer.next()
            if next_ch not in (Lexer.EOF, "\n"):
                continue

        if ch in (Lexer.EOF, "\n"):
            return Lexer.EOF

        if ch == end_quote:
            break

    return lexer.pos


def lex_left_meta(lexer: Lexer) -> Callable[[Lexer], ...] | None:
    if not lexer.accept("["):
        return lexer.error(LexerItem.Error, 'malformed square-bracketed markup')

    # Is link markup.
    if lexer.accept("["):
        lexer.data["isLink"] = True
    # May be image markup.
    else:
        lexer.accept("<>")
        if (not lexer.accept("Ii")) or (not lexer.accept("Mm")) or (not lexer.accept("Gg")) or (not lexer.accept("[")):
            return lexer.error(LexerItem.Error, 'malformed square-bracketed markup')
        lexer.data["isLink"] = False

    lexer.emit(LexerItem.LinkMeta)
    # account for both initial left square brackets
    lexer.depth = 2
    return lex_core_components


def lex_core_components(lexer: Lexer) -> Callable[[Lexer], ...] | None:
    what: str = "link" if lexer.data.get("isLink") else "image"
    delim: Delimiter = Delimiter.None_

    while True:
        match lexer.next():
            case Lexer.EOF | '\n':
                return lexer.error(LexerItem.Error, f'unterminated `{what}` markup')

            # This is not entirely reliable within sections that allow raw strings, since
            # it's possible, however unlikely, for a raw string to contain unpaired double
            # quotes.  The likelihood is low enough, however, that I'm deeming the risk as
            # acceptable—for now, at least.
            case '"':

                if slurp_quote(lexer, '"') == Lexer.EOF:
                    return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{what}` markup')
                break

            # possible pipe ('|') delimiter
            case '|':
                if delim == Delimiter.None_:
                    delim = Delimiter.LTR
                    lexer.backup()
                    lexer.emit(LexerItem.Text)
                    lexer.forward()
                    lexer.emit(LexerItem.DelimLTR)
                break

            # possible right arrow ('->') delimiter
            case '-':
                if delim == Delimiter.None_ and lexer.peek() == ">":
                    delim = Delimiter.LTR
                    lexer.backup()
                    lexer.emit(LexerItem.Text)
                    lexer.forward(2)
                    lexer.emit(LexerItem.DelimLTR)
                break

            #  possible left arrow ('<-') delimiter
            case '<':
                if delim == Delimiter.None_ and lexer.peek() == "-":
                    delim = Delimiter.RTL
                    lexer.backup()
                    lexer.emit(LexerItem.Link if lexer.data.get("isLink") else LexerItem.Source)
                    lexer.forward(2)
                    lexer.emit(LexerItem.DelimRTL)
                break

            case '[':
                lexer.depth += 1
                break

            case ']':
                lexer.depth -= 1
                if lexer.depth == 1:
                    match lexer.peek():
                        case '[':
                            lexer.depth += 1
                            lexer.backup()

                            if delim == Delimiter.RTL:
                                lexer.emit(LexerItem.Text)
                            else:
                                lexer.emit(LexerItem.Link if lexer.data.get("isLink") else LexerItem.Source)

                            lexer.forward(2)
                            lexer.emit(LexerItem.InnerMeta)
                            return lex_setter if lexer.data.get("isLink") else lex_image_link

                        case ']':
                            lexer.depth -= 1
                            lexer.backup()

                            if delim == Delimiter.RTL:
                                lexer.emit(LexerItem.Text)
                            else:
                                lexer.emit(LexerItem.Link if lexer.data.get("isLink") else LexerItem.Source)

                            lexer.forward(2)
                            lexer.emit(LexerItem.RightMeta)
                            return None

                        case _:
                            return lexer.error(LexerItem.Error, f'malformed `{what}` markup')

                break


def lex_image_link(lexer: Lexer) -> Callable[[Lexer], ...] | None:
    what: str = "link" if lexer.data.get("isLink") else "image"

    while True:
        match lexer.next():
            case Lexer.EOF | '\n':
                return lexer.error(LexerItem.Error, f'unterminated `{what}` markup')

            # This is not entirely reliable within sections that allow raw strings, since
            # it's possible, however unlikely, for a raw string to contain unpaired double
            # quotes.  The likelihood is low enough, however, that I'm deeming the risk as
            # acceptable—for now, at least.
            case '"':
                if slurp_quote(lexer, '"') == Lexer.EOF:
                    return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{what}` markup link compnent')
                break

            case '[':
                lexer.depth += 1
                break

            case ']':
                lexer.depth -= 1

                if lexer.depth == 1:
                    match lexer.peek():
                        case '[':
                            lexer.depth += 1
                            lexer.backup()
                            lexer.emit(LexerItem.Link)
                            lexer.forward(2)
                            lexer.emit(LexerItem.InnerMeta)
                            return lex_setter

                        case ']':
                            lexer.depth -= 1
                            lexer.backup()
                            lexer.emit(LexerItem.Link)
                            lexer.forward(2)
                            lexer.emit(LexerItem.RightMeta)
                            return None

                        case _:
                            return lexer.error(LexerItem.Error, f'malformed `{what}` markup')

                break


def lex_setter(lexer: Lexer) -> Callable[[Lexer], ...] | None:
    type_: str = "link" if lexer.data.get("isLink") else "image"

    while True:
        match lexer.next():
            case Lexer.EOF | '\n':
                return lexer.error(LexerItem.Error, f'unterminated `{type_}` markup')

            case '"':
                if slurp_quote(lexer, '"') == Lexer.EOF:
                    return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{type_}` markup setter component')
                break

            case "'":
                if slurp_quote(lexer, "'") == Lexer.EOF:
                    return lexer.error(LexerItem.Error, f'unterminated single quoted string in `{type_}` markup setter component')
                break

            case "[":
                lexer.depth += 1
                break

            case ']':
                lexer.depth -= 1
                if lexer.depth == 1:
                    if lexer.peek() != ']':
                        return lexer.error(LexerItem.Error, f'malformed `{type_}` markup')

                    lexer.depth -= 1
                    lexer.backup()
                    lexer.emit(LexerItem.Setter)
                    lexer.forward(2)
                    lexer.emit(LexerItem.RightMeta)
                    return None

                break


def parse_square_bracketed_markup(wikifier: ...): ...
