from pathlib import Path
from typing import Iterator

from src.core.schema.model import JSSyntaxErrorModel


def get_all_filepaths(suffix: str, directory: Path) -> Iterator[Path]:
    """
    Get all specified absolute filepaths.

    Parameters
    ----------
    suffix : str
        File suffix needed.
    directory : Path
        Directory to get files from.

    Returns
    -------
    Iterator[Path]
        All filepaths in given directory with given suffix.

    """
    return directory.glob(f"**/*{suffix}")


def traceback_detail(js_code: str, error: JSSyntaxErrorModel) -> tuple[str, str]:
    """
    Javascript traceback details.

    Parameters
    ----------
    js_code : str
        Javascript code which has errors.
    error : JSSyntaxErrorModel
        Model contains error location / position.

    Returns
    -------
    tuple[str, str]
        Javascript traceback details, including the error line and an indicator.
    """
    return (
        f"{js_code.splitlines()[error.loc.line-1]}".rstrip('\n'),
        f"{'^': >{error.loc.column+1}}"
    )


# def eval_javascript(js_code: str, js_output: str=None, js_options: dict=None):
#     """Evaluates the given JavaScript code and returns the result, throwing if there were errors."""
#     # language=JavaScript
#     function = \
#     """
#     function evalJavaScript(code, output, data) {
# 		return (function (code, output, SCRIPT$DATA$) {
# 			return eval(code);
# 		}).call(output ? { output } : null, String(code), output, data);
# 	}
#     evalJavaScript(dukpy['js_code'], dukpy['js_output'], dukpy['js_options'])
#     """
#     return dukpy.JSInterpreter().evaljs(code=function, js_code=js_code, js_output=js_output, js_options=js_options)


