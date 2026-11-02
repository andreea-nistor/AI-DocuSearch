"""Atomic JSON writes so a crash mid-write cannot truncate a user's data file."""

import json
import os
import tempfile
from typing import Any


def write_json_atomic(path: str, data: Any) -> None:
    """Write JSON to a temp file in the same directory, then replace the target."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
