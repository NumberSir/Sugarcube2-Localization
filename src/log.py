"""Output infos during running."""
import datetime
import sys

from loguru import logger as logger_

from src.config import settings

DIR_LOGS = settings.filepath.root / settings.filepath.log
DIR_LOGS.mkdir(parents=True, exist_ok=True)


def add_project_name(record):
    if record["extra"].get("project_name", False):
        record["extra"]["project_name"] = f"[{record['extra']['project_name']}] | "
    else:
        record["extra"]["project_name"] = ""


def add_filepath(record):
    if record["extra"].get("filepath", False):
        record["extra"]["filepath"] = f" | {record['extra']['filepath']}"
    else:
        record["extra"]["filepath"] = ""


logger_.remove()
logger_ = logger_.patch(add_project_name)
logger_ = logger_.patch(add_filepath)

NOW = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
FORMAT = settings.project.log_format
logger_.add(sink=sys.stdout, format=FORMAT, colorize=True, level=settings.project.log_level)
logger_.add(sink=DIR_LOGS / f"{NOW}.log", format=FORMAT, colorize=False, level="INFO", encoding="utf-8")
logger_.add(sink=DIR_LOGS / f"{NOW}.debug", format=FORMAT, colorize=False, level="DEBUG", encoding="utf-8")
logger = logger_


__all__ = [
    "logger"
]
