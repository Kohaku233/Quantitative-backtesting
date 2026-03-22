from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Crypto Quantitative Backtesting Platform"
    api_prefix: str = "/api"
    database_filename: str = "quantitative_backtesting.duckdb"


@lru_cache
def get_settings() -> Settings:
    return Settings()
