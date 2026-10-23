"""Regenerate src/colfit/_tables.py from the Unicode data files in tests/sources.

Run `python scripts/fetch_sources.py` first. The output holds code point ranges and property
values derived from the data, never its text.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "tests" / "sources"
TARGET = ROOT / "src" / "colfit" / "_tables.py"
VERSION = "18.0.0"
HANGUL = range(0xAC00, 0xD7A4)  # LV and LVT syllables, computed in code instead

# Single letters for the grapheme classes; digits and lower case letters encode numbers.
GCB = {
    "CR": "R",
    "LF": "N",
    "Control": "C",
    "Extend": "E",
    "ZWJ": "J",
    "Regional_Indicator": "I",
    "Prepend": "P",
    "SpacingMark": "S",
    "L": "L",
    "V": "V",
    "T": "T",
}
INCB = {"Extend": "X", "Linker": "K", "Consonant": "O"}


def records(name: str, field: int = 1) -> list[tuple[int, int, str]]:
    """(first, last, value) for every data line of a UCD file."""
    out = []
    for line in (SOURCES / name).read_text(encoding="utf-8").splitlines():
        data = line.split("#", 1)[0].strip()
        if not data:
            continue
        fields = [part.strip() for part in data.split(";")]
        first, _, last = fields[0].partition("..")
        out.append((int(first, 16), int(last or first, 16), ";".join(fields[field:])))
    return out


def missing_defaults(name: str) -> list[tuple[int, int, str]]:
    """The `@missing` lines, which give the value of code points the file does not list."""
    out = []
    pattern = re.compile(r"# @missing: ([0-9A-F]+)\.\.([0-9A-F]+); (\w+)")
    for match in pattern.finditer((SOURCES / name).read_text(encoding="utf-8")):
        out.append((int(match.group(1), 16), int(match.group(2), 16), match.group(3)))
    return out


def grapheme_classes() -> dict[int, str]:
    classes: dict[int, str] = {}
    for first, last, value in records("GraphemeBreakProperty.txt"):
        if value in ("LV", "LVT"):
            continue
        for code in range(first, last + 1):
            classes[code] = GCB[value]
    for first, last, value in records("emoji-data.txt"):
        if value == "Extended_Pictographic":
            for code in range(first, last + 1):
                assert code not in classes, f"ExtPict {code:X} has a grapheme class"
                classes[code] = "Q"
    return classes


def conjunct_classes() -> dict[int, str]:
    classes: dict[int, str] = {}
    for first, last, value in records("DerivedCoreProperties.txt"):
        prop, _, incb = value.partition(";")
        if prop == "InCB":
            for code in range(first, last + 1):
                classes[code] = INCB[incb]
    return classes


def width_classes() -> dict[int, str]:
    """``W`` two columns, ``Z`` none, ``M`` a spacing mark (none alone, widens its cluster)."""
    widths: dict[int, str] = {}
    eaw: dict[int, str] = {}
    for first, last, value in [
        *missing_defaults("EastAsianWidth.txt"),
        *records("EastAsianWidth.txt"),
    ]:
        for code in range(first, last + 1):
            eaw[code] = value
    for code, value in eaw.items():
        if value in ("W", "F"):
            widths[code] = "W"
    for first, last, value in records("DerivedGeneralCategory.txt"):
        if value in ("Mn", "Me", "Cf", "Cc", "Zl", "Zp", "Mc"):
            for code in range(first, last + 1):
                widths[code] = "M" if value == "Mc" else "Z"
    for first, last, value in records("DerivedCoreProperties.txt"):
        if value == "Default_Ignorable_Code_Point":
            for code in range(first, last + 1):
                if code != 0x115F:  # the Hangul leading filler starts a wide syllable block
                    widths[code] = "Z"
    for first, last, value in records("PropList.txt"):
        if value == "Prepended_Concatenation_Mark":
            for code in range(first, last + 1):
                del widths[code]  # format characters drawn with the digits that follow
    for first, last, value in records("GraphemeBreakProperty.txt"):
        if value == "Regional_Indicator":
            for code in range(first, last + 1):
                widths[code] = "W"  # drawn as a wide letter, and a pair as one wide flag
    for code in [*range(0x1160, 0x1200), *range(0xD7B0, 0xD800)]:
        widths[code] = "Z"  # Hangul medial vowels and final consonants join the syllable
    del widths[0xAD]  # soft hyphen: a format character that terminals draw as a hyphen
    return widths


def variation_bases() -> dict[int, str]:
    bases = {}
    text = (SOURCES / "emoji-variation-sequences.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        sequence = line.split(";", 1)[0].split()
        if sequence and not line.startswith("#"):
            assert sequence[1] in ("FE0E", "FE0F"), line
            bases[int(sequence[0], 16)] = "B"
    return bases


def encode(classes: dict[int, str]) -> list[str]:
    """Runs of equal class as `<gap><class><length - 1> `, numbers in base 36."""
    runs: list[list[int | str]] = []
    for code in sorted(classes):
        value = classes[code]
        if runs and runs[-1][1] == code - 1 and runs[-1][2] == value:
            runs[-1][1] = code
        else:
            runs.append([code, code, value])
    tokens, after = [], 0
    for first, last, value in runs:
        assert isinstance(first, int) and isinstance(last, int)
        tokens.append(f"{_b36(first - after)}{value}{_b36(last - first)} ")
        after = last + 1
    lines, line = [], ""
    for token in tokens:
        if len(line) + len(token) > 88:
            lines.append(line)
            line = ""
        line += token
    return [*lines, line]


def _b36(number: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    text = ""
    while True:
        number, rest = divmod(number, 36)
        text = digits[rest] + text
        if not number:
            return text


def render() -> str:
    out = [
        f'"""Unicode {VERSION} property runs, generated by scripts/gen_tables.py.',
        "",
        "Derived from the Unicode data files GraphemeBreakProperty.txt, emoji-data.txt,",
        "DerivedCoreProperties.txt, EastAsianWidth.txt, DerivedGeneralCategory.txt, PropList.txt",
        "and emoji-variation-sequences.txt. Copyright Unicode, Inc., Unicode License v3: see",
        "LICENSES/Unicode-3.0.txt (in the wheel, in the licenses folder of its metadata).",
        '"""',
        "",
    ]
    out.append(f'UNICODE_VERSION = "{VERSION}"')
    for name, table in (
        ("GRAPHEME", grapheme_classes()),
        ("CONJUNCT", conjunct_classes()),
        ("WIDTH", width_classes()),
        ("VARIATION", variation_bases()),
    ):
        out.append(f"{name} = (")
        out += [f'    "{line}"' for line in encode(table)]
        out.append(")")
    return "\n".join(out) + "\n"


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        return 0 if TARGET.read_text(encoding="utf-8") == render() else 1
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
