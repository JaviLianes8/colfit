# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
