"""Fit text to terminal columns: measure, cut, pad, wrap and lay out in columns."""

from __future__ import annotations

from ._columns import Order, columnize
from ._fit import Align, Side, fit, pad, truncate
from ._graphemes import graphemes
from ._width import display_width
from ._wrap import wrap

__version__ = "0.2.0"

__all__ = [
    "Align",
    "Order",
    "Side",
    "columnize",
    "display_width",
    "fit",
    "graphemes",
    "pad",
    "truncate",
    "wrap",
]
