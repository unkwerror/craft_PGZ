# core/config.py (полная модернизация)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class DatabaseSettings(BaseSettings):
    url: str = Field(default="sqlite:///./tender_analyzer.db")
    echo: bool = Field(default=False)
    model_config = SettingsConfigDict(env_prefix="DB_", case_sensitive=False)

class ParserSettings(BaseSettings):
    base_url: str = "https://zakupki.gov.ru"
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    model_config = SettingsConfigDict(env_prefix="PARSER_", case_sensitive=False)

class CacheSettings(BaseSettings):
    redis_url: str = Field(default="redis://localhost:6379/0")
    default_ttl: int = 3600
    search_results_ttl: int = 1800
    model_config = SettingsConfigDict(env_prefix="CACHE_", case_sensitive=False)

class FileStorageSettings(BaseSettings):
    base_dir: Path = Field(default=Path("./data"))
    documents_dir: str = "documents"
    reports_dir: str = "reports"
    exports_dir: str = "exports"
    max_file_size_mb: int = 50
    model_config = SettingsConfigDict(env_prefix="FILES_", case_sensitive=False)

class AppSettings(BaseSettings):
    app_name: str = "Tender Analyzer"
    version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")

    database: DatabaseSettings = DatabaseSettings()
    parser: ParserSettings = ParserSettings()
    cache: CacheSettings = CacheSettings()
    files: FileStorageSettings = FileStorageSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

settings = AppSettings()

def get_settings() -> AppSettings:
    return settings
