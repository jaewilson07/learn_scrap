import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg

from .config import app_config
from .migrations import MigrationRunner

__all__ = ["Db", "create_db"]


def _hash_refresh_token(token: str) -> str:
    if not app_config.api_jwt_secret:
        raise RuntimeError("API_JWT_SECRET is not configured")
    # Bind hash to server secret so DB leaks are less useful.
    h = hashlib.sha256()
    h.update(app_config.api_jwt_secret.encode("utf-8"))
    h.update(b":")
    h.update(token.encode("utf-8"))
    return h.hexdigest()


@dataclass(frozen=True)
class Db:
    pool: asyncpg.Pool

    async def migrate(self, *, migrations_dir: Path) -> list[str]:
        async with self.pool.acquire() as conn:
            runner = MigrationRunner(migrations_dir=migrations_dir)
            return await runner.apply(conn)

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

    async def get_identities(self, *, user_id: uuid.UUID) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT provider, provider_subject, email, name, avatar_url, created_at
                FROM user_identities
                WHERE user_id = $1
                ORDER BY created_at ASC
                """,
                user_id,
            )
        return [dict(r) for r in rows]

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

    async def issue_refresh_token(self, *, user_id: uuid.UUID) -> str:
        token = secrets.token_urlsafe(48)
        token_hash = _hash_refresh_token(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=int(app_config.refresh_token_ttl_seconds))
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
                VALUES ($1, $2, $3, $4)
                """,
                uuid.uuid4(),
                user_id,
                token_hash,
                expires_at,
            )
        return token

    async def rotate_refresh_token(self, *, refresh_token: str) -> tuple[uuid.UUID, str]:
        token_hash = _hash_refresh_token(refresh_token)
        now = datetime.now(timezone.utc)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, expires_at, revoked_at
                    FROM refresh_tokens
                    WHERE token_hash = $1
                    """,
                    token_hash,
                )
                if not row:
                    raise ValueError("Invalid refresh token")
                if row["revoked_at"] is not None:
                    raise ValueError("Refresh token revoked")
                if row["expires_at"] <= now:
                    raise ValueError("Refresh token expired")

                await conn.execute(
                    """
                    UPDATE refresh_tokens
                    SET last_used_at = $2, revoked_at = $2
                    WHERE id = $1
                    """,
                    row["id"],
                    now,
                )

        user_id = uuid.UUID(str(row["user_id"]))
        new_token = await self.issue_refresh_token(user_id=user_id)
        return user_id, new_token

    async def revoke_refresh_tokens_for_user(self, *, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            res = await conn.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = $2
                WHERE user_id = $1 AND revoked_at IS NULL
                """,
                user_id,
                now,
            )
        # asyncpg returns strings like "UPDATE 3"
        return int(res.split()[-1]) if res else 0


async def create_db(database_url: str) -> Db:
    pool = await asyncpg.create_pool(dsn=database_url, statement_cache_size=0)
    return Db(pool=pool)

