"""
1. Twine
1.1. 获取文件绝对路径 (按文件进行一级分割)
1.2. 获取段落信息 (按段落进行二级分割)
1.3. 获取基础元素信息 (comment, head, macro, tag, script, 剩下的就是 plain text)
1.4. ？将元素组合？
1.5. 修改为可导入 paratranz 的格式
1.6. 导出为 json 文件
"""

import os
import shutil

from contextlib import suppress
from pathlib import Path

from src.config import DIR_DOL
from src.log import logger


class Parser:
    def __init__(self, game_root: Path = DIR_DOL):
        self._game_root: Path = game_root       # 需要汉化的游戏内容根目录，默认 DoL | Root path for the game needed to be localized, DoL as default
        self._all_filepaths: list[Path] = []    # 所有文件绝对路径 | Absolute paths for all the files
        logger.debug(f"Game root: {self._game_root}")

    @staticmethod
    def clean(*filepaths: Path):
        for fp in filepaths:
            with suppress(FileNotFoundError):
                shutil.rmtree(fp)
            os.makedirs(fp, exist_ok=True)

    def get_all_filepaths(self) -> list[Path]:
        raise NotImplementedError

    @property
    def game_root(self) -> Path:
        return self._game_root

    @property
    def all_filepaths(self) -> list[Path]:
        return self._all_filepaths

    @all_filepaths.setter
    def all_filepaths(self, fps: list[Path]) -> None:
        self._all_filepaths = fps


__all__ = [
    "Parser",
]
