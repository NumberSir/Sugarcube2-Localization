from pathlib import Path
from typing import Iterator

from sugarcube2_localization.exceptions import GameRootNotExistException
from sugarcube2_localization.core.parser.internal import Parser
from sugarcube2_localization.core.utils import get_all_filepaths


class JavaScriptParser(Parser):
    def get_all_filepaths(self) -> Iterator[Path]:
        """Get all javascript absolute filepaths."""
        if not self.game_root.exists():
            raise GameRootNotExistException
        return get_all_filepaths(".js", self.game_root)


__all__ = [
    "JavaScriptParser",
]


if __name__ == '__main__':
    import dukpy
    from pprint import pprint
    from sugarcube2_localization.config import DIR_REPOSITORY

    with open(DIR_REPOSITORY / "sugarcube-2" / "src/lib/patterns.js", "r", encoding="utf-8") as fp:
        js_data = fp.read()
    result = dukpy.evaljs(js_data)
    pprint(result)
