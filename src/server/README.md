# Project-Hub Server (FastAPI)

This is a simple Python backend that saves your Kanban board data to a local file.

## How it works
* **Storage:** It keeps everything in a file called `projects.json`. When the server starts, it loads the data into memory.
* **API:** It only has two main jobs:
    1. Send the current list of projects to the frontend (`GET /api/projects`).
    2. Overwrite the JSON file whenever the frontend sends a change (`POST /api/projects`).
* **Validation:** Uses Pydantic models to make sure the task data coming from the frontend is formatted correctly.

## Running it
1. Install the requirements: `pip install -r src/server/requirements.txt`.
2. Run the server: `cd src && python3 -m server` (or `uvicorn server.main:app --app-dir src`).
3. The API will be live at http://localhost:9998.

## Notes
* Routes live under `/api`; everything else is served from the Angular build in `<repo>/dist`.
* There is no CORS: in dev, `ng serve` proxies `/api` to this server (`src/client/proxy.conf.json`).
* Saves are atomic (temp file + rename), and a failed save returns HTTP 500.

---
*By tugapse*