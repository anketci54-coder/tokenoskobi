from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_PRODUCT_STATE_DIR = Path("/var/lib/tokenoskobi-product-slice-03")


def get_root() -> Path:
    """
    Returns the Tokenoskobi root directory.

    Priority:
    1. TOKENOSKOBI_ROOT environment variable
    2. Repository containing this module (independent of working directory)
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


def product_state_dir() -> Path:
    """Keep existing installations on their ledger; fresh installs need no sudo."""
    if value := os.getenv("TOKENOSKOBI_SLICE03_STATE_DIR"):
        return Path(value).expanduser().resolve()
    # Never silently start another ledger merely because XDG was configured.
    # lstat() preserves even a broken legacy symlink and propagates access errors.
    try:
        LEGACY_PRODUCT_STATE_DIR.lstat()
    except FileNotFoundError:
        pass
    else:
        return LEGACY_PRODUCT_STATE_DIR
    if value := os.getenv("XDG_STATE_HOME"):
        return Path(value).expanduser().resolve() / "tokenoskobi/product-slice-03"
    return Path.home() / ".local/state/tokenoskobi/product-slice-03"


def product_cache_dir() -> Path:
    if value := os.getenv("TOKENOSKOBI_GT_RATE_DIR"):
        return Path(value).expanduser().resolve()
    return Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))).expanduser().resolve() / "tokenoskobi"
