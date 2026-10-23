# colfit guide

Every rule of every public name, with examples. Each Python block below runs as a test: a
run of comment lines right under the code holds what the code prints.

## Widths

`display_width` measures per extended grapheme cluster (UAX #29) with tables generated
from Unicode 18.0.0, so every Python version gives the same answer.

- East Asian Wide and Fullwidth characters take two columns; ambiguous ones take one.
- Marks, format characters (a ZWJ hides nothing after it), default ignorable code points,
  Hangul medial and final jamo and control characters take none; a soft hyphen takes one.
- An emoji ZWJ sequence (a ZWJ between two pictographs), a flag, a single regional
  indicator and a skin tone modifier after any emoji take two. The modifier rule is wider
  than UTS #51, which shows a swatch after a base that has no skin tone form.
- A presentation selector anywhere in a cluster (after marks or a ZWJ too) acts on its base
  only: on one with variation sequences, U+FE0F makes it two columns and U+FE0E one.
- A spacing vowel sign or a conjunct (consonant, linker, consonant, and any more after a
  linker or a ZWJ) makes its syllable two, and so does a spacing mark alone in its cluster
  (Myanmar, Tai Tham, Ahom, or after a soft hyphen, where other marks take none) or after
  a prepended character with no other base (U+0600, U+0D4E; a letter after it, even a jamo,
  is a base), with any marks or ZWJ between; else a prepended character adds its own width.
- Escape sequences take none and never split a cluster (see below).

```python
from colfit import display_width, graphemes

plain = ["abc", "\u65e5\u672c", "e\u0301", "\x1b[1mbold\x1b[0m", "\u0915\u094d\u0937\u093f"]
emoji = ["\U0001f44d\U0001f3fd", "\U0001f1ea\U0001f1f8", "\u2764", "\u2764\ufe0f"]
print([display_width(text) for text in plain], [display_width(text) for text in emoji])
print(graphemes("e\u0301\U0001f44d\U0001f3fd!") == ["e\u0301", "\U0001f44d\U0001f3fd", "!"])
# [3, 4, 1, 4, 2] [2, 2, 1, 2]
# True
```

## Escape sequences

Terminals act on escape sequences (ECMA-48) but never draw them. colfit knows CSI (`ESC [`
or the 8-bit CSI, as in colours), OSC strings (`ESC ]`, hyperlinks and titles, ended by ST
or BEL), DCS, SOS, PM and APC strings up to ST, and any other `ESC` sequence. A sequence
cut short by a character that cannot be part of it ends there; a control string also ends
before an `ESC` that does not start ST and before `CAN` or `SUB`, as the DEC parser does.

They take no columns, they are never cut, and the ones in removed text are kept right
after the ellipsis, so colours and links still close:

```python
from colfit import truncate

link = "\x1b]8;;https://example.com\x1b\\Example site\x1b]8;;\x1b\\"
print(repr(truncate(link, 8, ellipsis="...")))
red = "\x1b[31mwarning: disk almost full\x1b[0m"
print(repr(truncate(red, 10)))
# '\x1b]8;;https://example.com\x1b\\Examp...\x1b]8;;\x1b\\'
# '\x1b[31mwarning: …\x1b[0m'
```

A text that ends inside an unfinished sequence (a lone `ESC`, a colour code without its
final letter, a hyperlink without its terminator) would swallow whatever is written after
it, so `truncate`, `pad`, `fit`, `wrap` and `columnize` refuse it with `ValueError`.
`display_width` and `graphemes` take any text; the unfinished sequence runs to the end.

```python
from colfit import display_width, pad

print(display_width("ab\x1b]8;;https://example.com"))
try:
    pad("ab\x1b[31", 5)
except ValueError as error:
    print(error)
# 2
# text ends inside an unfinished escape sequence
```

## Cutting and padding

- `truncate` returns text that fits unchanged. Otherwise it replaces part of it with the
  ellipsis: at the end, at the start, or in the middle, where the start gets the odd
  column. Clusters are never split, so the result can be short of the width by less than
  the width of the cluster that did not fit; an ellipsis wider than the width is itself cut.
- `pad` adds `fill` to reach the width and returns wider text unchanged. Centring puts the
  odd column on the right, as `format(text, "^5")` does (`str.center` and
  `wcwidth.center` put it on the left when the width is odd).
- `fit` is `truncate` then `pad`: always exactly the width.
- Results are measured as written. An ellipsis whose first character joins the last kept
  cluster (a combining mark, a ZWJ, a variation selector) makes `truncate` keep less, so
  more columns can stay free; with an empty ellipsis in the middle the kept ends meet and
  can join too (two lone regional indicators make a flag). Text that starts or ends with
  such a character gets its fill where the width comes out exact; a `fill` may not be one.

```python
from colfit import fit, pad, truncate

print(truncate("\u65e5\u672c\u8a9e\u30c6\u30ad\u30b9\u30c8", 7, ellipsis="..."))
print(truncate("abcdefghij", 7, side="middle", ellipsis="."))
print("[" + pad("ab", 5, align="center") + "]", "[" + format("ab", "^5") + "]")
print("[" + fit("\u65e5\u672c\u8a9e", 4, ellipsis="") + "]")
# 日本...
# abc.hij
# [ ab  ] [ ab  ]
# [日本]
```

## Wrapping

- Lines break at spaces (U+0020 only: a no-break or ideographic space is part of a word);
  spaces at a break are dropped, spaces between words are kept.
- A word wider than the line starts a new line and breaks between clusters. A single
  cluster wider than the line gets a line of its own, the only line that can be wider.
- Each line break in the text (any `str.splitlines` break outside escape sequences) starts
  a paragraph; an empty paragraph gives an empty line. No text gives no lines.
- The leading spaces of a paragraph are its indent. They are kept when the first word fits
  after them, dropped when the word fits a line but not after them, and kept before a
  word that has to break anyway, as `textwrap` does.
- With `max_lines`, the last line kept ends with the ellipsis and the escapes of the dropped lines.

```python
from colfit import wrap

print(wrap("  one two three\n\nfour", 9))
print(wrap("   abcdefgh xy", 8))
print(wrap("supercalifragilistic", 8))
print(wrap("one two three four five", 9, max_lines=2))
print(wrap("", 5), wrap("   ", 5))
# ['  one two', 'three', '', 'four']
# ['abcdefgh', 'xy']
# ['supercal', 'ifragili', 'stic']
# ['one two', 'three…']
# [] ['']
```

For one line of text with at least one word, when every word and the indent fit a line,
`wrap` gives the same lines as `textwrap.wrap(text, width, break_on_hyphens=False)` on
ASCII text and as `wcwidth.wrap` with the same options on text with wide characters and
emoji. Both break a long word to fill the current line, where `wrap` starts it on a new
one; both treat a line break as a space and give no lines for spaces alone.

## Columns

`columnize` tries the most columns that could fit, then one fewer, and takes the first
layout whose columns, each as wide as its widest cell, fit with `gap` spaces between them.
Row order fills each row left to right; column order fills each column top to bottom with
as few rows as that column count allows, like `ls`. Lines end without trailing spaces, and
items wider than the width end up in a single column. An item may not start with a mark
that joins the text before it; an empty one adds only its gap. With `gap=0` cells touch,
so two that Unicode joins (two regional indicators make a flag) are drawn as one. The time
is linear in the number of items: beyond 32 passes over them and about four million item
visits, the search takes the most columns that fit when each is as wide as the widest
item. A gap too large for memory raises `MemoryError`.

GNU `ls -C -w W` (and `ls -x` for row order) lays names out the same way as
`columnize(names, W - 1)` as long as the search does not stop early (ls has no such limit):
ls leaves the last screen column free and reserves at least three columns for every column,
so the match holds for names of three characters or more.

```python
from colfit import columnize

names = ["README.md", "LICENSE", "pyproject.toml", "src", "tests", "CHANGELOG.md"]
print(columnize(names, 38))
print(columnize(names, 38, order="columns"))
print(columnize(names, 38, gap=1, order="columns"))
# README.md  LICENSE  pyproject.toml
# src        tests    CHANGELOG.md
# README.md       src
# LICENSE         tests
# pyproject.toml  CHANGELOG.md
# README.md pyproject.toml tests
# LICENSE   src            CHANGELOG.md
```

## Errors

Every public function raises `TypeError` for an argument of the wrong type (`bool` is not
a width) and `ValueError` for a value it cannot use; messages quote at most 40 characters.

| Function | `ValueError` when |
| --- | --- |
| `truncate` | `width` below 0, unknown `side`, text or ellipsis with a control character |
| `pad` | `width` below 0 or above `sys.maxsize`, unknown `align`, `fill` not one character one column wide or joining the text before it, text with a control character |
| `fit` | any of the above |
| `wrap` | `width` or `max_lines` below 1, a line or the ellipsis with a control character |
| `columnize` | `width` below 1, `gap` below 0 or above `sys.maxsize`, unknown `order`, an item with a control character or starting with a joining mark |

A control character here is one outside an escape sequence (C0, C1, U+2028, U+2029), or
a text ending inside an unfinished sequence. Tabs are refused too: expand them first with
`str.expandtabs()`. `columnize` raises `TypeError` for a single `str` instead of a list.

## How the results are checked

- The Unicode 18.0.0 files and UAX #29 and #11, fetched from unicode.org and checked
  against the sha256 in `tests/sources/MANIFEST.txt`: every line of
  `GraphemeBreakTest.txt`, every fully qualified emoji of `emoji-test.txt`, and the
  generated tables rebuilt from the data files.
- `wcwidth` 0.9.2 as an independent measure: every code point alone, every emoji of
  `emoji-test.txt`, Devanagari, Bengali, Gujarati, Oriya, Telugu and Malayalam syllables,
  the spacing marks of Myanmar, Tai Tham and Ahom, Hangul, styled text, `wrap`, `ljust`
  and `rjust`, apart from the differences the README lists, each checked too.
- GNU `ls` run live on generated file names, `textwrap.wrap` and `format` alignment.
