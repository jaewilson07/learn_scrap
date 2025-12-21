import uuid
from dataclasses import dataclass

import asyncpg

__all__ = ["Db", "create_db"]


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_identities (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider text NOT NULL,
  provider_subject text NOT NULL,
  email text NULL,
  name text NULL,
  avatar_url text NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(provider, provider_subject)
);

CREATE TABLE IF NOT EXISTS bookmarks (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  url text NOT NULL,
  title text NULL,
  html text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_user_created_at
  ON bookmarks(user_id, created_at DESC);
"""


@dataclass(frozen=True)
class Db:
    pool: asyncpg.Pool

    async def init_schema(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)

    async def get_or_create_user_id_for_identity(
        self,
        *,
        provider: str,
        provider_subject: str,
        email: str | None,
        name: str | None,
        avatar_url: str | None,
    ) -> uuid.UUID:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT user_id
                    FROM user_identities
                    WHERE provider = $1 AND provider_subject = $2
                    """,
                    provider,
                    provider_subject,
                )
                if row and row["user_id"]:
                    return uuid.UUID(str(row["user_id"]))

                user_id = uuid.uuid4()
                identity_id = uuid.uuid4()
                await conn.execute(
                    "INSERT INTO users (id) VALUES ($1)",
                    user_id,
                )
                await conn.execute(
                    """
                    INSERT INTO user_identities
                      (id, user_id, provider, provider_subject, email, name, avatar_url)
                    VALUES
                      ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    identity_id,
                    user_id,
                    provider,
                    provider_subject,
                    email,
                    name,
                    avatar_url,
                )
                return user_id

    async def create_bookmark(
        self,
        *,
        user_id: uuid.UUID,
        url: str,
        title: str | None,
        html: str | None,
    ) -> uuid.UUID:
        bookmark_id = uuid.uuid4()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO bookmarks (id, user_id, url, title, html)
                VALUES ($1, $2, $3, $4, $5)
                """,
                bookmark_id,
                user_id,
                url,
                title,
                html,
            )
        return bookmark_id

    async def list_bookmarks(self, *, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, url, title, created_at
                FROM bookmarks
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id,
                limit,
            )
        return [dict(r) for r in rows]


async def create_db(database_url: str) -> Db:
    pool = await asyncpg.create_pool(dsn=database_url)
    return Db(pool=pool)

