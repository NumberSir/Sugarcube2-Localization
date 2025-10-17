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
from typing import Iterator

from sugarcube2_localization.config import DIR_DOL


class Parser:
    def __init__(self, game_root: Path = DIR_DOL):
        self._game_root: Path = game_root       # Root path for the game needed to be localized, DoL as default

    @staticmethod
    def clean(*filepaths: Path):
        for fp in filepaths:
            with suppress(FileNotFoundError):
                shutil.rmtree(fp)
            os.makedirs(fp, exist_ok=True)

    def get_all_filepaths(self) -> Iterator[Path]:
        raise NotImplementedError

    @property
    def game_root(self) -> Path:
        return self._game_root


__all__ = [
    "Parser",
]
