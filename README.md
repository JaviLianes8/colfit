# colfit

Fit text to terminal columns: measure it, cut it with an ellipsis, pad or centre it, wrap
it, and lay lists out in columns. Widths follow what a terminal draws: wide East Asian
characters take two columns, accents none, an emoji sequence or a flag two, and escape
sequences (colours, links) none. Nothing is ever cut through the middle of a character.

## Install

```
pip install colfit
```

Python 3.10 or newer, no dependencies.

## Usage

```python
from colfit import display_width, fit, pad, truncate

print(display_width("日本語"), display_width("👩‍👩‍👧"), display_width("\x1b[31mred\x1b[0m"))
# 6 2 3

print(truncate("The quick brown fox", 12))
print(truncate("The quick brown fox", 12, side="middle"))
print(truncate("The quick brown fox", 12, side="start", ellipsis="..."))
# The quick b…
# The qu…n fox
# ...brown fox

print("[" + pad("ok", 6, align="center") + "]")
print("[" + fit("日本語テキスト", 7) + "]")
# [  ok  ]
# [日本語…]
```

`wrap` breaks at spaces, then between characters for words that are too long:

```python
from colfit import wrap

for line in wrap("The quick brown fox jumps over the lazy dog", 12):
    print(line)
# The quick
# brown fox
# jumps over
# the lazy dog

print(wrap("The quick brown fox jumps over the lazy dog", 12, max_lines=2))
# ['The quick', 'brown fox…']
```

`columnize` lays a list out in the most columns that fit, row by row or down the columns
like `ls`:

```python
from colfit import columnize

fruits = ["apple", "fig", "cherry", "date", "elderberry", "kiwi", "lime"]
print(columnize(fruits, width=30))
# apple       fig   cherry  date
# elderberry  kiwi  lime

print(columnize(fruits, width=30, order="columns"))
# apple   date        lime
# fig     elderberry
# cherry  kiwi
```

`graphemes` splits text into what a reader sees as characters:

```python
from colfit import graphemes

text = "🇪🇸👍🏽👩‍👩‍👧"
print(len(text), len(graphemes(text)))
# 9 3
```

## API

| Function | Result |
| --- | --- |
| `display_width(text)` | columns the text takes |
| `graphemes(text)` | the extended grapheme clusters of the text |
| `truncate(text, width, *, ellipsis="…", side="end")` | at most `width` columns, the cut marked |
| `pad(text, width, *, align="left", fill=" ")` | at least `width` columns |
| `fit(text, width, *, align, ellipsis, side, fill)` | exactly `width` columns |
| `wrap(text, width, *, max_lines=None, ellipsis="…")` | a list of lines of at most `width` columns |
| `columnize(items, width=80, *, gap=2, order="rows")` | one string, lines joined by `\n` |

`Align` (`"left"`, `"center"`, `"right"`), `Side` (`"end"`, `"start"`, `"middle"`) and
`Order` (`"rows"`, `"columns"`) are the literal types of those arguments.

## Rules

Width, per extended grapheme cluster (UAX #29), with tables generated from Unicode 18.0.0,
so every Python version gives the same answer:

- East Asian Wide and Fullwidth characters take two columns; ambiguous ones take one.
- Marks, format characters, default ignorable code points, Hangul medial and final jamo,
  and control characters take none; the soft hyphen, drawn as a hyphen, takes one.
- A ZWJ sequence or a skin tone modifier sequence on an emoji, a flag, and a single
  regional indicator take two.
- The emoji presentation selector makes a character with variation sequences two columns;
  the text presentation selector makes it one.
- A spacing vowel sign or a conjunct (consonant, linker, consonant) makes its syllable two.
- Escape sequences take none: CSI (`ESC [` or 8-bit) sequences, OSC, DCS, SOS, PM and APC
  strings up to ST (BEL also ends an OSC), and any other `ESC` sequence. An unfinished
  sequence runs to the end of the text.

Cutting and padding:

- Clusters are never split. Next to a wide character the result can be a column short;
  `fit` fills that column.
- The removed text is replaced by the ellipsis followed by the escape sequences it held, so
  colours and links still close. An ellipsis wider than the width is itself cut.
- A middle cut gives the odd column to the start; when a wide character keeps the start
  from using its half, the end may use the column.
- Centring puts the odd column on the right.
- `truncate`, `pad`, `fit`, `columnize` items and each line of `wrap` reject control
  characters outside escape sequences (`ValueError`). Expand tabs first with
  `str.expandtabs()`.

Wrapping keeps paragraphs (line breaks in the text), keeps the leading spaces of a
paragraph as its indent, drops spaces at a break, and gives a cluster wider than the line a
line of its own. With `max_lines`, the last kept line ends with the ellipsis and the escape
sequences of the dropped lines.

Wrong types raise `TypeError` (`bool` is not a width); negative widths, a zero width for
`wrap` and `columnize`, unknown `side`, `align` or `order` values, and a `fill` that is not
one character one column wide raise `ValueError`.

## Command line

`colfit` lays items out in columns, from arguments or one per line from standard input
(empty lines are skipped). Input and output are UTF-8. The width defaults to the
terminal's.

```
$ colfit -w 30 apple fig cherry date elderberry kiwi lime
apple       fig   cherry  date
elderberry  kiwi  lime
$ colfit -w 30 --down apple fig cherry date elderberry kiwi lime
apple   date        lime
fig     elderberry
cherry  kiwi
```

`-g N` sets the gap between columns; `python -m colfit` works too. Bad options or input
exit with status 2.

## Why

`len()` is wrong for terminal output as soon as a string holds CJK text, accents, emoji or
colour codes, and code that counts code points cuts emoji in half. `wcwidth` is the
reference for terminal widths and now offers its own `width`, `ljust`, `clip` and `wrap`.
`colfit` is for code that wants the layout side with no dependency: exact-width cells with
an ellipsis at the end, start or middle, tie rules written down, escape sequences kept
when text is cut, and `ls`-style columns, all typed and on fixed Unicode 18.0.0 data. Its
widths agree with `wcwidth` 0.9.2 on every single code point, on Indic syllables, Hangul
and styled text; for ZWJ and skin tone sequences on a base without the emoji presentation
selector, `colfit` follows UTS #51 and counts two columns where `wcwidth` counts one.

Not covered: line breaking by UAX #14 (text without spaces breaks between any two
characters), ambiguous characters as two columns, tab stops, and cursor movement
sequences (they count zero like every escape sequence).

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
