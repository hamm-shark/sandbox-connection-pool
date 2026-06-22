import functools
from pathlib import Path
from typing import TypeVar

import dotenv
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

TSettings = TypeVar("TSettings", bound=BaseSettings)


@functools.cache
def _load_dotenv_once() -> None:
    dotenv.load_dotenv()


def get_settings[TSettings](cls: type[TSettings]) -> TSettings:
    _load_dotenv_once()
    return cls()


class DataBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    USER: str = Field(default="postgres")
    PASSWORD: str = Field(default=...)
    NAME: str = Field(default="sandbox-connection-pool")
    HOST: str = Field(default="localhost")
    PORT: int = Field(default=5432)
    DRIVER: str = Field(default="psycopg")

    ECHO: bool = Field(default=False)
    TIMEOUT: int = Field(default=5)

    @property
    def dsn(self) -> str:
        return str(
            PostgresDsn.build(
                scheme=f"postgresql+{self.DRIVER}",
                username=self.USER,
                password=self.PASSWORD,
                host=self.HOST,
                port=self.PORT,
                path=self.NAME,
            ),
        )


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    DEBUG: bool = Field(default=False)

    db: DataBaseSettings = DataBaseSettings()
