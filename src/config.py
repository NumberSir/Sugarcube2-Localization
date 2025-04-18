from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ProjectSettings(BaseSettings):
    """About this project"""
    model_config = SettingsConfigDict(env_prefix="PROJECT_")

    name: str = Field(default="SugarCube2-Localization")
    log_format: str = Field(default="<g>{time:HH:mm:ss}</g> | [<lvl>{level}</lvl>] | {message}")


class FileSettings(BaseSettings):
    """About files / directories"""
    model_config = SettingsConfigDict(env_prefix="PATH_")

    root: Path = Field(default=Path(__file__).parent.parent)
    data: Path = Field(default=Path("data"))
    resource: Path = Field(default=Path("resource"))
    tmp: Path = Field(default=Path("data/tmp"))
    paratranz: Path = Field(default=Path("data/paratranz"))
    repo: Path = Field(default=Path("repositories"))  # hard coded


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
    file: FileSettings = FileSettings()


settings = Settings()

__all__ = [
    "Settings",
    "settings",
    "DefaultGames",
]

if __name__ == '__main__':
    from pprint import pprint

    pprint(Settings().model_dump())
