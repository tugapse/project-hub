# Project-Hub Server (FastAPI)

This is a simple Python backend that saves your Kanban board data to a local file.

## How it works
* **Storage:** each user has their own folder, `data/users/<user_id>/` (`projects.json` + `projects_archived.json`). A user's data is loaded into memory on their first request (`DatabaseRegistry`).
* **API:** It only has two main jobs (both require authentication and act on the signed-in user's data):
    1. Send the current list of projects to the frontend (`GET /api/projects`).
    2. Overwrite the JSON file whenever the frontend sends a change (`POST /api/projects`).
* **Auth:** users stored in `data/auth.json` (scrypt password hashes + SHA-256 hashes of tokens; every token has a `user_id`). The old single-user format is migrated on load.
    * Browser: `POST /api/auth/login` sets an HttpOnly `ph_session` cookie; `POST /api/auth/logout`; `GET /api/auth/me`.
    * Code: `Authorization: Bearer phub_...`, obtained via the device flow:
        1. `POST /api/auth/device/code {client_name}` → `device_code`, `user_code`, `verification_uri_complete`.
        2. The user opens the URL, signs in and approves (`GET /api/auth/device/{user_code}`, `POST /api/auth/device/approve`, browser session only).
        3. The client polls `POST /api/auth/device/token {device_code}` every `interval` seconds; it gets `400 {"error": "authorization_pending" | "slow_down" | "access_denied" | "expired_token"}` until approved, then `{access_token}` (once).
    * `GET /api/health` is public (used by the run scripts).
* **Validation:** Uses Pydantic models to make sure the task data coming from the frontend is formatted correctly.

## Running it
1. Install the requirements: `pip install -r src/server/requirements.txt`.
2. Create a user: `cd src && python3 -m server users add <username>`.
3. Run the server: `cd src && python3 -m server` (or `uvicorn server.main:app --app-dir src`).
4. The API will be live at http://localhost:9998.

## Notes
* Routes live under `/api`; everything else is served from the Angular build in `<repo>/dist`.
* There is no CORS: in dev, `ng serve` proxies `/api` to this server (`src/client/proxy.conf.json`).
* CLI: `python -m server [serve | users add|list|passwd|remove | tokens list | tokens revoke <id>]` (`create-user` is kept as an alias of `users add`). Removed users' data is moved to `data/deleted/<id>-<timestamp>/`. Changes to `auth.json` made by the CLI are picked up by a running server.
* Tests: `pip install -r src/server/requirements-dev.txt`, then `cd src && python -m pytest server/tests`.
* Saves are atomic (temp file + rename), and a failed save returns HTTP 500.

---
*By tugapse*