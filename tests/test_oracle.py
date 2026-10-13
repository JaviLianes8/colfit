"""wcwidth, the reference for what terminals draw, agrees with colfit where both are sure.

wcwidth is a test oracle only (pinned in the dev extras), never a runtime dependency.
"""

from __future__ import annotations

import random
import unicodedata
from collections.abc import Callable

import pytest
from conftest import code_points

from colfit import display_width
from colfit._unicode import conjunct_class

wcwidth = pytest.importorskip("wcwidth")
if wcwidth.__version__ != "0.9.2":
    pytest.skip("the oracle is pinned to wcwidth 0.9.2", allow_module_level=True)


def _reference(text: str) -> int:
    return int(wcwidth.width(text, control_codes="ignore"))


def test_every_code_point_alone_measures_as_in_wcwidth() -> None:
    differ = []
    for code in range(0x110000):
        char = chr(code)
        if unicodedata.category(char) == "Cs":
            continue
        if display_width(char) != _reference(char):
            differ.append(f"{code:04X}")
    assert differ == []


def _text_default_sequence(emoji: str) -> bool:
    """A zwj or modifier sequence on a base whose default presentation is text."""
    joined = "\u200d" in emoji or any("\U0001f3fb" <= char <= "\U0001f3ff" for char in emoji)
    return joined and wcwidth.wcwidth(emoji[0]) == 1 and "\ufe0f" not in emoji


def test_emoji_sequences_agree_except_text_default_sequences(
    source: Callable[[str], str],
) -> None:
    # UTS #51 draws every zwj and modifier sequence as one emoji, two columns; wcwidth
    # keeps the text width of a base that has no emoji presentation selector.
    agree = differ = 0
    for line in source("emoji-test.txt").splitlines():
        data = line.split("#", 1)[0]
        if ";" not in data:
            continue
        emoji = code_points(data.split(";")[0])
        if _text_default_sequence(emoji):
            assert (display_width(emoji), _reference(emoji)) == (2, 1), line
            differ += 1
        else:
            assert display_width(emoji) == _reference(emoji), line
            agree += 1
    assert agree > 5000
    assert 0 < differ < 120


@pytest.mark.parametrize("first", [0x900, 0x980, 0xA80, 0xB00, 0xC00, 0xD00])
def test_words_of_scripts_with_conjuncts_agree(first: int) -> None:
    # Syllables as written: consonant, optional linker and consonant, optional vowel sign.
    block = [chr(code) for code in range(first, first + 0x80)]
    consonants = [c for c in block if conjunct_class(c) == "O"]
    linkers = [c for c in block if conjunct_class(c) == "K"]
    signs = [c for c in block if unicodedata.category(c) in ("Mn", "Mc") and c not in linkers]
    rng = random.Random(first)
    for _ in range(2000):
        word = ""
        for _ in range(rng.randint(1, 4)):
            word += rng.choice(consonants)
            if rng.random() < 0.3:
                word += rng.choice(linkers) + rng.choice(consonants)
            if rng.random() < 0.6:
                word += rng.choice(signs)
        assert display_width(word) == _reference(word), [f"{ord(c):04X}" for c in word]


def test_hangul_syllables_and_jamo_agree() -> None:
    rng = random.Random(11)
    leading = [chr(c) for c in range(0x1100, 0x1160)]
    vowels = [chr(c) for c in range(0x1161, 0x11A8)]
    trailing = [chr(c) for c in range(0x11A8, 0x1200)]
    for _ in range(3000):
        syllable = chr(rng.randrange(0xAC00, 0xD7A4))
        if rng.random() < 0.5:
            syllable += rng.choice(trailing)
        jamo = rng.choice(leading) + rng.choice(vowels) + rng.choice(trailing)
        for text in (syllable, jamo, syllable + jamo):
            assert display_width(text) == _reference(text)


def test_styled_and_linked_text_agrees() -> None:
    samples = [
        "\x1b[1;31mbold red\x1b[0m",
        "\x1b]8;;https://example.com\x1b\\link\x1b]8;;\x1b\\",
        "\x1b]8;;https://example.com\x07link\x1b]8;;\x07",
        "\x1b[38;5;208m\u65e5\u672c\x1b[39m",
        "\x1b(Bplain",
    ]
    for text in samples:
        assert display_width(text) == _reference(text), text
