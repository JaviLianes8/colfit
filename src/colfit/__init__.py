"""Fit text to terminal columns: measure, cut, pad, wrap and lay out in columns.

``Align``, ``Side`` and ``Order`` are the ``Literal`` types of the ``align``, ``side`` and
``order`` arguments, for code that passes those values around:

>>> import typing
>>> from colfit import Align, Order, Side, pad
>>> typing.get_args(Align), typing.get_args(Side), typing.get_args(Order)
(('left', 'center', 'right'), ('end', 'start', 'middle'), ('rows', 'columns'))
>>> def cell(text: str, align: Align) -> str:
...     return "[" + pad(text, 4, align=align) + "]"
>>> cell("ok", "right")
'[  ok]'
"""

from __future__ import annotations

from ._columns import Order, columnize
from ._fit import Align, Side, fit, pad, truncate
from ._graphemes import graphemes
from ._width import display_width
from ._wrap import wrap

__version__ = "1.0.0"

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
