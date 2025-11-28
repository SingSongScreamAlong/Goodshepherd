"""Database configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSettings:
    """Runtime configuration for the SQL database layer."""

    url: str
    echo: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        # Check for dev mode (SQLite) first
        dev_mode = os.getenv("DEV_MODE", "false").lower() in {"1", "true", "yes"}
        
        if dev_mode:
            # Use SQLite for development without Docker
            db_path = Path(os.getenv("SQLITE_PATH", "./data/goodshepherd.db"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite+aiosqlite:///{db_path}"
        else:
            url = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://goodshepherd:goodshepherd@localhost:5432/goodshepherd",
            )
        
        echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() in {"1", "true", "yes"}
        return cls(url=url, echo=echo)
