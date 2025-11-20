from sqlalchemy import create_engine

from sugarcube2_localization.config import DIR_DATABASE
from sugarcube2_localization.log import logger
from sugarcube2_localization.core.schema.sql_model import BaseTable

DIR_DATABASE.mkdir(parents=True, exist_ok=True)
ENGINE = create_engine(f'sqlite+pysqlite:///{DIR_DATABASE}/db.db')
logger.info(f"Database {DIR_DATABASE}/db.db initialized")

BaseTable.metadata.drop_all(ENGINE)
BaseTable.metadata.create_all(ENGINE)


__all__ = [
    "ENGINE"
]