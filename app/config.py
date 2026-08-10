"""CP1 - Cau hinh theo 12-Factor.

Nguyen tac: khong co gia tri cau hinh nao nam trong code. Tat ca den tu
bien moi truong, de cung mot image chay duoc o laptop, staging va
production ma khong phai sua mot dong code nao.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toan bo cau hinh cua service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = 8000
    api_token: str
    redis_url: str = "redis://localhost:6379/0"
    bucket_capacity: int = 10
    refill_per_minute: int = 10
    daily_budget_usd: float = 1.0
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Doc cau hinh mot lan roi cache lai."""
    return Settings()
