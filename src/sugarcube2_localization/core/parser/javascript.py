import dukpy

from sqlalchemy.orm import Session
from pathlib import Path
from typing import Iterator

from sugarcube2_localization.config import DIR_DATA
from sugarcube2_localization.database import ENGINE
from sugarcube2_localization.exceptions import GameRootNotExistException
from sugarcube2_localization.log import logger

from sugarcube2_localization.core.parser.internal import Parser
from sugarcube2_localization.core.utils import get_all_filepaths
from sugarcube2_localization.core.schema.data_model import AcornParserOptions, NodeModel
from sugarcube2_localization.core.schema.sql_model import NodeModelTable


class JavaScriptParser(Parser):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self._logger = logger.bind(project_name="JSP")

		self._interpreter: dukpy.JSInterpreter = dukpy.JSInterpreter()
		self._parser_options: AcornParserOptions | None = None

		self._suffix = ".js"

		"""All filepaths with suffix '.twee'"""
		self._all_filepaths: list[Path] = None

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
		"""Get all twinescript absolute filepaths."""
		if not self.game_root.exists():
			self.logger.error(f"Game root does not exist: {self.game_root}")
			raise GameRootNotExistException
		self.all_filepaths = get_all_filepaths(self.suffix, self.game_root)
		return self.all_filepaths

	def tokenize(self) -> ...:
		all_filepaths = self.all_filepaths or self.get_all_filepaths()
		all_token_info: list[NodeModel] = []
		for filepath in all_filepaths:
			all_token_info = self._tokenize(filepath, all_token_info)

		with Session(ENGINE) as session:
			session.add_all(
				NodeModelTable(
					filepath=node_model.filepath.__str__(),
					type=node_model.type,
					body=node_model.body,
					pos_start=node_model.pos_start,
					pos_end=node_model.pos_end,
					length=node_model.length,
				)
				for node_model in all_token_info
			)
			session.commit()

	def _tokenize(self, filepath: Path, all_token_info: list[NodeModel]) -> list[NodeModel]:
		with filepath.open("r", encoding="utf-8") as fp:
			js_code = fp.read()

		# language=JavaScript
		tokenizer = \
		"""
		var acorn = require('acorn');
		var options = Object.assign({}, dukpy['options']);
		function tokenize() {
			try {
				return acorn.parse(dukpy['js_code'], options);
			} catch (e) {
				return Object.assign({error: true}, e);
			}
		}
		
		tokenize();
		"""

		result = self.interpreter.evaljs(
			code=tokenizer,
			js_code=js_code,
            options=self.parser_options.model_dump()
		)

		if "error" in result:
			self.logger.bind(filepath=filepath).warning(f"Tokenization error")
			return all_token_info

		if not result or "body" not in result:
			self.logger.bind(filepath=filepath).warning("No root node")
			return all_token_info

		all_token_info.extend([
			NodeModel(
				filepath=filepath.relative_to(self.game_root),
				type=node["type"],
				body=js_code[node["start"]:node["end"]],
				pos_start=node["start"],
				pos_end=node["end"],
				length=node["end"]-node["start"]
			)
			for node in result["body"]
		])
		return all_token_info

	""" Getters & Setters """

	@property
	def interpreter(self) -> dukpy.JSInterpreter:
		return self._interpreter

	@property
	def parser_options(self) -> AcornParserOptions:
		return self._parser_options

	@parser_options.setter
	def parser_options(self, _: AcornParserOptions):
		self._parser_options = _

	@property
	def suffix(self) -> str:
		return self._suffix

	@property
	def all_filepaths(self) -> list[Path]:
		return self._all_filepaths

	@all_filepaths.setter
	def all_filepaths(self, filepaths: list[Path]) -> None:
		self._all_filepaths = filepaths


__all__ = [
	"JavaScriptParser",
]


if __name__ == '__main__':
	parser = JavaScriptParser()
	parser.tokenize()
