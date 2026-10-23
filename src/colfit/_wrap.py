"""Wrap text into lines that fit a number of terminal columns."""

from __future__ import annotations

from ._check import int_arg, line_arg, text_arg
from ._cut import cut
from ._escapes import pieces
from ._fit import ELLIPSIS
from ._width import Unit, escapes_of, units


def _chunks(word: list[Unit], width: int) -> list[list[Unit]]:
    """Break a word too wide for a line at cluster boundaries."""
    out = []
    last = max((index for index, unit in enumerate(word) if unit[1]), default=-1)
    start = 0
    while start < len(word):
        end, used = start, 0
        while end < len(word) and used + word[end][1] <= width:
            used += word[end][1]
            end += 1
        while end < len(word) and not used:
            used += word[end][1]  # a cluster wider than the line still has to go somewhere
            end += 1
        if end > last:
            end = len(word)  # zero-width clusters and escapes stay with the text before them
        out.append(word[start:end])
        start = end
    return out


def _words(line: list[Unit]) -> list[tuple[list[Unit], list[Unit]]]:
    """(spaces before, word) pairs. A space with a mark on it is part of a word."""
    out: list[tuple[list[Unit], list[Unit]]] = []
    spaces: list[Unit] = []
    word: list[Unit] = []
    for unit in line:
        if unit[0] == " ":
            if word:
                out.append((spaces, word))
                spaces, word = [], []
            spaces.append(unit)
        else:
            word.append(unit)
    if word:
        out.append((spaces, word))
    return out


def _paragraph(text: str, width: int) -> list[list[Unit]]:
    lines: list[list[Unit]] = []
    current: list[Unit] = []
    used = 0
    carry: list[Unit] = []
    for spaces, word in _words(units(text)):
        size = sum(unit[1] for unit in word)
        if spaces and not current and not lines:  # the indent of the paragraph
            if size <= width < len(spaces) + size:
                spaces = []  # the first word fits a line, but not after the indent
            else:
                word, size, spaces = spaces + word, size + len(spaces), []
        if carry:
            carry += spaces  # in place: a long run of escapes between spaces stays linear
            spaces, carry = carry, []
        if current and not size:
            # Escape sequences alone join the line; their spaces go to the next word.
            current += word
            carry = spaces
            continue
        if current and used + len(spaces) + size <= width:
            current += spaces + word
            used += len(spaces) + size
            continue
        if current and not used:
            word = current + word  # a line of escapes only joins the next word
        elif current:
            lines.append(current)
        pieces = _chunks(word, width) if size > width else [word]
        lines += pieces[:-1]
        current = pieces[-1]
        used = sum(unit[1] for unit in current)
    if current or not lines:
        lines.append(current)
    return lines


def _paragraphs(text: str) -> list[str]:
    """Split at line breaks outside escape sequences, as ``str.splitlines`` would."""
    out: list[str] = []
    current: list[str] = []  # joined once per paragraph, so many pieces stay linear
    for piece, escape in pieces(text):
        for part in piece.splitlines(keepends=True):
            body = part if escape else (part.splitlines() or [""])[0]
            current.append(body)
            if body != part:
                out.append("".join(current))
                current = []
    if any(current):
        out.append("".join(current))
    return out


def wrap(
    text: str, width: int, *, max_lines: int | None = None, ellipsis: str = ELLIPSIS
) -> list[str]:
    r"""Wrap ``text`` into lines of at most ``width`` columns.

    Lines break at spaces (U+0020 only); a word wider than ``width`` breaks between
    grapheme clusters. Line breaks in ``text`` start new paragraphs. The leading spaces of
    a paragraph are its indent: kept when the first word fits after them, dropped when the
    word fits a line but not after them, and kept before a word that has to break anyway.
    A single cluster wider than ``width`` gets a line of its own, the only case where a
    line is wider. With ``max_lines``, the lines after it are dropped and the last kept
    line ends with ``ellipsis``, followed by the escape sequences of the dropped text.

    >>> wrap("The quick brown fox jumps", 10)
    ['The quick', 'brown fox', 'jumps']
    >>> wrap("The quick brown fox jumps", 10, max_lines=2, ellipsis="...")
    ['The quick', 'brown f...']
    >>> wrap("  Indented first line\nsecond paragraph", 12)
    ['  Indented', 'first line', 'second', 'paragraph']

    Raises ``TypeError`` for arguments of the wrong type and ``ValueError`` for a
    ``width`` or ``max_lines`` below 1, or a line of ``text`` (or the ``ellipsis``)
    holding a control character outside an escape sequence, such as a tab, or ending
    inside an unfinished one.
    """
    text_arg("text", text)
    int_arg("width", width, 1)
    if max_lines is not None:
        int_arg("max_lines", max_lines, 1)
    line_arg("ellipsis", ellipsis)
    lines: list[list[Unit]] = []
    for paragraph in _paragraphs(text):
        lines += _paragraph(line_arg("text line", paragraph), width)
    if max_lines is None or len(lines) <= max_lines:
        return ["".join(unit[0] for unit in line) for line in lines]
    dropped = [(found, 0, True) for line in lines[max_lines:] for found in escapes_of(line)]
    # An empty unit too wide for any budget forces the cut after the last kept line.
    last = cut([*lines[max_lines - 1], ("", width + 1, False), *dropped], width, ellipsis, "end")
    return ["".join(unit[0] for unit in line) for line in lines[: max_lines - 1]] + [last]
