from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings"""

    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")


class MongoSettings(BaseSettings):
    """MongoDB connection settings"""

    host: str = Field(default="mongodb")
    port: int = Field(default=27017)
    username: str = Field(...)
    password: str = Field(...)
    database: str = Field(...)
    auth_source: str = Field(...)

    @property
    def url(self) -> str:
        """Get MongoDB connection URL"""
        return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MONGO_")


class BinanceSettings(BaseSettings):
    """Binance API settings"""

    base_url: str = Field(default="https://api.binance.com/api/v3")
    timeout: float = Field(default=30.0)
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BINANCE_")


class Settings(BaseSettings):
    """Settings"""

    app: AppSettings = Field(default_factory=AppSettings)
    mongo: MongoSettings = Field(default_factory=MongoSettings)
    binance: BinanceSettings = Field(default_factory=BinanceSettings)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance so we do not re-parse .env repeatedly."""
    return Settings()
