# Project-Hub UI (Angular)

This is the frontend for the Project-Hub task board. It’s a basic Angular app that lets you drag tasks around and edit their details in a modal.

## What it does
* **Drag and Drop:** Uses Angular CDK to move tasks between To Do, Doing, and Done.
* **Task Details:** A popup to add notes, manage a checklist, and pick an icon/color for each task.
* **Themes:** Has a simple toggle for Dark and Light mode.
* **Auto-Sync:** Every time you move or change a task, it sends the update to the local backend.

## Setup
1. Make sure you have the Angular CLI installed.
2. Run `npm install`.
3. Run `ng serve` to see it at http://localhost:4200.

## Logic
All the main logic is in `app.component.ts`. It handles the task models, the progress bar calculations, and the communication with the Python server.

---
*By tugapse*
