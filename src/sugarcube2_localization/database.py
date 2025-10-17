from sqlalchemy import create_engine

from sugarcube2_localization.config import DIR_DATABASE

DIR_DATABASE.mkdir(parents=True, exist_ok=True)
ENGINE = create_engine(f'sqlite+pysqlite:///{DIR_DATABASE}/db.db')


__all__ = [
    "ENGINE"
]