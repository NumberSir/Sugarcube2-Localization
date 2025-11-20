import dukpy

from pathlib import Path
from typing import Iterator

from sugarcube2_localization.config import DIR_DATA
from sugarcube2_localization.log import logger
from sugarcube2_localization.exceptions import GameRootNotExistException
from sugarcube2_localization.core.reviewer.internal import Reviewer
from sugarcube2_localization.core.utils import get_all_filepaths, traceback_detail
from sugarcube2_localization.core.schema.data_model import AcornParserOptions, JSSyntaxErrorModel


class JavascriptReviewer(Reviewer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._logger = logger.bind(project_name="JSR")

        self._interpreter: dukpy.JSInterpreter = dukpy.JSInterpreter()
        self._parser_options: AcornParserOptions | None = None

        self.init_environment()

    def init_environment(self):
        """Install required JavaScript dependencies."""
        dukpy.install_jspackage(
            package_name='acorn',
            version=None,
            modulesdir=DIR_DATA / "node_modules",
        )
        self.interpreter.loader.register_path(DIR_DATA / 'node_modules' / 'acorn' / 'dist')
        self.parser_options = AcornParserOptions()

    def get_all_filepaths(self) -> Iterator[Path]:
        """Get all javascript absolute filepaths."""
        if not self.game_root.exists():
            raise GameRootNotExistException
        return get_all_filepaths(".js", self.game_root / "game")

    def validate_basic_syntax(self):
        """https://github.com/acornjs/acorn/tree/master/acorn/"""
        for filepath in self.get_all_filepaths():
            with filepath.open("r", encoding="utf-8") as fp:
                js_code = fp.read()

            # language=JavaScript
            validation = \
            """
            var acorn = require('acorn');
            var options = Object.assign({}, dukpy['options']);
            function validate() {
                try {
                    return acorn.parse(dukpy['js_code'], options);
                } catch (e) {
                    return Object.assign({error: true}, e)
                }
            }
            
            validate();
            """

            result = self.interpreter.evaljs(
	            code=validation,
	            js_code=js_code,
	            options=self.parser_options.model_dump()
            )
            if "error" not in result:  # Syntax error
                self.logger.bind(filepath=filepath).debug("JavaScript 语法无错误")
                continue

            error_msg, error_pointer = traceback_detail(js_code=js_code, error=JSSyntaxErrorModel(**result))
            self.logger.bind(filepath=filepath).error(f"JavaScript 语法有误：{result['loc']['line'], result['loc']['column']}")
            self.logger.error(error_msg)
            self.logger.error(error_pointer)

    @property
    def interpreter(self) -> dukpy.JSInterpreter:
        return self._interpreter

    @property
    def parser_options(self) -> AcornParserOptions:
        return self._parser_options

    @parser_options.setter
    def parser_options(self, _: AcornParserOptions):
        self._parser_options = _


__all__ = [
    "JavascriptReviewer"
]


if __name__ == '__main__':
    reviewer = JavascriptReviewer()
    reviewer.validate_basic_syntax()
