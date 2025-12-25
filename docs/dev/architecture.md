## Architecture overview (this branch)

### What we’re building

A **Chrome extension** that can “bookmark” the current page by sending:

- URL
- title
- full extracted HTML

to a **FastAPI backend**. The backend is responsible for:

- authenticating the user (Google OAuth today)
- authorizing access (“only this user can see their bookmarks”)
- persisting bookmarks into a Postgres database (**Supabase Postgres is treated as plain Postgres**)

### Why “Supabase as Postgres behind the API”

We intentionally treat Supabase as **storage only** (Postgres), not as:

- the auth provider (Supabase Auth/GoTrue)
- the authorization enforcement layer (Supabase RLS)
- the client-facing API (PostgREST)

**Reason:** this keeps a microservice boundary where the **FastAPI service owns auth + authorization**, and the database can be swapped later without changing extension behavior.

### High-level request flows

#### 1) Login (extension)

1. Extension opens a tab to:
   - `GET /login?return_to=chrome-extension://<extension-id>/auth.html`
2. Backend redirects user to Google OAuth.
3. Google redirects back to:
   - `GET /auth/google/callback`
4. Backend:
   - normalizes the provider identity (`provider="google"`, `provider_subject=<google sub>`)
   - creates or looks up an internal `user_id`
   - issues:
     - a short-lived access token (JWT)
     - a longer-lived refresh token (opaque, stored hashed in DB)
   - redirects the browser to the extension `auth.html` with tokens in the **URL fragment**:
     - `#access_token=...&refresh_token=...`

#### 2) Bookmark save

1. Extension extracts `{url,title,html}` from the active tab.
2. Extension calls:
   - `POST /bookmarks` with `Authorization: Bearer <access_token>`
3. Backend:
   - verifies JWT
   - writes the bookmark row with the token’s `user_id`

#### 3) Token refresh

If the access token expires:

1. Extension calls:
   - `POST /auth/refresh` with `{ refresh_token }`
2. Backend:
   - validates refresh token against DB hash + expiry + revoked flag
   - revokes the old refresh token and issues a new one (**rotation**)
   - returns a fresh `{access_token, refresh_token}`

### Data model (designed for future account linking)

We do **not** bind bookmarks to “Google users”.

Instead:

- **`users`**: the canonical “internal user”
- **`user_identities`**: provider identities that authenticate as that user
  - `(provider, provider_subject)` is unique
  - later we can add GitHub/Facebook identities that point to the same `user_id`
- **`bookmarks`**: owned by `user_id`
- **`refresh_tokens`**: opaque tokens stored as a hash; supports revocation and rotation

This structure supports “account linking” later without changing bookmark ownership.

### Security decisions (why they exist)

- **Bearer tokens for extension API calls**
  - avoids cross-origin cookie complexity and CSRF class of issues
- **`return_to` allowlist**
  - prevents leaking tokens to arbitrary extension IDs
  - in production, `return_to` requires explicit allowlisting via env
- **Tokens in URL fragment, not query**
  - reduces accidental logging (server logs, proxies)
- **Refresh tokens stored hashed**
  - DB leak ≠ immediate token replay
- **HTML size limit (`MAX_HTML_BYTES`)**
  - prevents runaway request sizes and storage blowups
- **Basic rate limiting**
  - early-stage abuse protection (note: per-process; not global across instances)

### Project structure (relevant parts)

Backend:

- `src/legendary_potato/app/main.py`: FastAPI app + middleware + lifespan startup (DB/migrations)
- `src/legendary_potato/api/routes/auth.py`: Google OAuth routes + extension return redirect
- `src/legendary_potato/api/routes/auth_api.py`: `/me`, refresh, revoke
- `src/legendary_potato/api/routes/bookmarks.py`: bookmark endpoints
- `src/legendary_potato/core/db.py`: database access layer (queries + refresh token ops)
- `src/legendary_potato/core/migrations.py`: simple SQL migration runner
- `migrations/*.sql`: schema migrations

Extension (MV3):

- `extension/manifest.json`
- `extension/popup.html`, `extension/popup.js`
- `extension/auth.html`, `extension/auth.js`

