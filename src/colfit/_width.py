"""Terminal display width of text, measured per grapheme cluster."""

from __future__ import annotations

from collections.abc import Iterator

from ._check import text_arg
from ._escapes import pieces
from ._graphemes import clusters
from ._unicode import char_width, conjunct_class, grapheme_class, has_variations, is_spacing_mark

_ZWJ = "\u200d"
_TEXT_STYLE = "\ufe0e"
_EMOJI_STYLE = "\ufe0f"
_MODIFIERS = ("\U0001f3fb", "\U0001f3ff")  # the five skin tone modifiers

Unit = tuple[str, int, bool]
"""A grapheme cluster or an escape sequence: ``(text, columns, is_escape)``.

A cluster that has escape sequences inside it keeps them in its text.
"""


def cluster_width(cluster: str) -> int:
    """Columns one grapheme cluster takes."""
    start = 0
    prepended = 0
    while start < len(cluster) - 1 and grapheme_class(cluster[start]) == "P":
        prepended += char_width(cluster[start])  # drawn before the cluster it joins
        start += 1
    if start and is_spacing_mark(cluster[start]) and char_width(cluster[start - 1]):
        # A spacing mark right after a visible prepended character widens it, as it
        # widens any other base.
        start -= 1
        prepended -= char_width(cluster[start])
    base = cluster[start]
    width = char_width(base)
    emoji = grapheme_class(base) == "Q"
    previous = base
    for char in cluster[start + 1 :]:
        if char == _EMOJI_STYLE:
            if has_variations(base):
                width = 2
        elif char == _TEXT_STYLE:
            if has_variations(base):
                width = 1
        elif emoji:
            zwj_sequence = previous == _ZWJ and grapheme_class(char) == "Q"
            if zwj_sequence or _MODIFIERS[0] <= char <= _MODIFIERS[1]:
                width = 2  # a zwj or modifier sequence is drawn as one emoji (UTS #51)
        elif width and is_spacing_mark(char):
            width = 2
        elif width and conjunct_class(char) == "O":
            width = 2  # consonant, linker, consonant: one conjunct
        elif previous != _ZWJ and grapheme_class(char) != "I":
            width += char_width(char)
        previous = char
    return prepended + width


def measured(visible: str) -> Iterator[tuple[str, int]]:
    """The clusters of ``visible`` text with the columns each takes there."""
    syllable = 0  # columns of the last cluster that did not start with a spacing mark
    for cluster in clusters(visible):
        width = cluster_width(cluster)
        if not is_spacing_mark(cluster[0]):
            syllable = width
        elif syllable == 1:
            # A spacing mark UAX #29 leaves out of the cluster before it still widens it.
            width += 1
            syllable = 2
        yield cluster, width


def _plain(text: str) -> bool:
    return text.isascii() and text.isprintable()


def units(text: str) -> list[Unit]:
    """Split ``text`` into grapheme clusters and escape sequences, with their widths.

    Clusters are found in the visible text, so an escape sequence never splits one.
    """
    found = pieces(text)
    if len(found) == 1 and not found[0][1]:
        if _plain(text):
            return [(char, 1, False) for char in text]
        return [(cluster, width, False) for cluster, width in measured(text)]
    out: list[Unit] = []
    visible = measured("".join(piece for piece, escape in found if not escape))
    width, missing = 0, 0
    held: list[str] = []  # the pieces of the cluster being built, joined once at its end
    for piece, escape in found:
        if escape:
            if missing:
                held.append(piece)  # inside a cluster: it stays there
            else:
                out.append((piece, 0, True))
            continue
        at = 0
        while at < len(piece):
            if not missing:
                cluster, width = next(visible)
                missing, held = len(cluster), []
            step = min(missing, len(piece) - at)
            held.append(piece[at : at + step])
            at, missing = at + step, missing - step
            if not missing:
                out.append(("".join(held), width, False))
    return out


def escapes_of(line: list[Unit]) -> list[str]:
    """The escape sequences ``line`` holds, also those inside clusters, in order."""
    found = []
    for text, _, escape in line:
        if escape:
            found.append(text)
        elif len(text) > 1:
            found += [piece for piece, inside in pieces(text) if inside]
    return found


def width_of(text: str) -> int:
    if _plain(text):
        return len(text)
    visible = "".join(piece for piece, escape in pieces(text) if not escape)
    if _plain(visible):
        return len(visible)
    return sum(width for _, width in measured(visible))


def display_width(text: str) -> int:
    r"""Return the number of terminal columns ``text`` takes.

    Text is measured per extended grapheme cluster (UAX #29) with the Unicode 18.0.0
    tables: East Asian Wide and Fullwidth characters take two columns; marks, format,
    default ignorable and control characters none; an emoji sequence, a flag or a cluster
    with a spacing mark or a conjunct two. Escape sequences take none and never split a
    cluster.

    >>> display_width("abc"), display_width("\u65e5\u672c"), display_width("e\u0301")
    (3, 4, 1)
    >>> display_width("\U0001f468\u200d\U0001f469\u200d\U0001f467")  # one family emoji
    2
    >>> display_width("\x1b[31mred\x1b[0m")
    3

    Raises ``TypeError`` when ``text`` is not a ``str``.
    """
    return width_of(text_arg("text", text))
