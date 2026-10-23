"""Contracts added after the author mutation round: each pins a rule a mutant got past."""

from __future__ import annotations

import pytest

from colfit import columnize, display_width, pad


@pytest.mark.parametrize("introducer", ["\x90", "\x98", "\x9e", "\x9f"])
def test_an_8_bit_control_string_runs_to_its_terminator_or_the_end(introducer: str) -> None:
    # DCS, SOS, PM and APC as single 8-bit characters, with no ESC anywhere in the text.
    assert display_width("ab" + introducer + "junk") == 2
    assert display_width("ab" + introducer + "junk\x9cxy") == 4


def test_a_linker_with_no_consonant_before_it_makes_no_conjunct() -> None:
    # Marks take no columns, so a cluster that starts with a virama is just its consonant.
    assert display_width("\u094d\u0915") == 1
    assert display_width("\u0301\u094d\u0915") == 1
    assert display_width("\u0915\u094d\u0915") == 2


def test_columnize_strips_only_ascii_spaces_at_line_ends() -> None:
    items = ["a\u3000", "b\u00a0"]
    assert columnize(items, 3) == "a\u3000\nb\u00a0"
    assert pad("a\u3000", 4) == "a\u3000 "
