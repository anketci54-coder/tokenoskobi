"""
Tokenoskobi Platform File Lock Layer

Purpose:
    Provide a single interface for file locking across platforms.

Linux:
    Uses POSIX fcntl.

Windows:
    Uses a no-op implementation for now.
"""

from __future__ import annotations

from contextlib import contextmanager
import platform

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

if IS_LINUX:
    import fcntl


@contextmanager
def shared_lock(file_obj):
    if IS_LINUX:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    else:
        # Temporary Windows implementation
        yield


@contextmanager
def exclusive_lock(file_obj):
    if IS_LINUX:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    else:
        # Temporary Windows implementation
        yield

def lock_ex(file_obj):
    """
    Acquire an exclusive lock.
    """
    if IS_LINUX:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)


def lock_sh(file_obj):
    """
    Acquire a shared lock.
    """
    if IS_LINUX:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_SH)


def unlock(file_obj):
    """
    Release the current lock.
    """
    if IS_LINUX:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

