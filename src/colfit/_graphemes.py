"""Extended grapheme clusters (UAX #29), so a cut never splits what reads as one character."""

from __future__ import annotations

from collections.abc import Iterator

from ._check import text_arg
from ._unicode import conjunct_class, grapheme_class

_CONTROLS = frozenset("RNC")


def _joined(before: str, after: str, emoji_zwj: bool, linker: bool, odd_ri: bool) -> bool:
    if before == "R" and after == "N":
        return True  # GB3
    if before in _CONTROLS or after in _CONTROLS:
        return False  # GB4, GB5
    if before == "L" and after in "LVHY":
        return True  # GB6
    if before in "HV" and after in "VT":
        return True  # GB7
    if before in "YT" and after == "T":
        return True  # GB8
    if after in "EJS" or before == "P":
        return True  # GB9, GB9a, GB9b
    if linker:
        return True  # GB9c, checked by the caller against the next character
    if emoji_zwj and after == "Q":
        return True  # GB11
    return before == after == "I" and odd_ri  # GB12, GB13


def clusters(text: str) -> Iterator[str]:
    """The extended grapheme clusters of ``text``, one at a time."""
    start = 0
    before = ""
    emoji = False  # an Extended_Pictographic followed by Extend characters only
    emoji_zwj = False  # the previous character is a ZWJ that follows such an emoji
    linker = False  # a Linker followed by InCB Extend characters only
    ri_run = 0
    for index, char in enumerate(text):
        after = grapheme_class(char)
        conjunct = conjunct_class(char)
        if index and not _joined(
            before, after, emoji_zwj, linker and conjunct == "O", ri_run % 2 == 1
        ):
            yield text[start:index]
            start = index
        emoji_zwj = after == "J" and emoji
        emoji = after == "Q" or (emoji and after == "E")
        linker = conjunct == "K" or (linker and conjunct == "X")
        ri_run = ri_run + 1 if after == "I" else 0
        before = after
    if text:
        yield text[start:]


def graphemes(text: str) -> list[str]:
    r"""Split ``text`` into extended grapheme clusters (UAX #29, Unicode 18.0.0).

    A cluster is what a reader sees as one character: a letter with its accents, a
    Hangul syllable, an emoji sequence, a flag. Escape sequences get no special treatment
    here. Joining the clusters gives ``text`` back.

    >>> graphemes("e\u0301a") == ["e\u0301", "a"]
    True
    >>> len(graphemes("\U0001f1ea\U0001f1f8\U0001f44d\U0001f3fd"))  # a flag, a thumb
    2
    >>> graphemes("")
    []

    Raises ``TypeError`` when ``text`` is not a ``str``.
    """
    return list(clusters(text_arg("text", text)))
