"""Package version, single-sourced from installed distribution metadata."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("aetherlab")
except PackageNotFoundError:  # pragma: no cover - not installed (e.g. source tree)
    __version__ = "0.0.0.dev0"
