# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-11-15

### Added
- **Login.** Browser sign-in with an HttpOnly session cookie (30 days). Failed attempts are rate limited per client.
- **API access from code.** Bearer tokens obtained via a device flow (like `gh auth login`): the script shows a link and a code, and you approve it in the browser. See `examples/project_hub_client.py`.
- **Multiple users.** Each user has their own projects, stored in `data/users/<id>/`. Users never see each other's data.
- **User management CLI.** `python -m server users add|list|passwd|remove` and `tokens list|revoke`. Changes apply to a running server without a restart, and removed users' data is moved to `data/deleted/`.
- **Deploy scripts.** `deploy/install.sh` installs or updates the app as a hardened systemd service. `deploy/setup-nginx.sh` publishes it under `/hub/` without touching other nginx proxies. See `deploy/README.md`.
- Confirmation dialog before deleting projects, tasks and checklist items.
- "Not started" projects get their own section in the sidebar, with status icons. Dragging a project between sections changes its status.
- Three-state project status switch (not started / active / archived) in the header. New projects start as "not started" and become active once a task leaves the first column.
- Sync indicator in the header. Saves are debounced and sent in order.
- Drag and drop to reorder projects and checklist items.
- `--help` in `build.sh`, `run.sh`, `run-dev.sh` and the deploy scripts.

### Changed
- Code is organized into `src/server` (a Python package, `python -m server`) and `src/client` (Angular, split into `core/` and `features/`).
- API routes moved under `/api`. In development, `ng serve` proxies them instead of relying on CORS.
- The client uses relative URLs, so it works behind a sub-path such as `/hub/`.
- `run-dev.sh` runs the backend and the Angular dev server together with colored output, and stops both if either exits. `run.sh` runs only the server, which also serves the built client.
- `build.sh` can run from any folder, uses `npm ci` and accepts `PROJECT_HUB_BASE_HREF`.
- The `PROJECT_HUB_DATA_DIR` environment variable replaces `PROJECT_HUB_JSON_FILE`.

### Fixed
- "Not started" projects were dropped when saving.
- A failed save could corrupt the data files. Writes are now atomic, and a failed save returns HTTP 500.

### Upgrading
- On the first start, the single-user `auth.json` and `data/projects*.json` are migrated automatically to the new multi-user layout. The existing user keeps their projects and tokens.
- Create additional accounts with `python -m server users add <name>`, or `sudo project-hub users add <name>` on a deployed server.

## [0.1.2] - 2026-06-16

### Added
- Project status toggle in the header and main view.

### Changed
- Archived projects are no longer selected automatically on startup.

## [0.1.1] - 2026-05-25

### Changed
- `build.sh` checks for the required system dependencies.

### Fixed
- The client could not reach the API when served from a sub-path.

## [0.1.0] - 2026-05-22

### Added
- Kanban board with To Do / Doing / Done columns and drag and drop between them.
- Task detail modal with description, notes, color, icon and a checklist with progress.
- Project sidebar, collapsible, with archived projects.
- Light and dark themes.
- FastAPI server with Pydantic models and JSON file storage, with active and archived projects in separate files. The server also serves the built client.
- `build.sh` to set up the Python environment and build the client.

[Unreleased]: https://github.com/tugapse/project-hub/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/tugapse/project-hub/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/tugapse/project-hub/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/tugapse/project-hub/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/tugapse/project-hub/releases/tag/v0.1.0
