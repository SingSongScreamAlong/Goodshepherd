"""Database configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    """Runtime configuration for the SQL database layer."""

    url: str
    echo: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://goodshepherd:goodshepherd@localhost:5432/goodshepherd",
        )
        echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() in {"1", "true", "yes"}
        return cls(url=url, echo=echo)
