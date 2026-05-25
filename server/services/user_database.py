import json
import os
from pathlib import Path
from typing import List, Optional

from entities.dto import UserInDB

USERS_JSON_FILE = os.getenv("PROJECT_HUB_USERS_JSON_FILE", "./data/users.json")
DB_FILE = Path(USERS_JSON_FILE)

class UsersDatabase:
    _users_storage: List[UserInDB]

    def __init__(self):
        self._users_storage = []
        self.load_from_disk()

    def load_from_disk(self):
        """Loads users from the JSON file into memory."""
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        if DB_FILE.exists() and DB_FILE.stat().st_size > 0:
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._users_storage = [UserInDB(**u) for u in data] if data else []
            except Exception as e:
                print(f" Load Error from {DB_FILE}: {e}")
                self._users_storage = []
        else:
            self._users_storage = []

    def save_to_disk(self):
        """Dumps the current in-memory user list to the JSON file."""
        try:
            DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(DB_FILE, "w", encoding="utf-8") as f:
                data = [u.model_dump(mode="json") for u in self._users_storage]
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f" Failed to save users to disk: {e}")

    def get_user(self, username: str) -> Optional[UserInDB]:
        """Retrieves a user by username."""
        for user in self._users_storage:
            if user.username == username:
                return user
        return None

    def add_user(self, user: UserInDB) -> UserInDB:
        """Adds a new user to the database and saves to disk."""
        if self.get_user(user.username):
            raise ValueError(f"User with username '{user.username}' already exists.")
        self._users_storage.append(user)
        self.save_to_disk()
        return user