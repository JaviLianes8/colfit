# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-23

The first stable release. The public API is the ten names of 0.2.0 with the same
signatures, parameter names and defaults: `display_width`, `graphemes`, `truncate`, `pad`,
`fit`, `wrap`, `columnize` and the `Align`, `Side` and `Order` types, plus the `colfit`
command. From here on they change only in a new major version.

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
- Error messages quote at most 40 characters of an argument, and an integer too large to
  print no longer breaks the message.
- `columnize` skips column counts whose first row is already too wide and, in column
  order, layouts it has already tried, so wide widths take far less time. The layouts are
  the same.
- The package no longer exposes a stray `annotations` name next to its public names.
- `wrap` breaks a very long word in time proportional to its length; it used to take
  time proportional to the square of the length.

### Added

- Every public name has a docstring with examples that run as tests.
- A [GUIDE](https://github.com/JaviLianes8/colfit/blob/main/GUIDE.md) with every rule and
  how the results compare with `wcwidth`, `textwrap` and GNU `ls`.

## [0.2.0]

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

## [0.1.0]

- First release: `columnize` lays strings out in the most columns that fit a
  width, with row-major or column-major order and a configurable gap.
- `display_width` measures terminal cells, counting wide East Asian characters
  as two and combining or zero-width characters as zero.
