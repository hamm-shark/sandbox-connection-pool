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


class ConnectionPoolSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONN_POLL_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    POOL_SIZE: int = 40
    MAX_OVERFLOW: int = 0
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 3600


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    USE_SA_CONNECTION_POOL: bool = True
    PAYMENT_FAILURE_RATE: float | int = 0.1
    DOMESTIC_FAILURE_RATE: float | int = 0.01
    SESSION_NUMBERS: list[int] = Field(default=[2, 3, 4])
    PAYMENT_DELAYS: list[float | int] = Field(default=[2, 3, 5, 9, 10])
    DOMESTIC_DELAYS: list[float | int] = Field(default=[2, 3, 5, 9, 10])
    DEFAULT_PROCESS_DELAYS: list[float | int] = Field(default=[2, 3, 5, 9, 10])

    db: DataBaseSettings = DataBaseSettings()
    conn_pool: ConnectionPoolSettings = ConnectionPoolSettings()
