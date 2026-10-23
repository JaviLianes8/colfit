# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-23

The first release on PyPI (0.1.0 and 0.2.0 were never uploaded there). The public API is
the ten names of 0.2.0 with the same signatures, parameter names and defaults:
`display_width`, `graphemes`, `truncate`, `pad`, `fit`, `wrap`, `columnize` and the
`Align`, `Side` and `Order` types, plus the `colfit` command and its exit codes. From here
on they change only in a new major version.

### Changed

- `wrap` keeps the leading spaces of a paragraph only when the first word fits after
  them. When the word fits a line but not after the indent, the indent is dropped, as
  `textwrap` does, instead of the word being split.
- `side`, `align` and `order` values that are not `str` raise `TypeError`, like every
  other argument of the wrong type, instead of `ValueError`.
- `truncate`, `pad`, `fit`, `wrap` and `columnize` refuse text (and an ellipsis or item)
  that ends inside an unfinished escape sequence, such as a lone `ESC` or a hyperlink
  without its terminator, with `ValueError`: the padding, ellipsis or next cell written
  after it would have become part of the sequence and never been drawn. `display_width`
  and `graphemes` still take any text.
- An OSC, DCS, SOS, PM or APC string also ends before an `ESC` that does not start its
  terminator, and before `CAN` or `SUB`, as terminals end it. The text after such an
  interrupted string is measured again instead of counting as part of the string.
- An escape sequence never splits a grapheme cluster: a flag, an emoji ZWJ sequence or an
  accented letter with a colour code inside measures as without it, and a cluster holding
  many escape sequences is cut, padded and wrapped in linear time.
- A spacing mark that UAX #29 puts in a cluster of its own (31 code points in Myanmar,
  Tai Tham and Ahom) widens the syllable before it to two columns, as a spacing vowel
  sign inside a cluster does. `"\u1005\u102c"` measures 2, not 1.
- A ZWJ joins an emoji into a two-column sequence only when another pictograph follows
  it: `"\u00a9\u200d\u0301"` measures 1, not 2.
- Characters that Unicode prepends to a cluster (such as U+0D4E) add their own width
  before it instead of taking the place of its base. A spacing mark after a visible
  prepended character, in a cluster with no other base (right after it or after other
  marks or a ZWJ, in any order), still widens it to two columns, as in 0.2.0:
  `"\u0600\u200d\u093e"` measures 2, as `"a\u200d\u093e"` does.
- `truncate`, `fit` and `wrap` with `max_lines` measure the result with its ellipsis in
  place, so an ellipsis that joins the kept text (one starting with a combining mark,
  a ZWJ or a variation selector) can no longer push it past the width; the result may
  then leave more columns free than the cluster that did not fit. `pad` and `fit` put the
  fill where it reaches the width when the text starts or ends with such a character.
- `pad` and `fit` refuse a `fill` that joins the text before it (a combining or spacing
  mark) and a `width` above `sys.maxsize` with `ValueError`; such a width used to raise
  `OverflowError` or `MemoryError`.
- `columnize` and the `colfit` command refuse an item that starts with a mark joining
  the text before it, with `ValueError` (exit status 2): the mark would have joined the
  space or cell before it and changed that line's width.
- `columnize` builds the gap only between columns, so a gap wider than the width gives
  one column instead of a huge allocation. A `gap` above `sys.maxsize` raises
  `ValueError` instead of `OverflowError`, and the `colfit` command reports it, or a gap
  too large for memory, with exit status 2 instead of a traceback.
- Error messages quote at most 40 characters of an argument, and an integer too large to
  print no longer breaks the message. The `colfit` command does the same for a bad
  `-w` or `-g` value.
- The `colfit` command splits standard input only at line ends (`\n`, `\r\n`, `\r`) and
  refuses other control characters, such as a form feed, with exit status 2, as it does
  for items given as arguments. A byte order mark at the start of the input is dropped.
- `columnize` counts an item that takes no column (empty, or escape sequences only) as
  such when it works out how many columns could fit, so more columns can fit with such
  items; it used to assume every item takes at least one column.
- `columnize` skips column counts that its widest items or one of its rows already make
  too wide, takes at once a count where every column could be as wide as the widest
  item, and in column order skips layouts it has already tried. Its time is linear in
  the number of items: a search that needs more than 32 passes over them beyond a fixed
  allowance of about four million item visits (thousands of items across thousands of
  columns) stops there and takes the most columns that fit when each is as wide as the
  widest item. It no longer pads the last cell of a line, so a single column of long
  items takes time in proportion to their length. Other layouts are the same.
- `wrap` takes time in proportion to the length of a paragraph made of many escape
  sequences, or of many escape sequences between spaces; both used to take time in
  proportion to the square of it. It breaks a very long word in linear time too.
- `truncate` cuts printable ASCII text by slicing, and `display_width` sums widths as it
  goes, so a long line no longer needs memory for one entry per character.
- The package no longer exposes a stray `annotations` name next to its public names.

### Added

- Every function has a docstring with examples that run as tests; the `Align`, `Side`
  and `Order` types are described, with an example, in the package docstring.
- A [GUIDE](https://github.com/JaviLianes8/colfit/blob/main/GUIDE.md) with every rule and
  how the results compare with `wcwidth`, `textwrap` and GNU `ls`.
- The Unicode License v3 notice for the tables derived from the Unicode data, shipped as
  `LICENSES/Unicode-3.0.txt`; the package licence is `MIT AND Unicode-3.0`.

## [0.2.0] - 2026-10-13

Committed as c2f5f19 and never uploaded to PyPI.

### Added

- `truncate` cuts text to a width with an ellipsis at the end, the start or the middle.
- `pad` pads text to a width, aligned left, right or centred, with any one-column fill.
- `fit` returns text in exactly a given width: cut, then padded.
- `wrap` wraps text at spaces, breaks long words between characters, keeps paragraphs and
  indents, and caps the number of lines with an ellipsis.
- `graphemes` splits text into extended grapheme clusters (UAX #29).
- `Align`, `Side` and `Order` literal types.
- A `colfit` command (and `python -m colfit`) that lays items out in columns.

### Changed

- Widths are measured per grapheme cluster with tables generated from Unicode 18.0.0, the
  same on every Python version. Emoji ZWJ and modifier sequences, flags, presentation
  selectors, spacing vowel signs, conjuncts and Hangul jamo now measure as terminals draw
  them.
- Escape sequences (colours, hyperlinks, any ECMA-48 sequence) take no columns, so styled
  items line up in `columnize`.
- `columnize` rejects a width below 1, a negative gap, a single string, non-string items
  and items with control characters, instead of guessing.
- Lines from `columnize` drop trailing spaces only, never other trailing whitespace.

## [0.1.0] - 2026-10-11

Committed as debdd9f and never uploaded to PyPI.

- `columnize` lays strings out in the most columns that fit a
  width, with row-major or column-major order and a configurable gap.
- `display_width` measures terminal cells, counting wide East Asian characters
  as two and combining or zero-width characters as zero.

[Unreleased]: https://github.com/JaviLianes8/colfit/commits/main
[1.0.0]: https://github.com/JaviLianes8/colfit/compare/c2f5f19...main
[0.2.0]: https://github.com/JaviLianes8/colfit/compare/debdd9f...c2f5f19
[0.1.0]: https://github.com/JaviLianes8/colfit/commit/debdd9f
