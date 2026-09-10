from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Return source root or PyInstaller bundle root."""
    if getattr(sys, "frozen", False):
        executable_root = Path(sys.executable).resolve().parent
        if (executable_root / "models").is_dir():
            return executable_root
        return Path(getattr(sys, "_MEIPASS", executable_root))
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    return application_root().joinpath(*parts)
