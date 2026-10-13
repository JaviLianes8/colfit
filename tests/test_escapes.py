"""Escape sequences: byte ranges derived by hand from ECMA-48 sections 5.3 to 5.6.

The OSC ending with BEL is the xterm convention. Each sequence measures zero and is kept
whole when the text around it is cut.
"""

from __future__ import annotations

import pytest

from colfit import display_width, truncate
from colfit._escapes import pieces, strip

SEQUENCES = [
    "\x1b[0m",  # CSI with a parameter and a final byte
    "\x1b[38;2;255;128;0m",  # several parameters
    "\x1b[?25l",  # private parameter string (first byte 0x3F)
    "\x1b[ q",  # an intermediate byte (0x20) before the final byte
    "\x1b[@",  # no parameters, lowest final byte
    "\x1b[~",  # highest final byte
    "\x9b31m",  # the 8-bit CSI
    "\x1b]8;;https://example.com/a?b=c\x1b\\",  # OSC ended by ST
    "\x1b]0;title\x07",  # OSC ended by BEL (xterm)
    "\x9d0;title\x9c",  # 8-bit OSC and ST
    "\x1bP1$r0m\x1b\\",  # DCS
    "\x1bXany\x07thing\x1b\\",  # SOS: BEL does not end it
    "\x1b^private\x1b\\",  # PM
    "\x1b_app\x1b\\",  # APC
    "\x1bE",  # a C1 function in 7-bit form (NEL)
    "\x1bc",  # an independent control function (RIS)
    "\x1b(B",  # designate a character set: intermediate and final
    "\x1b7",  # a private function (DECSC)
]


@pytest.mark.parametrize("sequence", SEQUENCES)
def test_each_sequence_is_one_escape_piece(sequence: str) -> None:
    assert pieces("a" + sequence + "b") == [("a", False), (sequence, True), ("b", False)]


@pytest.mark.parametrize("sequence", SEQUENCES)
def test_each_sequence_takes_no_columns(sequence: str) -> None:
    assert display_width(sequence + "ab" + sequence) == 2


def test_text_without_escapes_is_one_piece() -> None:
    assert pieces("plain \u00e9") == [("plain \u00e9", False)]
    assert pieces("") == []


def test_unfinished_sequences_run_to_the_end() -> None:
    assert pieces("a\x1b[31") == [("a", False), ("\x1b[31", True)]
    assert pieces("a\x1b]8;;http://x") == [("a", False), ("\x1b]8;;http://x", True)]
    assert pieces("a\x1b") == [("a", False), ("\x1b", True)]
    assert pieces("a\x1bPq#0") == [("a", False), ("\x1bPq#0", True)]


def test_a_sequence_broken_by_a_character_out_of_range_ends_there() -> None:
    assert pieces("\x1b[31\u00e9x") == [("\x1b[31", True), ("\u00e9x", False)]


def test_adjacent_sequences_are_separate_pieces() -> None:
    assert pieces("\x1b[1m\x1b[31m") == [("\x1b[1m", True), ("\x1b[31m", True)]


def test_strip_removes_only_escape_sequences() -> None:
    assert strip("\x1b[1mbold\x1b[0m \x1b]8;;u\x07link\x1b]8;;\x07") == "bold link"


def test_c1_characters_that_open_nothing_are_plain_text() -> None:
    assert pieces("a\x85b") == [("a\x85b", False)]


def test_cut_keeps_the_sequences_of_the_removed_text_after_the_ellipsis() -> None:
    text = "\x1b]8;;https://x.y\x1b\\a long link\x1b]8;;\x1b\\"
    assert truncate(text, 4) == "\x1b]8;;https://x.y\x1b\\a l\u2026\x1b]8;;\x1b\\"
