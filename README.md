# learn_scrap

## Goal (current milestone)

- Google OAuth login (backend)
- Chrome extension (MV3) can save current page `{url,title,html}` to backend
- Backend persists per-user bookmarks in Postgres (Supabase Postgres works as a drop-in)

## Local development

### 1) Configure env

Copy `env_sample` to `.env` and fill in:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `STARLET_SECRET_KEY`
- `API_JWT_SECRET`
- `DATABASE_URL`
- `MAX_HTML_BYTES` (optional)
- `REFRESH_TOKEN_TTL_SECONDS` (optional)

If you're using `docker compose` from this repo, set:

- `DATABASE_URL=postgresql://app:app@db:5432/app`

### 2) Start services

```bash
docker compose up --build
```

The API will be available at `http://localhost:8001`.

### 3) Google OAuth redirect URI

In Google Cloud Console, set the authorized redirect URI to:

- `http://localhost:8001/auth/google/callback`

## Chrome extension (hello world)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder
4. Click the extension icon:
   - **Sign in with Google** (opens a login tab)
   - After login, the backend redirects to `extension/auth.html` and stores an access + refresh token
   - Click **Save current page** to send `{url,title,html}` to `POST /bookmarks`