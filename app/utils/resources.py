from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Return source root or PyInstaller bundle root."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    return application_root().joinpath(*parts)
