# Login (Option A – Single Admin)

## Where login data is stored

| What | Where |
|------|--------|
| **Login page** | `frontend/login.html` |
| **Admin username** | `.env` → `ADMIN_USERNAME` (default: `admin`) |
| **Admin password** | `.env` → `ADMIN_PASSWORD` (default: `admin`) |
| **Token (optional)** | `.env` → `ADMIN_TOKEN`. If not set, the API derives a token from `SECRET_KEY` + `ADMIN_USERNAME`. |
| **“Logged in” state** | Browser **localStorage** → key `wardrobe_token` (the token returned after successful login). |

No user table is used; everything is in `.env` and localStorage.

## Setup

1. Set credentials in `.env` (or keep defaults):
   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_secure_password
   ```
2. Restart the API: `python api.py`
3. Open `frontend/login.html`, sign in with the username and password from `.env`.

## Flow

- User opens any app page (index, wardrobe, upload, dressing-room) → if no `wardrobe_token` in localStorage, redirect to `login.html`.
- User submits username/password on `login.html` → API checks against `ADMIN_USERNAME` / `ADMIN_PASSWORD` → returns a token → frontend saves it in localStorage and redirects to `index.html`.
- **Logout** clears localStorage and redirects to `login.html`.

## API

- `POST /api/auth/login` — body: `{ "username", "password" }` → returns `{ "success", "token" }`.
- `GET /api/auth/me` — header: `Authorization: Bearer <token>` → returns `{ "logged_in", "username" }` (optional).

For production, set a strong `ADMIN_PASSWORD` and consider setting `ADMIN_TOKEN` in `.env` to a long random string.
