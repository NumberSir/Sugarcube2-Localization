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
    name: str | None = Field(default=None)
    # args: list | None = Field(default_factory=list)  # TODO
    body: str | None = Field(default=None)
    pos_start: int = Field(default=-1)
    pos_end: int = Field(default=-1)
    length: int = Field(default=-1)

    passage: str | None = Field(default=None)


class PassageModel(_BaseModelExtraAllowed):
    """
    :: TITLE [TAG]
    BODY (LENGTH)
    """
    filepath: Path = Field(...)
    title: str | None = Field(default=None)
    tag: str | None = Field(default=None)
    body: str | None = Field(default=None)
    length: int = Field(default=-1)
    widgets: list[WidgetModel] | None = Field(default_factory=list)


# class ElementCommentModel(_BaseModelExtraAllowed):
#     content: str = Field(default="MISSING_CONTENT")


# class ElementMacroModel(_BaseModelExtraAllowed):
#     """<<name args>>"""
#     name: str = Field(default="MISSING_NAME")
#     args: str = Field(default="MISSING_ARGS")
#     is_close: bool = Field(default=False)


# class ElementTagModel(_BaseModelExtraAllowed):
#     """<name args>"""
#     name: str = Field(default="MISSING_NAME")
#     args: str = Field(default="MISSING_ARGS")
#     is_close: bool = Field(default=False)


# class ElementVariableModel(_BaseModelExtraAllowed):
#     """naked variable, starts with $ or _ """
#     display_name: str = Field(default="MISSING_DISPLAY_NAME")
#     type: str = Field(default="MISSING_TYPE")


# class ElementTextModel(_BaseModelExtraAllowed):
#     """Pure texts / Plain texts"""


class ElementModel(_BaseModelExtraAllowed):
    """Basic element constitutes each passage."""
    filepath: Path = Field(...)
    passage: str = Field(...)
    widget: str | None = Field(default=None)
    block: str | None = Field(default=None, description="该元素是否为块的首尾，否则为填充文本")
    block_name: str | None = Field(default=None, description="仅当为块首尾时，存放其名称")
    block_semantic_key: str | None = Field(default=None, description="仅当为块首尾时，存放其语义化键名")
    block_semantic_key_hash: str | None = Field(default=None, description="语义化键名散列处理，剪短储存长度")
    type: str | None = Field(default=None)
    body: str | None = Field(default=None)
    arguments: str | None = Field(default=None, description="仅当为MACRO时，存放其参数")
    # body_desugared: str = Field(default="MISSING_DESUGARED")
    pos_start: int = Field(default=-1)
    pos_end: int = Field(default=-1)
    length: int = Field(default=-1)
    level: int = Field(default=-1)
    # data: ElementCommentModel | ElementMacroModel | None = Field(default=None)


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

""" From sugarcube-2 """

# class LexerItemModel(_BaseModelExtraAllowed):
#     type_: Enum | None = Field(default=None, alias="type")
#     message: str | None = Field(default=None)
#     text: str = Field(..., )
#     start: int = Field(..., )
#     pos: int = Field(..., )


# class LexerDataModel(_BaseModelExtraAllowed):
#     is_link: bool | None = Field(default=None)


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
