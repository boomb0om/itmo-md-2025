from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")


class MongoSettings(BaseSettings):
    """MongoDB connection settings"""
    host: str = "mongodb"
    port: int = 27017
    username: str = "admin"
    password: str = "admin"
    database: str = "crypto_data"
    auth_source: str = "admin"
    
    @property
    def url(self) -> str:
        return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MONGO_")


class BinanceSettings(BaseSettings):
    """Binance API settings"""
    base_url: str = "https://api.binance.com/api/v3"
    timeout: float = 30.0
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BINANCE_")


class NewsSettings(BaseSettings):
    """News API settings"""
    cryptopanic_api_key: str = ""
    rss_urls: list[str] = [
        "https://cryptopanic.com/api/v1/posts/?auth_token={token}&public=true",
    ]
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NEWS_")


# Global settings instances
app_settings = AppSettings()
mongo_settings = MongoSettings()
binance_settings = BinanceSettings()
news_settings = NewsSettings()

