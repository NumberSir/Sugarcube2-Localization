import os

from pathlib import Path

from src.core.parser.internal import Parser


class JavaScriptParser(Parser):
    def get_all_filepaths(self) -> list[Path]:
        return [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".js")
        ]


__all__ = [
    "JavaScriptParser",
]