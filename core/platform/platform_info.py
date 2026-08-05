from __future__ import annotations

import platform
from pathlib import Path


def get_platform_info() -> dict:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "cwd": str(Path.cwd()),
    }


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"