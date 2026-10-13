"""Ground truth read from the Unicode 18.0.0 files and UAX #29 as fetched for this round."""

from __future__ import annotations

import html
import importlib.util
import re
import sys
import unicodedata
from collections.abc import Callable
from pathlib import Path

from conftest import code_points

from colfit import display_width, graphemes
from colfit._tables import UNICODE_VERSION

Reader = Callable[[str], str]
ROOT = Path(__file__).resolve().parents[1]


def _break_cases(text: str) -> list[list[str]]:
    cases = []
    for line in text.splitlines():
        data = line.split("#", 1)[0].strip()
        if not data:
            continue
        clusters = [code_points(part.replace("\u00d7", " ")) for part in data.split("\u00f7")]
        cases.append([cluster for cluster in clusters if cluster])
    return cases


def test_the_tables_are_unicode_18(source: Reader) -> None:
    assert UNICODE_VERSION == "18.0.0"
    assert "GraphemeBreakTest-18.0.0.txt" in source("GraphemeBreakTest.txt")
    assert "EastAsianWidth-18.0.0.txt" in source("EastAsianWidth.txt")


def test_every_line_of_the_grapheme_break_test_splits_as_listed(source: Reader) -> None:
    cases = _break_cases(source("GraphemeBreakTest.txt"))
    assert len(cases) > 800
    failures = [case for case in cases if graphemes("".join(case)) != case]
    assert failures == []


def test_every_fully_qualified_emoji_is_one_cluster_two_columns(source: Reader) -> None:
    seen = 0
    for line in source("emoji-test.txt").splitlines():
        data = line.split("#", 1)[0]
        if "; fully-qualified" in data or "; component" in data:
            emoji = code_points(data.split(";")[0])
            assert graphemes(emoji) == [emoji], line
            assert display_width(emoji) == 2, line
            seen += 1
    assert seen > 3500


def test_the_implemented_rules_are_those_of_the_fetched_annex(source: Reader) -> None:
    text = html.unescape(re.sub(r"<[^>]+>", " ", source("tr29-49.html")))
    text = re.sub(r"\s+", " ", text)
    assert "Unicode 18.0.0" in text
    # <x> stands for the "do not break" sign of the annex.
    for rule in (
        r"GB3 CR <x> LF",
        r"GB6 L <x> (L | V | LV | LVT)",
        r"GB7 (LV | V) <x> (V | T)",
        r"GB8 (LVT | T) <x> T",
        r"GB9 <x> (Extend | ZWJ)",
        r"GB9a <x> SpacingMark",
        r"GB9b Prepend <x>",
        r"GB9c \p{InCB=Linker} \p{InCB=Extend}* <x> \p{InCB=Consonant}",
        r"GB11 \p{Extended_Pictographic} Extend* ZWJ <x> \p{Extended_Pictographic}",
        r"GB12 sot (RI RI)* RI <x> RI",
        r"GB13 [^RI] (RI RI)* RI <x> RI",
    ):
        assert rule.replace("<x>", "\u00d7") in text, rule


def _east_asian_width(text: str) -> dict[int, str]:
    classes: dict[int, str] = {}
    for first, last, value in re.findall(r"# @missing: (\w+)\.\.(\w+); (\w+)", text):
        classes.update(dict.fromkeys(range(int(first, 16), int(last, 16) + 1), value))
    for line in text.splitlines():
        data = line.split("#", 1)[0].strip()
        if data:
            span, value = (part.strip() for part in data.split(";"))
            first, _, last = span.partition("..")
            classes.update(dict.fromkeys(range(int(first, 16), int(last or first, 16) + 1), value))
    return classes


def test_visible_wide_and_fullwidth_characters_take_two_columns(source: Reader) -> None:
    classes = _east_asian_width(source("EastAsianWidth.txt"))
    ignorable = re.findall(
        r"^(\w+)(?:\.\.(\w+))? +; Default_Ignorable_Code_Point",
        source("DerivedCoreProperties.txt"),
        flags=re.MULTILINE,
    )
    skip = {
        *range(0x1160, 0x1200),  # Hangul medial and final jamo, drawn inside the syllable
        *range(0xD7B0, 0xD800),
        *range(0x1F1E6, 0x1F200),  # regional indicators, drawn wide (tested elsewhere)
    }
    for first, last in ignorable:
        skip.update(range(int(first, 16), int(last or first, 16) + 1))
    # Letters, digits, punctuation and symbols are drawn; marks and formats are not.
    visible = re.compile(r"[LNPS]")
    checked = 0
    for code, value in classes.items():
        char = chr(code)
        if code in skip or not visible.match(unicodedata.category(char)):
            continue
        expected = 2 if value in ("W", "F") else 1
        assert display_width(char) == expected, f"{code:04X} {value}"
        checked += 1
    assert checked > 100_000


def test_the_generated_tables_match_the_sources(source: Reader) -> None:
    source("GraphemeBreakProperty.txt")
    spec = importlib.util.spec_from_file_location("gen_tables", ROOT / "scripts" / "gen_tables.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode, before = True, sys.dont_write_bytecode
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = before
    expected = (ROOT / "src" / "colfit" / "_tables.py").read_text(encoding="utf-8")
    assert module.render() == expected
