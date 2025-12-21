## Configuration reference (env vars)

All environment configuration lives in `.env` (see `env_sample`).

### Core app settings

- `ENV`
  - `local` (default): app may use ngrok logic and relaxed dev behaviors
  - `production`: stricter behaviors (e.g. `return_to` allowlist required)
- `UVICORN_PORT`
  - local port (defaults to 8001)
- `PUBLIC_DOMAIN`
  - public URL for OAuth redirect correctness in hosted environments (Cloud Run)

### Google OAuth

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

### Session security

- `STARLET_SECRET_KEY`
  - used by `SessionMiddleware` to sign session cookies

### Database (Supabase Postgres as plain Postgres)

- `DATABASE_URL`
  - Example for compose dev DB:
    - `postgresql://app:app@db:5432/app`

### Tokens (extension auth)

- `API_JWT_SECRET`
  - server secret used to sign access JWTs and salt refresh token hashes
- `API_JWT_ISSUER`
  - default: `legendary_potato`
- `API_JWT_TTL_SECONDS`
  - access token lifetime (JWT)
- `REFRESH_TOKEN_TTL_SECONDS`
  - refresh token lifetime (opaque token stored hashed in DB)

### Security / limits

- `MAX_HTML_BYTES`
  - max UTF-8 size allowed for the `html` field when creating a bookmark
- `CORS_ALLOW_ORIGIN_REGEX`
  - which browser origins may call the API (extension origin)
  - for production, set this to your specific extension ID, e.g.:
    - `chrome-extension://<your-extension-id>`
    - or a tight regex
- `EXTENSION_RETURN_TO_ALLOWLIST`
  - comma-separated allowlist of `return_to` values that can receive tokens
  - entries can be:
    - exact URL: `chrome-extension://<id>/auth.html`
    - origin prefix (must end with `/`): `chrome-extension://<id>/`

