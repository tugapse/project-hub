import json
import os
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Holds auth.json and one folder per user under users/<user_id>/.
DATA_DIR = Path(os.getenv("PROJECT_HUB_DATA_DIR", str(PROJECT_ROOT / "data")))


def write_json_atomic(path: Path, data: Any, mode: int | None = None):
    """Writes JSON to a temp file in the same directory, then atomically replaces the target.

    `mode` optionally sets the file permissions (e.g. 0o600 for secrets).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        if mode is not None:
            os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