# def eval_twinescript(js_code: str, js_output: str=None, js_options: dict=None):
#     """
#     WARNING: Do not use a dollar sign or underscore as the first character of the
#     data variable, `SCRIPT$DATA$`, as `desugar()` will break references to it within
#     the code string.
#     """
#     # language=JavaScript
#     function = \
#     r"""
#     const desugar = (() => {
# 		const tokenTable = new Map([
# 			// Story $variable sigil-prefix.
# 			['$',     'State.variables.'],
# 			// Temporary _variable sigil-prefix.
# 			['_',     'State.temporary.'],
# 			// Assignment operator.
# 			['to',    '='],
# 			// Equality operators.
# 			['eq',    '=='],
# 			['neq',   '!='],
# 			['is',    '==='],
# 			['isnot', '!=='],
# 			// Relational operators.
# 			['gt',    '>'],
# 			['gte',   '>='],
# 			['lt',    '<'],
# 			['lte',   '<='],
# 			// Logical operators.
# 			['and',   '&&'],
# 			['or',    '||'],
# 			// Unary operators.
# 			['not',   '!'],
# 			['def',   '"undefined" !== typeof'],
# 			['ndef',  '"undefined" === typeof']
# 		]);
# 		const desugarRE = new RegExp([
# 			'(?:""|\'\'|``)',                                     //   Empty quotes (incl. template literal)
# 			'(?:"(?:\\\\.|[^"\\\\])+")',                          //   Double quoted, non-empty
# 			"(?:'(?:\\\\.|[^'\\\\])+')",                          //   Single quoted, non-empty
# 			'(`(?:\\\\.|[^`\\\\])+`)',                            // 1=Template literal, non-empty
# 			'(?:[=+\\-*\\/%<>&\\|\\^~!?:,;\\(\\)\\[\\]{}]+)',     //   Operator characters
# 			'(?:\\.{3})',                                         //   Spread/rest syntax
# 			'([^"\'=+\\-*\\/%<>&\\|\\^~!?:,;\\(\\)\\[\\]{}\\s]+)' // 2=Barewords
# 		].join('|'), 'g');
# 		const varTest = new RegExp("^[$_=][$A-Z_a-z][$0-9A-Z_a-z]*");
#
# 		function desugar(sugaredCode) {
# 			desugarRE.lastIndex = 0;
#
# 			let code  = sugaredCode;
# 			let match;
#
# 			while ((match = desugarRE.exec(code)) !== null) {
# 				// no-op: Empty quotes, Double quoted, Single quoted, Operator characters, Spread/rest syntax
#
# 				// Template literal, non-empty.
# 				if (match[1]) {
# 					const sugaredTemplate = match[1];
# 					const template = desugarTemplate(sugaredTemplate);
#
# 					if (template !== sugaredTemplate) {
# 						code = code.splice(
# 							match.index,            // starting index
# 							sugaredTemplate.length, // replace how many
# 							template                // replacement string
# 						);
# 						desugarRE.lastIndex += template.length - sugaredTemplate.length;
# 					}
# 				}
#
# 				// Barewords.
# 				else if (match[2]) {
# 					let token = match[2];
#
# 					// If the token is simply a dollar-sign or underscore, then it's either
# 					// just the raw character or, probably, a function alias, so skip it.
# 					if (token === '$' || token === '_') {
# 						continue;
# 					}
#
# 					// If the token is a story $variable or temporary _variable, then reset
# 					// it to just its sigil for replacement.
# 					if (varTest.test(token)) {
# 						token = token[0];
# 					}
#
# 					// If the finalized token has a mapping, replace it within the code string
# 					// with its counterpart.
# 					const replacement = tokenTable.get(token);
#
# 					if (replacement) {
# 						code = code.splice(
# 							match.index,  // starting index
# 							token.length, // replace how many
# 							replacement   // replacement string
# 						);
# 						desugarRE.lastIndex += replacement.length - token.length;
# 					}
# 				}
# 			}
#
# 			return code;
# 		}
#
# 		const templateGroupStartRE = /\$\{/g;
# 		const templateGroupParseRE = new RegExp([
# 			'(?:""|\'\')',               //   Empty quotes
# 			'(?:"(?:\\\\.|[^"\\\\])+")', //   Double quoted, non-empty
# 			"(?:'(?:\\\\.|[^'\\\\])+')", //   Single quoted, non-empty
# 			'(\\{)',                     // 1=Opening curly brace
# 			'(\\})'                      // 2=Closing curly brace
# 		].join('|'), 'g');
#
# 		// WARNING: Does not currently handle nested template strings.
# 		function desugarTemplate(sugaredLiteral) {
# 			templateGroupStartRE.lastIndex = 0;
#
# 			let template   = sugaredLiteral;
# 			let startMatch;
#
# 			while ((startMatch = templateGroupStartRE.exec(template)) !== null) {
# 				const startIndex = startMatch.index + 2;
# 				let endIndex = startIndex;
# 				let depth    = 1;
# 				let endMatch;
#
# 				templateGroupParseRE.lastIndex = startIndex;
#
# 				while ((endMatch = templateGroupParseRE.exec(template)) !== null) {
# 					// Opening curly brace.
# 					if (endMatch[1]) {
# 						++depth;
# 					}
# 					// Closing curly brace.
# 					else if (endMatch[2]) {
# 						--depth;
# 					}
#
# 					if (depth === 0) {
# 						endIndex = endMatch.index;
# 						break;
# 					}
# 				}
#
# 				// If the group is not empty, replace it within the template
# 				// with its desugared counterpart.
# 				if (endIndex > startIndex) {
# 					const desugarREIndex = desugarRE.lastIndex;
# 					const sugaredGroup   = template.slice(startIndex, endIndex);
# 					const group          = desugar(sugaredGroup);
# 					desugarRE.lastIndex = desugarREIndex;
#
# 					template = template.splice(
# 						startIndex,          // starting index
# 						sugaredGroup.length, // replace how many
# 						group                // replacement string
# 					);
# 					templateGroupStartRE.lastIndex += group.length - sugaredGroup.length;
# 				}
# 			}
#
# 			return template;
# 		}
#
# 		return desugar;
# 	})();
#     function evalTwineScript(code, output, data) {
# 		return (function (code, output, SCRIPT$DATA$) {
# 			return eval(code);
# 		}).call(output ? { output } : null, desugar(String(code)), output, data);
# 	}
#     evalTwineScript(dukpy['js_code'], dukpy['js_output'], dukpy['js_options'])
#     """
#     return dukpy.JSInterpreter().evaljs(code=function, js_code=js_code, js_output=js_output, js_options=js_options)


__all__ = [
    "get_all_filepaths",
    "traceback_detail",
]
