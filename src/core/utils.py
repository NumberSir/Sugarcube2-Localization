from pathlib import Path
from typing import Iterator

from src.core.schema.model import JSSyntaxErrorModel


def get_all_filepaths(suffix: str, directory: Path) -> Iterator[Path]:
    """Get all specified absolute filepaths."""
    return directory.glob(f"**/*{suffix}")


def traceback_detail(js_code: str, error: JSSyntaxErrorModel) -> tuple[str, str]:
    """Javascript traceback details."""
    return (
        f"{js_code.splitlines()[error.loc.line-1]}".rstrip('\n'),
        f"{'^': >{error.loc.column+1}}"
    )

__all__ = [
    "get_all_filepaths",
    "traceback_detail",
]
