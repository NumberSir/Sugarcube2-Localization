from sqlalchemy import create_engine

from src.config import DIR_DATABASE
from src.core.schema.sql_model import BaseTable


DIR_DATABASE.mkdir(parents=True, exist_ok=True)
ENGINE = create_engine(f'sqlite+pysqlite:///{DIR_DATABASE}/db.db')


__all__ = [
    "ENGINE"
]