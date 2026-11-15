# Project-Hub

A high-performance, minimalist **Kanban Task Management** application built with a focus on developer productivity. 

![Project Hub Dashboard](./assets/dashboard.png)

---

## 🚀 Key Features

* **Fluid Kanban Interface:** Effortless task management across customizable status columns (To Do, Doing, Done).
* **Refined Task Detail Modal:** Optimized 60/40 split layout with a "Sharp-Edge" IDE-inspired design.
* **Reactive Checklists:** Real-time sub-task tracking with automated progress calculation and persistent state.

### 📸 Visual Preview

#### Task Detail Workspace
The detail popup is designed for deep work, featuring integrated category icons, color coding, and an expanded notes area.

![Task Detail Modal](./assets/popup.png)

---

## 🛠️ Technical Stack

* **Client:** Angular — `src/client`
* **Server:** FastAPI / Python 3 — `src/server` (port 9998 by default)
* **Data Persistence:** Pydantic-validated JSON storage (`data/projects.json`) with in-memory caching.

## 📁 Project Structure

```
src/
  server/    FastAPI backend (API + serves the built client)
  client/    Angular frontend
dist/        Angular build output, served by the server (generated)
data/        projects.json / projects_archived.json (generated)
build.sh     Creates .venv, installs deps, builds the client into dist/
run.sh       Runs the server (API + built client) on port 9998
run-dev.sh   Runs the server + Angular dev server (port 4200)
```

## 📦 Installation & Setup

```bash
git clone https://github.com/tugapse/project-hub.git
cd project-hub
./build.sh
```

## 🖥️ Usage

**Production-style (single process):**
```bash
./run.sh
```
Open http://localhost:9998.

**Development (hot reload):**
```bash
./run-dev.sh
```
Open http://localhost:4200 (API on 9998).

**Environment variables:**
* `PROJECT_HUB_HOST` (default `0.0.0.0`)
* `PROJECT_HUB_PORT` (default `9998`)
* `PROJECT_HUB_JSON_FILE` (default `<repo>/data/projects.json`)

**To stop:** Press Ctrl+C. The scripts trap the signal and free the ports.

---
*Created as part of a personal tooling and learning.*
*Maintained by Fabio Almeida.*
