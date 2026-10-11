"""Arrange strings into evenly sized terminal columns that fit a width, display-width aware."""

from __future__ import annotations

from ._columns import columnize
from ._width import display_width

__version__ = "0.1.0"

__all__ = ["columnize", "display_width"]
