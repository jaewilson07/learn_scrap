import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from src.legendary_potato.core.config import app_config

async def test_conn():
    load_dotenv()
    db_url = app_config.database_url
    if not db_url:
        print("DATABASE_URL not found in config")
        return

    # Redact password for output
    safe_url = db_url
    if "@" in db_url:
        parts = db_url.split("@")
        protocol_user = parts[0].split(":")
        if len(protocol_user) > 2: # has password
             safe_url = f"{protocol_user[0]}:{protocol_user[1]}:***@{parts[1]}"
        else:
             safe_url = f"{parts[0]}:***@{parts[1]}"

    print(f"Attempting to connect to: {safe_url}")
    try:
        conn = await asyncpg.connect(db_url)
        print("Successfully connected to Supabase/Postgres!")
        res = await conn.fetchval("SELECT NOW()")
        print(f"Database time: {res}")
        await conn.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
