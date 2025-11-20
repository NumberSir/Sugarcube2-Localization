from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ProjectSettings(BaseSettings):
    """About this project"""
    model_config = SettingsConfigDict(env_prefix="PROJECT_")

    name: str = Field(default="Sugarcube2-Localization")
    version: str = Field(default="0.0.1")
    username: str = Field(default="Anonymous")
    email: str = Field(default="anonymous@email.com")
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="<g>{time:HH:mm:ss}</g> | [<lvl>{level:^7}</lvl>] | {extra[project_name]}{message:<35}"
    )

    @property
    def user_agent(self) -> str:
        return (
            f"{self.username}/"
            f"{self.name}/"
            f"{self.version} "
            f"({self.email})"
        )


class FilepathSettings(BaseSettings):
    """About files / directories"""
    model_config = SettingsConfigDict(env_prefix="PATH_")

    root: Path = Field(default=Path(__file__).parent.parent.parent)
    data: Path = Field(default=Path("data"))
    log: Path = Field(default=Path("data/log"))
    database: Path = Field(default=Path("data/database"))
    paratranz: Path = Field(default=Path("data/paratranz"))
    repo: Path = Field(default=Path("repositories"))  # hard coded
    resources: Path = Field(default=Path("resources"))
    tmp: Path = Field(default=Path("data/tmp"))


class DefaultGames(Enum):
    degrees_of_lewdity = "degrees-of-lewdity"
    degrees_of_lewdity_plus = "degrees-of-lewdity-plus"


class GitHubSettings(BaseSettings):
    """About GitHub"""
    model_config = SettingsConfigDict(env_prefix='GITHUB_')

    access_token: str = Field(default=None)


class ParatranzSettings(BaseSettings):
    """About Paratranz"""
    model_config = SettingsConfigDict(env_prefix='PARATRANZ_')

    project_id: int = Field(default=None)
    token: str = Field(default=None)


class Settings(BaseSettings):
    """Main settings"""
    paratranz: ParatranzSettings = ParatranzSettings()
    github: GitHubSettings = GitHubSettings()
    project: ProjectSettings = ProjectSettings()
    filepath: FilepathSettings = FilepathSettings()


settings = Settings()
DIR_ROOT = settings.filepath.root
DIR_DATA = DIR_ROOT / settings.filepath.data
DIR_LOG = DIR_ROOT / settings.filepath.log
DIR_DATABASE = DIR_ROOT / settings.filepath.database
DIR_RESOURCES = DIR_ROOT / settings.filepath.resources
DIR_REPOSITORY = DIR_ROOT / settings.filepath.repo
DIR_TMP = DIR_ROOT / settings.filepath.tmp
DIR_DOL = DIR_REPOSITORY / DefaultGames.degrees_of_lewdity.value
DIR_DOLP = DIR_REPOSITORY / DefaultGames.degrees_of_lewdity_plus.value

__all__ = [
    "Settings",
    "settings",
    "DefaultGames",

    "DIR_ROOT",
    "DIR_DATA",
    "DIR_LOG",
    "DIR_DATABASE",
    "DIR_RESOURCES",
    "DIR_REPOSITORY",
    "DIR_TMP",

    "DIR_DOL",
    "DIR_DOLP",
]

if __name__ == '__main__':
    from pprint import pprint

    pprint(Settings().model_dump())
