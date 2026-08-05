from __future__ import annotations

import platform
from contextlib import contextmanager


IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


@contextmanager
def shared_lock(_file):
    """
    Cross-platform shared lock placeholder.

    Linux:
        Later this will use fcntl.LOCK_SH

    Windows:
        Currently no-op.
    """

    yield


@contextmanager
def exclusive_lock(_file):
    """
    Cross-platform exclusive lock placeholder.

    Linux:
        Later this will use fcntl.LOCK_EX

    Windows:
        Currently no-op.
    """

    yield