## Deployment overview (GCP + managed DB later)

This doc is intentionally high-level. It’s meant to help devs who can code but haven’t deployed services before.

### What you deploy

You deploy at least two “things”:

1. **The backend service** (FastAPI in a container)
2. **A Postgres database** (hosted Supabase Postgres or self-hosted Postgres/Supabase later)

The Chrome extension is deployed separately (Chrome Web Store or enterprise distribution).

### What stays the same across hosted vs self-hosted DB

If you treat Supabase as “Postgres behind the API”, then the backend only cares about:

- `DATABASE_URL`

So a hosted Supabase Postgres URL and a self-hosted Postgres URL are both “just Postgres” to the app.

### Minimal production checklist (practical)

- **Use HTTPS** for the backend public URL (Cloud Run gives this)
- **Set `ENV=production`**
  - this turns on stricter behaviors (notably `return_to` allowlist handling)
- **Lock down `EXTENSION_RETURN_TO_ALLOWLIST`**
  - allow only your real extension URL(s)
- **Lock down `CORS_ALLOW_ORIGIN_REGEX`**
  - allow only `chrome-extension://<your-extension-id>`
- **Store secrets in Secret Manager**
  - `GOOGLE_CLIENT_SECRET`, `STARLET_SECRET_KEY`, `API_JWT_SECRET`, DB password
- **Make the database network-private**
  - best case: DB is only reachable from the backend service network
- **Run migrations**
  - this app runs migrations on startup; in bigger deployments you may move that to a one-off job

### OAuth redirect URIs in production

Google OAuth requires exact redirect URIs.

For Cloud Run, your redirect usually looks like:

- `https://<service-name>-<hash>-<region>.a.run.app/auth/google/callback`

If you use a custom domain, it becomes:

- `https://api.yourdomain.com/auth/google/callback`

### Extension production gotcha: stable extension ID

The allowlist and CORS config needs your extension ID:

- `chrome-extension://<extension-id>/auth.html`

An unpacked extension’s ID can change. A published extension has a stable ID.

