from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = Path.cwd()


def get_root() -> Path:
    """
    Returns the Tokenoskobi root directory.

    Priority:
    1. TOKENOSKOBI_ROOT environment variable
    2. Current working directory
    """
    value = os.getenv("TOKENOSKOBI_ROOT")
    if value:
        return Path(value).resolve()

    return DEFAULT_ROOT.resolve()


def tools_dir() -> Path:
    return get_root() / "tools"


def core_dir() -> Path:
    return get_root() / "core"


def engineering_dir() -> Path:
    return get_root() / "engineering"


def data_dir() -> Path:
    return get_root() / "data"