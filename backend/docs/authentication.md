# Google sign-in with Auth0

Run Tib uses the Auth0 React SDK (Authorization Code with PKCE) for Google sign-in.
FastAPI validates the API access token using Auth0's public signing keys and finds
or creates a local user by the verified `sub`. No passwords or Google client
secrets belong in this repository.

## 1. Create the Auth0 application

In the Auth0 dashboard, create an application named **Run Tib**, choosing
**Single Page Application**. Copy its **Domain** and **Client ID**.

Set these application settings for local development:

| Setting | Value |
| --- | --- |
| Allowed Callback URLs | `http://localhost:5173` |
| Allowed Logout URLs | `http://localhost:5173` |
| Allowed Web Origins | `http://localhost:5173` |

Use `localhost` consistently. If you change the frontend port or hostname, update
all three settings. Add the exact HTTPS frontend origin when deploying.

## 2. Register the backend API

Under **Applications → APIs**, create **Run Tib API**:

- Identifier: `https://run-tib-api` (an identifier, not a URL you need to host).
- Signing algorithm: **RS256**.
- Enable **RBAC** and **Add Permissions in the Access Token** in API settings.
- Add the permission `create:challenges` under Permissions.

Ordinary users can sign in and browse challenges. To let yourself create challenges,
create an organizer role with `create:challenges` and assign that role to your Auth0
user after your first login. Sign out and sign back in after permission changes.

## 3. Enable Google

Under **Authentication → Social**, create or open the **google-oauth2** connection.
Enable it for the **Run Tib** application on the connection's Applications tab.
Keep the standard profile and email scopes enabled.

For your own Google OAuth credentials:

1. In Google Cloud, create/select a project and configure Google Auth Platform's
   branding/consent screen and audience. Add test users while in testing mode.
2. Create an OAuth client with type **Web application**.
3. Set the authorized redirect URI to the exact callback shown by Auth0, normally
   `https://YOUR_AUTH0_DOMAIN/login/callback`.
4. Put the Google client ID and secret in the **Auth0 Google connection settings**.

The Google callback goes to Auth0; the Auth0 application callback goes to the React
app. These are different URLs. Auth0 development keys, if available, are only for
initial local testing; use your own Google credentials for production.

## 4. Configure the project

The local `.env` files contain empty Auth0 fields ready to fill in.

`frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AUTH0_DOMAIN=your-tenant.region.auth0.com
VITE_AUTH0_CLIENT_ID=your_spa_client_id
VITE_AUTH0_AUDIENCE=https://run-tib-api
```

`backend/.env` (keep your existing database settings):

```dotenv
AUTH0_DOMAIN=your-tenant.region.auth0.com
AUTH0_AUDIENCE=https://run-tib-api
FRONTEND_ORIGIN=http://localhost:5173
```

Use the domain without `https://` or a trailing slash. Both audience values must
exactly match the API Identifier. The SPA Client ID is public; no Auth0 client
secret is needed. Never put secrets in `VITE_*` variables, which are browser-visible.

## 5. Run and verify

From `backend` with the virtual environment active:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

From `frontend`:

```bash
npm install
npm run dev
```

Restart both servers after editing `.env`. Open `http://localhost:5173` and choose
**Continue with Google**. After returning, your name should appear beside **Sign out**.
Check the `users` table in DBeaver: the account is keyed by `google-oauth2|...`.
Signing in again uses the same row. Profile fields are saved on first sign-in.

- `GET /api/v1/auth/me` requires a valid access token and creates the local account
  on first access. Disabled accounts receive 403.
- `POST /api/v1/challenges` requires a valid user and `create:challenges` permission.
- Challenge reads and `/health` remain public.
- Protected requests must send `Authorization: Bearer <access_token>`. Use the API
  access token from `getAccessTokenSilently()`, not the ID token.
- The frontend persists the SDK token cache in browser local storage and uses
  rotating refresh tokens to renew expired access tokens. Configure the Auth0
  refresh-token settings below, then sign in again once to obtain a refresh token.
- Sign-out ends the app/Auth0 session; it does not sign you out of Google itself.
- Until frontend Auth0 settings are present, browsing works and the header shows
  “Sign-in coming soon”. Missing backend Auth0 configuration fails closed with 503.

Run backend authentication tests without contacting Auth0 or PostgreSQL:

