"""Terminal display width of text, measured per grapheme cluster."""

from __future__ import annotations

from ._check import text_arg
from ._escapes import pieces
from ._graphemes import graphemes
from ._unicode import char_width, conjunct_class, grapheme_class, has_variations, is_spacing_mark

_ZWJ = "\u200d"
_TEXT_STYLE = "\ufe0e"
_EMOJI_STYLE = "\ufe0f"
_MODIFIERS = ("\U0001f3fb", "\U0001f3ff")  # the five skin tone modifiers

Unit = tuple[str, int, bool]
"""A grapheme cluster or an escape sequence: ``(text, columns, is_escape)``."""


def cluster_width(cluster: str) -> int:
    """Columns one grapheme cluster takes."""
    base = cluster[0]
    width = char_width(base)
    emoji = grapheme_class(base) == "Q"
    previous = base
    for char in cluster[1:]:
        if char == _EMOJI_STYLE:
            if has_variations(base):
                width = 2
        elif char == _TEXT_STYLE:
            if has_variations(base):
                width = min(width, 1)
        elif emoji:
            if previous == _ZWJ or _MODIFIERS[0] <= char <= _MODIFIERS[1]:
                width = 2  # a zwj or modifier sequence is drawn as one emoji (UTS #51)
        elif width and (is_spacing_mark(char) or grapheme_class(char) == "S"):
            width = 2
        elif width and conjunct_class(char) == "O":
            width = 2  # consonant, linker, consonant: one conjunct
        elif previous != _ZWJ and grapheme_class(char) != "I":
            width += char_width(char)
        previous = char
    return width


def units(text: str) -> list[Unit]:
    """Split ``text`` into grapheme clusters and escape sequences, with their widths."""
    out: list[Unit] = []
    for piece, escape in pieces(text):
        if escape:
            out.append((piece, 0, True))
        elif piece.isascii() and piece.isprintable():
            out += [(char, 1, False) for char in piece]
        else:
            out += [(cluster, cluster_width(cluster), False) for cluster in graphemes(piece)]
    return out


def width_of(text: str) -> int:
    if text.isascii() and text.isprintable():
        return len(text)
    return sum(unit[1] for unit in units(text))


def display_width(text: str) -> int:
    """Return the number of terminal columns ``text`` takes.

    Text is measured per extended grapheme cluster (UAX #29) with the Unicode 18.0.0
    tables: East Asian Wide and Fullwidth characters take two columns; marks, format,
    default ignorable and control characters none; an emoji sequence, a flag or a cluster
    with a spacing mark or a conjunct two. Escape sequences take none.
    """
    return width_of(text_arg("text", text))
