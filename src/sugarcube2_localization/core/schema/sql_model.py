from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship


class BaseTable(DeclarativeBase): ...


class PassageModelTable(BaseTable):
    __tablename__ = 'passage'

    id: Mapped[int] = mapped_column(primary_key=True)

    filepath: Mapped[str] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(nullable=True)
    tag: Mapped[str] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column(nullable=True)
    length: Mapped[int] = mapped_column(nullable=True)
    widgets: Mapped[list] = mapped_column(JSON, nullable=True)


class WidgetModelTable(BaseTable):
    __tablename__ = 'widget'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(nullable=True)
    # args: Mapped[list]
    body: Mapped[str] = mapped_column(nullable=True)
    pos_start: Mapped[int] = mapped_column(nullable=True)
    pos_end: Mapped[int] = mapped_column(nullable=True)
    length: Mapped[int] = mapped_column(nullable=True)

    passage: Mapped[str] = mapped_column(nullable=True)


class ElementModelTable(BaseTable):
    __tablename__ = 'element'

    id: Mapped[int] = mapped_column(primary_key=True)

    filepath: Mapped[str] = mapped_column(nullable=True)
    passage: Mapped[str] = mapped_column(nullable=True)
    widget: Mapped[str] = mapped_column(nullable=True)
    block: Mapped[str] = mapped_column(nullable=True)
    block_name: Mapped[str] = mapped_column(nullable=True)
    block_semantic_key: Mapped[str] = mapped_column(nullable=True)
    block_semantic_key_hash: Mapped[str] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column(nullable=True)
    arguments: Mapped[str] = mapped_column(nullable=True)
    pos_start: Mapped[int] = mapped_column(nullable=True)
    pos_end: Mapped[int] = mapped_column(nullable=True)
    length: Mapped[int] = mapped_column(nullable=True)
    level: Mapped[int] = mapped_column(nullable=True)


__all__ = [
    "BaseTable",
    "PassageModelTable",
    "WidgetModelTable",
    "ElementModelTable",
]