```bash
python -m unittest discover -s tests -v
```

## References

- [Auth0 React quickstart](https://auth0.com/docs/quickstart/spa/react)
- [Configure the Google connection](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/google)
- [PyJWT validation and JWKS](https://pyjwt.readthedocs.io/en/stable/usage.html)

## Troubleshooting and terminal logs

Restart both `uvicorn main:app --reload` and `npm run dev` after configuration or
Vite changes. The dev server uses port 5173 with `strictPort` so it cannot silently
switch to a port missing from Auth0's callback allowlist.

- The backend logs token rejection reasons, Auth0 profile failures, database error
  types/SQLSTATE, and a request ID, status, and duration for API requests.
- Successful first account creation logs `auth.user_saved` after the commit.
- Browser callback, sign-in, sign-out, and account errors appear in the browser
  console and are forwarded over Vite's development websocket to its terminal.
  Error text is sanitized; tokens, authorization headers, and user profiles are
  not intentionally logged. The forwarding is development-only.
- The UI includes API failure details and a request ID for matching backend logs.
- Errors displayed entirely on Google/Auth0 pages cannot reach the app terminal.
  Check **Auth0 → Monitoring → Logs** and the error on that page.
- The backend uses certifi's trusted CA bundle for Auth0 JWKS HTTPS requests.
  This fixes missing system CA certificates on Python/macOS without disabling TLS
  certificate or hostname verification.

A Google/Auth0 login alone does not insert a Run Tib database row. The browser must
return to Run Tib and successfully call `GET /api/v1/auth/me`; that request verifies
the token, reads the Auth0 profile, and commits the local user. In DBeaver, refresh
`run_tib → public → users` after seeing `auth.user_saved` and a 200 response.

## Stay signed in after refresh

The frontend now uses `cacheLocation="localstorage"`, `useRefreshTokens`, and
`useRefreshTokensFallback`. The SDK adds `offline_access` to login requests,
restores its cache after reload, and renews short-lived access tokens using a
rotating refresh token. Fallback can recover an older session through Auth0's
cookie when available; reliable multi-day access requires refresh tokens.

Configure the following in Auth0:

1. **Applications → APIs → Run Tib API → Settings**: enable **Allow Offline Access**.
2. **Applications → Applications → Run Tib → Settings**: enable **Refresh Token
   Rotation**. Under advanced grant types, ensure **Refresh Token** is enabled.
3. Under **Refresh Token Expiration**, enable maximum and idle expiration. A
   reasonable starting point for this app is a maximum of **7 days (604800 seconds)**
   and an idle lifetime of **3 days (259200 seconds)**. This means an active user
   can remain signed in for up to a week; an unused session expires after three days.
4. Save, restart the frontend, and sign out/sign in once to populate the new cache
   with a refresh token. Reload the page to confirm your account returns.

These lifetimes are Auth0 server settings; the frontend cannot override them.
Clearing browser data, signing out, revocation, or expiration can require another
login. Browser local storage is accessible to JavaScript on the same origin, so
avoid untrusted scripts and keep access tokens short-lived. Do not extend access
tokens to seven days to implement a seven-day session.

## Authorize Swagger with an access token

Swagger uses **HTTPBearer** only. Sign into the frontend, open browser DevTools →
Network, and select the `/api/v1/auth/me` request (reload the page if needed).
Under Request Headers, find `Authorization: Bearer ...` and copy only the token
value after `Bearer`.

Open `http://localhost:8000/docs`, click **Authorize**, paste the token into the
**HTTPBearer** value field, and click **Authorize**. Swagger automatically adds the
Bearer prefix to API requests. Try `GET /api/v1/auth/me`.

Use the API access token, not an ID token or refresh token. When it expires, copy
a fresh token from a successful frontend request. Do not paste tokens into chat,
source code, or logs. Signing out of the website does not clear a token already
pasted into Swagger; use Swagger's Logout too when done.

The backend needs only the Auth0 domain and audience. It does not need a Client ID
or secret. Any Auth0 callback/web-origin entries added solely for Swagger can be
removed; retain the frontend's URLs.

`create:challenges` still requires an organizer permission on the Auth0 user. An
ordinary successful Google login grants access to your account, not organizer rights.

References:
- [Auth0 refresh token rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/use-refresh-token-rotation)
- [Auth0 refresh token expiration](https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-expiration)
