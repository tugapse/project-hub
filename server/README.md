# Project-Hub Server (FastAPI)

This is a simple Python backend that saves your Kanban board data to a local file.

## How it works
* **Storage:** It keeps everything in a file called `projects.json`. When the server starts, it loads the data into memory.
* **API:** It only has two main jobs:
    1. Send the current list of projects to the frontend (`GET /projects`).
    2. Overwrite the JSON file whenever the frontend sends a change (`POST /projects`).
* **Validation:** Uses Pydantic models to make sure the task data coming from the frontend is formatted correctly.

## Running it
1. Install the requirements: `pip install fastapi uvicorn pydantic`.
2. Run the server: `python3 server/main.py`.
3. The API will be live at http://localhost:8000.

## Note
The `allow_origins=["*"]` setting is enabled in the CORS middleware so the Angular app can talk to this server without being blocked.

---
*By tugapse*