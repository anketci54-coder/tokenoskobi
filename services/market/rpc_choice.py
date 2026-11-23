"""Choosing which RPC endpoint a job should use."""
from __future__ import annotations

from typing import Any, Callable


def pick_public_rpc(urls: list[str], call: Callable[[str, str, list[Any]], Any]) -> str:
    """First public BSC endpoint that answers as chain 56.

    The watcher makes many calls, so it never uses the metered Alchemy key; that quota is kept for
    the panel's analyses.
    """
    for url in urls:
        try:
            if int(call(url, "eth_chainId", []), 16) == 56:
                return url
        except Exception:
            continue
    raise RuntimeError("NO_PUBLIC_RPC")
