from __future__ import annotations

import os
import platform


def environment() -> dict:
    return {
        "os": platform.system(),
        "python": platform.python_version(),
        "tokenoskobi_root": os.getenv("TOKENOSKOBI_ROOT"),
        "is_windows": platform.system() == "Windows",
        "is_linux": platform.system() == "Linux",
    }


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value