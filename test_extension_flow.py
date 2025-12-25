import asyncio
import os
import uuid
import datetime
import jwt
from dotenv import load_dotenv
from starlette.testclient import TestClient
from src.legendary_potato.app.main import app
from src.legendary_potato.core.config import app_config

# Load environment variables
load_dotenv()

def generate_test_token(user_id: str) -> str:
    """Generates a valid JWT for the test user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "iss": app_config.api_jwt_issuer,
        "sub": user_id,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=app_config.api_jwt_ttl_seconds),
        "typ": "access",
    }
    return jwt.encode(payload, app_config.api_jwt_secret, algorithm="HS256")

def run_test():
    # 1. Create a fake user ID (we'll need to insert this user into the DB first for FK constraints if the app checks existence,
    #    but let's see if the 'bookmarks' endpoint requires the user to exist in the 'users' table. 
    #    Looking at db.py, 'create_bookmark' takes a user_id. 
    #    The SQL has a FK constraint usually. 
    #    So we should insert the user first.
    
    # Actually, we can use the app's internal logic to create a user if we want, or just insert directly.
    # Since we are using TestClient, we are interacting with the running app (or rather, an instance of it).
    # To properly test, we should probably insert a user into the DB.
    pass

async def async_setup_and_test():
    # We need to manually insert a user because the auth flow is what usually creates them.
    # We can use the 'Db' class directly.
    from src.legendary_potato.core.db import create_db
    
    db = await create_db(app_config.database_url)
    
    user_id = uuid.uuid4()
    identity_id = uuid.uuid4()
    provider_subject = f"test_sub_{uuid.uuid4().hex[:8]}"
    
    print(f"Creating test user {user_id}...")
    
    async with db.pool.acquire() as conn:
        # Check if user exists (unlikely given uuid4)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)
        # We might not need an identity for the bookmark test, but it's good practice
        await conn.execute(
            """
            INSERT INTO user_identities (id, user_id, provider, provider_subject, email, name)
            VALUES ($1, $2, 'test_provider', $3, 'test@example.com', 'Test User')
            """,
            identity_id, user_id, provider_subject
        )
    
    await db.pool.close()
    
    # Now generate the token
    token = generate_test_token(str(user_id))
    print(f"Generated token: {token[:10]}...")
    
    # Define the bookmark payload (mimicking what popup.js sends)
    bookmark_payload = {
        "url": f"https://example.com/test-page-{uuid.uuid4().hex[:6]}",
        "title": "Test Page Title",
        "html": "<html><body><h1>Hello World</h1></body></html>"
    }
    
    # Use TestClient as a context manager to trigger lifespan (DB init)
    with TestClient(app) as client:
        print("Sending bookmark...")
        response = client.post(
            "/bookmarks",
            json=bookmark_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ Bookmark saved successfully!")
            print("Response:", response.json())
            
            # Verify it's in the list
            print("Verifying via list endpoint...")
            list_resp = client.get(
                "/bookmarks",
                headers={"Authorization": f"Bearer {token}"}
            )
            bookmarks_list = list_resp.json().get("bookmarks", [])
            found = any(b["url"] == bookmark_payload["url"] for b in bookmarks_list)
            if found:
                print("✅ Bookmark found in list!")
            else:
                print("❌ Bookmark NOT found in list.")
                print("List response:", list_resp.json())
                
        else:
            print(f"❌ Failed to save bookmark. Status: {response.status_code}")
            print("Response:", response.text)

if __name__ == "__main__":
    asyncio.run(async_setup_and_test())
