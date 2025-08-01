from pathlib import Path

from pydantic import BaseModel, Field


class _BaseModelExtraAllowed(BaseModel, extra="allow"): ...


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


__all__ = [
    "WidgetModel",
    "PassageModel",
    "ElementModel",
]
