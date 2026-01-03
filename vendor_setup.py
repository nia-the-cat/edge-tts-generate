from __future__ import annotations

import os
import sys
from os.path import abspath, dirname, join


_ENVIRONMENT_FLAGS = {
    "AIOHTTP_NO_EXTENSIONS": "1",
    "FROZENLIST_NO_EXTENSIONS": "1",
    "MULTIDICT_NO_EXTENSIONS": "1",
    "YARL_NO_EXTENSIONS": "1",
    "PROPCACHE_NO_EXTENSIONS": "1",
}


def ensure_vendor_path() -> str:
    """Ensure the vendored dependencies are importable and configured."""

    vendor_dir = abspath(join(dirname(__file__), "vendor"))
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)

    for key, value in _ENVIRONMENT_FLAGS.items():
        os.environ.setdefault(key, value)

    return vendor_dir
