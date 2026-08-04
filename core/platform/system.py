"""
Tokenoskobi Platform Compatibility Layer

This module centralizes platform-specific behavior.
No production code should directly import fcntl.
"""

from __future__ import annotations

import platform

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def supports_posix_file_lock() -> bool:
    return IS_LINUX


def current_platform() -> str:
    return platform.system()


def current_python() -> str:
    return platform.python_version()


if __name__ == "__main__":
    print("=" * 60)
    print("TOKENOSKOBI PLATFORM")
    print("=" * 60)
    print("Platform :", current_platform())
    print("Python   :", current_python())
    print("POSIX    :", supports_posix_file_lock())
