## Local development guide (backend + extension)

This project has two parts:

- **Backend**: FastAPI service (`legendary_potato`)
- **Extension**: Chrome MV3 extension in `extension/`

### Prerequisites

- Docker + Docker Compose
- A Google Cloud OAuth client (Web application)

### 1) Create your `.env`

Copy `env_sample` to `.env`:

- Fill in `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Set `STARLET_SECRET_KEY` and `API_JWT_SECRET` to long random values
- For compose dev DB, set:
  - `DATABASE_URL=postgresql://app:app@db:5432/app`

### 2) Start the backend + database

From the repo root:

```bash
docker compose up --build
```

The backend will listen on `http://localhost:8001`.

On startup the app will:

- connect to the database (if `DATABASE_URL` is set)
- apply SQL migrations from `migrations/`

### 3) Configure Google OAuth redirect URI

In Google Cloud Console → OAuth Client (Web application):

- add redirect URI:
  - `http://localhost:8001/auth/google/callback`

### 4) Load the Chrome extension (unpacked)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Choose the `extension/` directory in this repo

### 5) Log in from the extension

1. Click the extension icon
2. Click **Sign in with Google**
3. Complete the Google login flow
4. The backend redirects to `auth.html` inside the extension and stores tokens

### 6) Save a page

1. Navigate to any page
2. Click the extension icon → **Save current page**
3. The extension sends `{url,title,html}` to `POST /bookmarks`

### Useful endpoints for debugging

- `GET /` shows whether the backend session exists
- `GET /me` (Bearer) shows the internal `user_id` and identities
- `GET /bookmarks` (Bearer) lists your most recent bookmarks

