"""Wrap text into lines that fit a number of terminal columns."""

from __future__ import annotations

from ._check import int_arg, line_arg, text_arg
from ._fit import ELLIPSIS, cut, take
from ._width import Unit, units


def _chunks(word: list[Unit], width: int) -> list[list[Unit]]:
    """Break a word too wide for a line at cluster boundaries."""
    out = []
    while word:
        # A single cluster wider than the line still has to go somewhere: alone.
        count = max(take(word, width), 1)
        while count < len(word) and word[count][2]:
            count += 1  # an escape sequence stays with the text before it
        out.append(word[:count])
        word = word[count:]
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
    if out and out[0][0]:
        out[0] = ([], out[0][0] + out[0][1])  # leading spaces are the indent
    return out


def _paragraph(text: str, width: int) -> list[list[Unit]]:
    lines: list[list[Unit]] = []
    current: list[Unit] = []
    used = 0
    for spaces, word in _words(units(text)):
        size = sum(unit[1] for unit in word)
        if current and used + len(spaces) + size <= width:
            current += spaces + word
            used += len(spaces) + size
            continue
        if current:
            lines.append(current)
        pieces = _chunks(word, width) if size > width else [word]
        lines += pieces[:-1]
        current = pieces[-1]
        used = sum(unit[1] for unit in current)
    if current or not lines:
        lines.append(current)
    return lines


def wrap(
    text: str, width: int, *, max_lines: int | None = None, ellipsis: str = ELLIPSIS
) -> list[str]:
    """Wrap ``text`` into lines of at most ``width`` columns.

    Lines break at spaces; a word wider than ``width`` breaks between grapheme clusters.
    Line breaks in ``text`` start new paragraphs, and leading spaces of a paragraph are
    kept as its indent. A single cluster wider than ``width`` gets a line of its own, the
    only case where a line is wider. With ``max_lines``, the lines after it are dropped
    and the last kept line ends with ``ellipsis``, followed by the escape sequences of
    the dropped text.
    """
    text_arg("text", text)
    int_arg("width", width, 1)
    if max_lines is not None:
        int_arg("max_lines", max_lines, 1)
    line_arg("ellipsis", ellipsis)
    lines: list[list[Unit]] = []
    for paragraph in text.splitlines():
        lines += _paragraph(line_arg("text line", paragraph), width)
    if max_lines is None or len(lines) <= max_lines:
        return ["".join(unit[0] for unit in line) for line in lines]
    dropped = [unit for line in lines[max_lines:] for unit in line if unit[2]]
    # An empty unit too wide for any budget forces the cut after the last kept line.
    last = cut([*lines[max_lines - 1], ("", width + 1, False), *dropped], width, ellipsis, "end")
    return ["".join(unit[0] for unit in line) for line in lines[: max_lines - 1]] + [last]
