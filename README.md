# colfit

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

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

The rules in short: widths per grapheme cluster on fixed Unicode 18.0.0 tables, escape
sequences take no columns and are never lost, clusters are never split, and control
characters (tabs included) are refused with `ValueError` instead of guessed at. The
[GUIDE](https://github.com/JaviLianes8/colfit/blob/main/GUIDE.md) has every rule with
examples, and how the results were checked.

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
colour codes, and `textwrap` counts code points too. Code that cuts by code points also
splits emoji and accented letters in half.

`wcwidth` is the reference for terminal widths. Version 0.9.2 also offers `width`,
`ljust`, `rjust`, `center`, `clip` and `wrap`, with tab stops, cursor movement and a choice
of Unicode versions and terminals. `colfit` is a smaller, layout-first alternative with no
dependency: cells cut to an exact width with an ellipsis at the end, the start or the
middle, written tie rules, escape sequences kept when text is cut, and `ls`-style columns
(the same layout as GNU `ls`), all typed, on fixed Unicode 18.0.0 data.

Its widths agree with `wcwidth` 0.9.2 on every single code point, on Indic syllables,
Hangul and styled text, and its `wrap` gives the lines of `wcwidth.wrap` for words that fit
a line. For ZWJ and skin tone sequences on a base without the emoji presentation selector,
`colfit` follows UTS #51 and counts two columns where `wcwidth` counts one.

Not covered: line breaking by UAX #14 (text without spaces breaks between any two
characters), ambiguous characters as two columns, tab stops, and cursor movement
sequences (they count zero like every escape sequence).

## Documentation

- [GUIDE](https://github.com/JaviLianes8/colfit/blob/main/GUIDE.md): every rule, with
  examples that run as tests.
- [CHANGELOG](https://github.com/JaviLianes8/colfit/blob/main/CHANGELOG.md): what changed
  in each release.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/colfit/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
