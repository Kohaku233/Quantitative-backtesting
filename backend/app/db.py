from pathlib import Path

from backend.app.config import get_settings


def get_database_path(root: Path | None = None) -> Path:
    base_path = root or Path.cwd()
    return base_path / get_settings().database_filename
