from pathlib import Path
from typing import Iterator

from sugarcube2_localization.config import DIR_DOL


class Reviewer:
    def __init__(self, game_root: Path = DIR_DOL, **kwargs):
        self._game_root: Path = game_root       # Root path for the game needed to be localized, DoL as default
        self._all_filepaths: Iterator[Path] | None = None    # Absolute paths for all the files

    def validate_basic_syntax(self) -> bool:
        """Check whether the basic syntax is correct."""
        raise NotImplementedError

    @property
    def game_root(self) -> Path:
        return self._game_root

    @property
    def all_filepaths(self) -> Iterator[Path]:
        return self._all_filepaths

    @all_filepaths.setter
    def all_filepaths(self, fps: Iterator[Path]) -> None:
        self._all_filepaths = fps


__all__ = [
    "Reviewer",
]
