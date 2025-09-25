# import re
# from collections.abc import Callable
#
# from core.parser.lexer import Lexer
# from core.schema.enum import Delimiter, LexerItem
# from core.schema.model import LexerItemModel
#
#
# class Wikifier:
#     def __init__(self, destination, source: str = None, options: dict = None):
#         self._source: str = source                              # The source text to process.
#         self._options: dict = options | {"profile": "all"}      # Our options.
#         self._output: str = None                                # Our output element or document fragment.
#         self._match_text: str = None                            # The current text that matched (the selected parser).
#         self._match_length: int = None                          # The length of the current text match.
#         self._match_start: int = None                           # The starting position of the current text match.
#         self._next_match: int = 0                               # The current position of parser (approximately: matchStart + matchLength).
#
#         # TODO: destination
#         # // No destination specified.  Create a fragment to act as the output buffer.
#         # if (destination == null) { // nullish test
#         #     this.output = document.createDocumentFragment();
#         # }
#         #
#         # // jQuery-wrapped destination.  Grab the first element.
#         # else if (destination instanceof jQuery) {
#         #     this.output = destination[0];
#         # }
#         #
#         # // Normal destination.
#         # else {
#         #     this.output = destination;
#         # }
#
#     # TODO: subWikify
#     # subWikify(output, terminator, options) {
#     # 	/**
#     # 	 * 目前的用法是将类 markdown 符号转为对应的 HTML tag
#     # 	 * eg: terminator -> tag
#     # 	 * parserlib.js
#     # 	 * - quoteByBlock
#     # 	 *   - <<<\n -> <blockquote>
#     # 	 * - formatByChar
#     # 	 *   - '' -> <strong>
#     # 	 *   - // -> <em>
#     # 	 *   - __ -> <u>
#     # 	 *   - ^^ -> <sup>
#     # 	 *   - ~~ -> <sub>
#     # 	 *   - == -> <s>
#     # 	 * - quoteByLine
#     # 	 *   - \n -> <br>
#     # 	 * - customStyle
#     # 	 *   - \n@@ -> <div> / <span>
#     # 	 *   - @@ -> <div> / <span>
#     # 	 * - heading
#     # 	 *   - \n -> <h1> ... <h6>
#     # 	 * - table
#     # 	 *   - \|(?:[cfhk]?)$\n? -> <style caption-side='top/bottom'>
#     # 	 * - list
#     # 	 *   - \n -> <li>
#     # 	 * - htmlTag
#     # 	 *   - <\/${tagName}\s*> -> <${tagName}>
#     # 	 */
#     #
#     # 	/** 1. output 与 options 的更新 */
#     # 	// Cache and temporarily replace the current output buffer.
#     # 	const oldOutput = this.output;
#     # 	this.output = output;
#     #
#     # 	let newOptions;
#     # 	let oldOptions;
#     #
#     # 	// Parser option overrides.
#     # 	if (Wikifier.Option.length > 0) {
#     # 		newOptions = Object.assign(newOptions || {}, Wikifier.Option.options);
#     # 	}
#     # 	// Local parameter option overrides.
#     # 	if (options !== null && typeof options === 'object') {
#     # 		newOptions = Object.assign(newOptions || {}, options);
#     # 	}
#     # 	// If new options exist, cache and temporarily replace the current options.
#     # 	if (newOptions) {
#     # 		oldOptions = this.options;
#     # 		this.options = Object.assign({}, this.options, newOptions);
#     # 	}
#     #
#     # 	/** 2.  */
#     # 	const parsersProfile   = Wikifier.Parser.Profile.get(this.options.profile);
#     # 	const terminatorRegExp = terminator
#     # 		? new RegExp(`(?:${terminator})`, this.options.ignoreTerminatorCase ? 'gim' : 'gm')
#     # 		: null;
#     # 	let terminatorMatch;
#     # 	let parserMatch;
#     #
#     # 	do {
#     # 		// Prepare the RegExp match positions.
#     # 		parsersProfile.parserRegExp.lastIndex = this.nextMatch;
#     #
#     # 		if (terminatorRegExp) {
#     # 			terminatorRegExp.lastIndex = this.nextMatch;
#     # 		}
#     #
#     # 		// Get the first matches.
#     # 		parserMatch     = parsersProfile.parserRegExp.exec(this.source);
#     # 		terminatorMatch = terminatorRegExp ? terminatorRegExp.exec(this.source) : null;
#     #
#     # 		// Try for a terminator match, unless there's a closer parser match.
#     # 		if (terminatorMatch && (!parserMatch || terminatorMatch.index <= parserMatch.index)) {
#     # 			// Output any text before the match.
#     # 			if (terminatorMatch.index > this.nextMatch) {
#     # 				this.outputText(this.output, this.nextMatch, terminatorMatch.index);
#     # 			}
#     #
#     # 			// Set the match parameters.
#     # 			this.matchStart  = terminatorMatch.index;
#     # 			this.matchLength = terminatorMatch[0].length;
#     # 			this.matchText   = terminatorMatch[0];
#     # 			this.nextMatch   = terminatorRegExp.lastIndex;
#     #
#     # 			// Restore the original output buffer and options.
#     # 			this.output = oldOutput;
#     #
#     # 			if (oldOptions) {
#     # 				this.options = oldOptions;
#     # 			}
#     #
#     # 			// Exit.
#     # 			return;
#     # 		}
#     #
#     # 		// Try for a parser match.
#     # 		else if (parserMatch) {
#     # 			// Output any text before the match.
#     # 			if (parserMatch.index > this.nextMatch) {
#     # 				this.outputText(this.output, this.nextMatch, parserMatch.index);
#     # 			}
#     #
#     # 			// Set the match parameters.
#     # 			this.matchStart  = parserMatch.index;
#     # 			this.matchLength = parserMatch[0].length;
#     # 			this.matchText   = parserMatch[0];
#     # 			this.nextMatch   = parsersProfile.parserRegExp.lastIndex;
#     #
#     # 			// Figure out which parser matched.
#     # 			let matchingParser;
#     #
#     # 			for (let i = 1, pMLength = parserMatch.length; i < pMLength; ++i) {
#     # 				if (parserMatch[i]) {
#     # 					matchingParser = i - 1;
#     # 					break; // stop once we've found the matching parser
#     # 				}
#     # 			}
#     #
#     # 			// Call the parser.
#     # 			parsersProfile.parsers[matchingParser].handler(this);
#     #
#     # 			if (TempState.break != null) { // nullish test
#     # 				break;
#     # 			}
#     # 		}
#     # 	} while (terminatorMatch || parserMatch);
#     #
#     # 	// Output any text after the last match.
#     # 	if (TempState.break == null) { // nullish test
#     # 		if (this.nextMatch < this.source.length) {
#     # 			this.outputText(this.output, this.nextMatch, this.source.length);
#     # 			this.nextMatch = this.source.length;
#     # 		}
#     # 	}
#     #
#     # 	// In case of <<break>>/<<continue>>, remove the last <br>.
#     # 	else if (
#     # 		this.output.lastChild
#     # 		&& this.output.lastChild.nodeType === Node.ELEMENT_NODE
#     # 		&& this.output.lastChild.nodeName.toUpperCase() === 'BR'
#     # 	) {
#     # 		jQuery(this.output.lastChild).remove();
#     # 	}
#     #
#     # 	// Restore the original output buffer and options.
#     # 	this.output = oldOutput;
#     #
#     # 	if (oldOptions) {
#     # 		this.options = oldOptions;
#     # 	}
#     # }
#
#     # TODO: outputText
#     # outputText(destination, startPos, endPos) {
#     #     jQuery(destination).append(document.createTextNode(this.source.substring(startPos, endPos)));
#     # }
#
#     # TODO: wikifyEval
#     # static wikifyEval(text) {
#     # 	const output = document.createDocumentFragment();
#     #
#     # 	new Wikifier(output, text);
#     #
#     # 	const errors = output.querySelector('.error');
#     #
#     # 	if (errors !== null) {
#     # 		throw new Error(errors.textContent.replace(errorPrologRE, ''));
#     # 	}
#     #
#     # 	return output;
#     # }
#
#     class Option:
#         _optionsStack: list[dict] = []
#
#         @classmethod
#         def length(cls):
#             return len(cls)
#
#         @classmethod
#         def __len__(cls):
#             return len(cls._optionsStack)
#
#         @classmethod
#         def options(cls):
#             return {
#                 k: v
#                 for option in cls._optionsStack
#                 for k, v in option.items()
#             }
#
#         @classmethod
#         def clear(cls):
#             cls._optionsStack = []
#
#         @classmethod
#         def get(cls, index: int):
#             return cls._optionsStack[index]
#
#         @classmethod
#         def pop(cls):
#             cls._optionsStack.pop()
#
#         @classmethod
#         def append(cls, options: dict):
#             if not isinstance(options, dict) or options is None:
#                 raise TypeError(f"Wikifier.Option.push options parameter must be a dict (received: {type(options)})")
#             cls._optionsStack.append(options)
#
#     class Parser:
#         _parsers: list[dict] = []
#         _profiles: dict = None
#
#         @classmethod
#         def parsers(cls) -> list[dict]:
#             return cls._parsers
#
#         @classmethod
#         def add(cls, parser: dict):
#             if not isinstance(parser, dict):
#                 raise TypeError("Wikifier.Parser.add parser parameter must be a dict")
#
#             if "name" not in parser.keys():
#                 raise Exception("parser object missing required 'name' property")
#             elif not isinstance(parser["name"], str):
#                 raise TypeError("parser object 'name' property must be a string")
#
#             if "match" not in parser.keys():
#                 raise Exception("parser object missing required 'match' property")
#             elif not isinstance(parser["match"], str):
#                 raise TypeError("parser object 'match' property must be a string")
#
#             if "handler" not in parser.keys():
#                 raise Exception("parser object missing required 'handler' property")
#             elif not isinstance(parser["handler"], Callable):
#                 raise TypeError("parser object 'handler' property must be a callable")
#
#             if "profiles" in parser and not isinstance(parser["profiles"], list):
#                 raise TypeError("parser object 'profiles' property must be a list")
#
#             if cls.has(parser["name"]):
#                 raise Exception(f"cannot clobber existing parser `{parser['name']}`")
#
#             cls._parsers.append(parser)
#
#         @classmethod
#         def delete(cls, name: str):
#             if parser := list(filter(lambda p: p["name"] == name, cls._parsers)):
#                 cls._parsers.remove(parser[0])
#
#         @classmethod
#         def is_empty(cls) -> bool:
#             return not len(cls._parsers)
#
#         @classmethod
#         def has(cls, name: str) -> bool:
#             return bool(list(filter(lambda p: p["name"] == name, cls._parsers)))
#
#         @classmethod
#         def get(cls, name: str) -> dict | None:
#             if parser := list(filter(lambda p: p["name"] == name, cls._parsers)):
#                 return parser[0]
#             return None
#
#         @classmethod
#         def profiles_getter(cls) -> dict:
#             return cls._profiles
#
#         @classmethod
#         def profiles_compile(cls) -> dict:
#             all_ = cls._parsers
#             core = list(filter(
#                 lambda p: (not isinstance(p.get("profiles"), list)) or ('core' in p.get("profiles")),
#                 all_
#             ))
#
#             cls._profiles = {
#                 "all": {
#                     "parsers": all_,
#                     "parserRegExp": re.compile('|'.join(f"({p['match']})" for p in all_))
#                 },
#                 "core": {
#                     "parsers": core,
#                     "parserRegExp": re.compile('|'.join(f"({p['match']})" for p in core))
#                 }
#             }
#             return cls._profiles
#
#         @classmethod
#         def profiles_is_empty(cls) -> bool:
#             return not isinstance(cls._profiles, dict) or len(cls._profiles) == 0
#
#         @classmethod
#         def profiles_get(cls, profile: str) -> dict:
#             if not isinstance(cls._profiles, dict) or profile not in cls._profiles:
#                 raise Exception(f"nonexistent parser profile '{profile}'")
#             return cls._profiles[profile]
#
#         @classmethod
#         def profiles_has(cls, profile: str) -> bool:
#             return isinstance(cls._profiles, dict) and profile in cls._profiles
#
#     @property
#     def source(self) -> str:
#         return self._source
#
#     @property
#     def options(self) -> dict:
#         return self._options
#
#     @options.setter
#     def options(self, options: dict):
#         self._options = options
#
#     @property
#     def output(self) -> str:
#         return self._output
#
#     @output.setter
#     def output(self, output: str):
#         self._output = output
#
#     @property
#     def match_text(self) -> str:
#         return self._match_text
#
#     @property
#     def match_length(self) -> int:
#         return self._match_length
#
#     @property
#     def match_start(self) -> int:
#         return self._match_start
#
#     @property
#     def next_match(self) -> int:
#         return self._next_match
#
#     @next_match.setter
#     def next_match(self, next_match: int):
#         self._next_match = next_match
#
#
# def slurp_quote(lexer: Lexer, end_quote: str) -> int:
#     while True:
#         ch = lexer.next()
#         if ch == "\\":
#             next_ch = lexer.next()
#             if next_ch not in {Lexer.EOF, "\n"}:
#                 continue
#
#         elif ch in {Lexer.EOF, "\n"}:
#             return Lexer.EOF
#
#         elif ch == end_quote:
#             break
#
#     return lexer.pos
#
#
# def lex_left_meta(lexer: Lexer) -> Callable[[Lexer], ...] | None:
#     if not lexer.accept("["):
#         return lexer.error(LexerItem.Error, 'malformed square-bracketed markup')
#
#     # Is link markup.
#     if lexer.accept("["):
#         lexer.data.is_link = True
#     # May be image markup.
#     else:
#         lexer.accept("<>")
#         if (not lexer.accept("Ii")) or (not lexer.accept("Mm")) or (not lexer.accept("Gg")) or (not lexer.accept("[")):
#             return lexer.error(LexerItem.Error, 'malformed square-bracketed markup')
#         lexer.data.is_link = False
#
#     lexer.emit(LexerItem.LinkMeta)
#     # account for both initial left square brackets
#     lexer.depth = 2
#     return lex_core_components
#
#
# def lex_core_components(lexer: Lexer) -> Callable[[Lexer], ...] | None:
#     what: str = "link" if lexer.data.is_link else "image"
#     delim: Delimiter = Delimiter.None_
#
#     while True:
#         match lexer.next():
#             case Lexer.EOF | '\n':
#                 return lexer.error(LexerItem.Error, f'unterminated `{what}` markup')
#
#             # This is not entirely reliable within sections that allow raw strings, since
#             # it's possible, however unlikely, for a raw string to contain unpaired double
#             # quotes.  The likelihood is low enough, however, that I'm deeming the risk as
#             # acceptable—for now, at least.
#             case '"':
#
#                 if slurp_quote(lexer, '"') == Lexer.EOF:
#                     return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{what}` markup')
#                 break
#
#             # possible pipe ('|') delimiter
#             case '|':
#                 if delim == Delimiter.None_:
#                     delim = Delimiter.LTR
#                     lexer.backup()
#                     lexer.emit(LexerItem.Text)
#                     lexer.forward()
#                     lexer.emit(LexerItem.DelimLTR)
#                 break
#
#             # possible right arrow ('->') delimiter
#             case '-':
#                 if delim == Delimiter.None_ and lexer.peek() == ">":
#                     delim = Delimiter.LTR
#                     lexer.backup()
#                     lexer.emit(LexerItem.Text)
#                     lexer.forward(2)
#                     lexer.emit(LexerItem.DelimLTR)
#                 break
#
#             #  possible left arrow ('<-') delimiter
#             case '<':
#                 if delim == Delimiter.None_ and lexer.peek() == "-":
#                     delim = Delimiter.RTL
#                     lexer.backup()
#                     lexer.emit(LexerItem.Link if lexer.data.is_link else LexerItem.Source)
#                     lexer.forward(2)
#                     lexer.emit(LexerItem.DelimRTL)
#                 break
#
#             case '[':
#                 lexer.depth += 1
#                 break
#
#             case ']':
#                 lexer.depth -= 1
#                 if lexer.depth == 1:
#                     match lexer.peek():
#                         case '[':
#                             lexer.depth += 1
#                             lexer.backup()
#
#                             if delim == Delimiter.RTL:
#                                 lexer.emit(LexerItem.Text)
#                             else:
#                                 lexer.emit(LexerItem.Link if lexer.data.is_link else LexerItem.Source)
#
#                             lexer.forward(2)
#                             lexer.emit(LexerItem.InnerMeta)
#                             return lex_setter if lexer.data.is_link else lex_image_link
#
#                         case ']':
#                             lexer.depth -= 1
#                             lexer.backup()
#
#                             if delim == Delimiter.RTL:
#                                 lexer.emit(LexerItem.Text)
#                             else:
#                                 lexer.emit(LexerItem.Link if lexer.data.is_link else LexerItem.Source)
#
#                             lexer.forward(2)
#                             lexer.emit(LexerItem.RightMeta)
#                             return None
#
#                         case _:
#                             return lexer.error(LexerItem.Error, f'malformed `{what}` markup')
#
#                 break
#
#
# def lex_image_link(lexer: Lexer) -> Callable[[Lexer], ...] | None:
#     what: str = "link" if lexer.data.is_link else "image"
#
#     while True:
#         match lexer.next():
#             case Lexer.EOF | '\n':
#                 return lexer.error(LexerItem.Error, f'unterminated `{what}` markup')
#
#             # This is not entirely reliable within sections that allow raw strings, since
#             # it's possible, however unlikely, for a raw string to contain unpaired double
#             # quotes.  The likelihood is low enough, however, that I'm deeming the risk as
#             # acceptable—for now, at least.
#             case '"':
#                 if slurp_quote(lexer, '"') == Lexer.EOF:
#                     return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{what}` markup link compnent')
#                 break
#
#             case '[':
#                 lexer.depth += 1
#                 break
#
#             case ']':
#                 lexer.depth -= 1
#
#                 if lexer.depth == 1:
#                     match lexer.peek():
#                         case '[':
#                             lexer.depth += 1
#                             lexer.backup()
#                             lexer.emit(LexerItem.Link)
#                             lexer.forward(2)
#                             lexer.emit(LexerItem.InnerMeta)
#                             return lex_setter
#
#                         case ']':
#                             lexer.depth -= 1
#                             lexer.backup()
#                             lexer.emit(LexerItem.Link)
#                             lexer.forward(2)
#                             lexer.emit(LexerItem.RightMeta)
#                             return None
#
#                         case _:
#                             return lexer.error(LexerItem.Error, f'malformed `{what}` markup')
#
#                 break
#
#
# def lex_setter(lexer: Lexer) -> Callable[[Lexer], ...] | None:
#     type_: str = "link" if lexer.data.is_link else "image"
#
#     while True:
#         match lexer.next():
#             case Lexer.EOF | '\n':
#                 return lexer.error(LexerItem.Error, f'unterminated `{type_}` markup')
#
#             case '"':
#                 if slurp_quote(lexer, '"') == Lexer.EOF:
#                     return lexer.error(LexerItem.Error, f'unterminated double quoted string in `{type_}` markup setter component')
#                 break
#
#             case "'":
#                 if slurp_quote(lexer, "'") == Lexer.EOF:
#                     return lexer.error(LexerItem.Error, f'unterminated single quoted string in `{type_}` markup setter component')
#                 break
#
#             case "[":
#                 lexer.depth += 1
#                 break
#
#             case ']':
#                 lexer.depth -= 1
#                 if lexer.depth == 1:
#                     if lexer.peek() != ']':
#                         return lexer.error(LexerItem.Error, f'malformed `{type_}` markup')
#
#                     lexer.depth -= 1
#                     lexer.backup()
#                     lexer.emit(LexerItem.Setter)
#                     lexer.forward(2)
#                     lexer.emit(LexerItem.RightMeta)
#                     return None
#
#                 break
#
#
# def parse_square_bracketed_markup(w: Wikifier):
#     # Initialize the lexer.
#     lexer = Lexer(w.source, lex_left_meta)
#
#     # Set the initial positions within the source string.
#     lexer.start = lexer.pos = w.match_start
#
#     # Lex the raw argument string.
#     markup = {}
#     items: list[LexerItemModel] = lexer.run()
#     last: LexerItemModel = items[-1]
#
#     if last and last.type_ == LexerItem.Error:
#         markup["error"] = last.message
#     else:
#         for item in items:
#             text: str = item.text.strip()
#
#             match item.type_:
#                 case LexerItem.ImageMeta:
#                     markup["isImage"] = True
#
#                     if text[1] == '<':
#                         markup["align"] = "left"
#                     elif text[1] == '>':
#                         markup["align"] = "right"
#                     break
#
#                 case LexerItem.LinkMeta:
#                     markup["isLink"] = True
#                     break
#
#                 case LexerItem.Link:
#                     if text[0] == '~':
#                         markup["forceInternal"] = True
#                         markup["link"] = text[1:]
#                     else:
#                         markup["link"] = text
#                     break
#
#                 case LexerItem.Setter:
#                     markup["setter"] = text
#                     break
#
#                 case LexerItem.Source:
#                     markup["source"] = text
#                     break
#
#                 case LexerItem.Text:
#                     markup["text"] = text
#                     break
#
#
#     markup["pos"] = lexer.pos
#     return markup
