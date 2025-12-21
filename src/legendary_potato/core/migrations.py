from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import asyncpg

__all__ = ["MigrationRunner"]


@dataclass(frozen=True)
class MigrationRunner:
    migrations_dir: Path

    async def apply(self, conn: asyncpg.Connection) -> list[str]:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version text PRIMARY KEY,
              applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )

        applied = {
            r["version"]
            for r in await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
        }

        files = sorted(self.migrations_dir.glob("*.sql"))
        ran: list[str] = []
        for f in files:
            version = f.name
            if version in applied:
                continue
            sql = f.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations(version) VALUES ($1)",
                    version,
                )
            ran.append(version)
        return ran

