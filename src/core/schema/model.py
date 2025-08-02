from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class _BaseModelExtraAllowed(BaseModel, extra="allow"): ...


""" Parser """
class WidgetModel(_BaseModelExtraAllowed):
    """
    (POS_START)
    <<widget "NAME" [ARGS*]>>
    BODY (LENGTH)
    <</widget>>
    (POS_END)
    """
    name: str = Field(default="MISSING_NAME")
    args: list | None = Field(default_factory=list)  # TODO
    body: str = Field(default="MISSING_BODY")
    pos_start: int = Field(default=-1)
    pos_end: int = Field(default=-1)
    length: int = Field(default=-1)


class PassageModel(_BaseModelExtraAllowed):
    """
    :: TITLE [TAG]
    BODY (LENGTH)
    """
    filepath: Path = Field(...)
    title: str = Field(default="MISSING_TITLE")
    tag: str | None = Field(default=None)
    body: str = Field(default="MISSING_BODY")
    length: int = Field(default=-1)
    widgets: list[WidgetModel] | None = Field(default_factory=list)


class ElementModel(_BaseModelExtraAllowed):
    """Basic element constitutes each passage."""
    filepath: Path = Field(...)
    title: str = Field(default="MISSING_TITLE")
    type: str = Field(default="MISSING_TYPE")
    body: str = Field(default="MISSING_BODY")
    pos_start: int = Field(default=-1)
    pos_end: int = Field(default=-1)
    length: int = Field(default=-1)


""" Reviewer """
class AcornParserOptions(_BaseModelExtraAllowed):
    """https://github.com/acornjs/acorn/tree/master/acorn/#interface"""
    ecmaVersion: int | str = Field(
        default=2026, description=(
            "ECMA Version. "
            "Degrees-of-Lewdity use 2020 as default, "
            "while sugarcube-2 use 2022 as default, "
            "but only use 2026 could pass the syntax validation."
        )
    )
    sourceType: Literal['script', 'module', 'commonjs'] = Field(default="script")
    onInsertedSemicolon: bool | None = Field(default=None)
    onTrailingComma: bool | None = Field(default=None)
    allowReserved: bool | None = Field(default=None)
    allowReturnOutsideFunction: bool | None = Field(default=False)
    allowImportExportEverywhere: bool | None = Field(default=False)
    allowAwaitOutsideFunction: bool | None = Field(default=None)
    allowSuperOutsideMethod: bool | None = Field(default=None)
    allowHashBang: bool | None = Field(default=False)
    checkPrivateFields: bool | None = Field(default=True)
    locations: bool | None = Field(default=False)
    onToken: bool | None = Field(default=None)
    onComment: bool | None = Field(default=None)
    ranges: bool | None = Field(default=False)
    program: bool | None = Field(default=None)
    sourceFile: bool | None = Field(default=None)
    directSourceFile: bool | None = Field(default=None)
    preserveParens: bool | None = Field(default=False)


class JSSyntaxErrorModel(_BaseModelExtraAllowed):
    """Javascript syntax errors from Acorn"""
    class LocationModel(_BaseModelExtraAllowed):
        line: int = Field(...)
        column: int = Field(...)

    error: bool = Field(default=True)
    pos: int = Field(...)
    loc: LocationModel = Field(...)
    raisedAt: int = Field(...)


__all__ = [
    "WidgetModel",
    "PassageModel",
    "ElementModel",

    "AcornParserOptions",
    "JSSyntaxErrorModel",
]


if __name__ == '__main__':
    options = AcornParserOptions(ecmaVersion=2022)
    print(options.model_dump())
