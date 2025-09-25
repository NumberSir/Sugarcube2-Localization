from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings
from src.config import DIR_DATABASE


DATABASE = create_async_engine(f'sqlite+aiosqlite:///{DIR_DATABASE}')


__all__ = [
    "DATABASE"
]