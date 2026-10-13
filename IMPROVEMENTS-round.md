# colfit improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Ground truth pinned: Unicode 18.0.0 data, UAX #29, UAX #11 and ECMA-48 in a local folder with a tracked manifest
- [x] Grapheme clusters (UAX #29 extended) from generated tables, never split
- [x] Display width per cluster: East Asian Width, marks, emoji sequences, flags, conjuncts
- [x] Escape sequences (ECMA-48 and the xterm OSC ending) take no columns and are never dropped
- [x] `truncate`, `pad`, `fit` and `wrap` with an ellipsis and documented tie rules
- [x] `columnize` on the new width, strict validation
- [x] Command line tool
- [x] Contracts: break test, emoji test, wcwidth oracle, properties, README examples, wheel e2e
- [x] Mutation run (each guard changed one at a time must fail the suite)
- [x] Docs and packaging: README, CHANGELOG, metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Independent review findings fixed with regression tests
- [x] Pull request opened, guard clean

## Starting point

`0.1.0` (not on PyPI) ships `columnize(items, width, *, gap, order)` and `display_width(text)`.
Read as a user who prints tables, menus and status lines to a terminal:

- Width is a sum over code points with the running Python's `unicodedata`. The same string
  measures differently on Python 3.10 (Unicode 13) and 3.14 (Unicode 16).
- Emoji sequences are wrong: a family emoji (four people joined by ZWJ) measures 8, a flag 2
  only by luck (each regional indicator counts 1), a heart with the emoji presentation
  selector 1 instead of 2, a skin tone modifier adds 2.
- Unassigned default ignorable code points, Hangul medial and final jamo and spacing marks
  are miscounted; Indic conjuncts and vowel signs measure as code points, not as cells.
- Escape sequences count: `"\x1b[31mred\x1b[0m"` measures 7 instead of 3, so coloured items
  break the column layout.
- Only `columnize` exists. There is no way to cut a string to a width with an ellipsis, pad
  or centre it to an exact width, or wrap it, without splitting an emoji or an accent.
- `width < 1` is silently treated as 1; non-string items fail deep inside with a confusing
  error; items with a newline or tab silently break the grid.
- No command line tool, README examples are not executed, no installed-wheel test, no
  ground truth in the tests.

## Sources (fetched 2026-10-13)

- Unicode 18.0.0 UCD: `EastAsianWidth.txt`, `DerivedGeneralCategory.txt`,
  `GraphemeBreakProperty.txt`, `GraphemeBreakTest.txt`, `DerivedCoreProperties.txt`
  (Indic_Conjunct_Break, Default_Ignorable_Code_Point), `PropList.txt`
  (Prepended_Concatenation_Mark), `emoji-data.txt` (Extended_Pictographic),
  `emoji-variation-sequences.txt`, and `emoji-test.txt`.
- UAX #29 revision 49 (Unicode 18.0.0), section 3.1.1: rules GB1 to GB999 for extended
  grapheme clusters, including GB9c (`\p{InCB=Linker} \p{InCB=Extend}* x \p{InCB=Consonant}`; this revision
  no longer names the consonant before the linker) and GB11 to GB13.
- UAX #11 revision 46: the W and F classes are wide, A is ambiguous (narrow outside East
  Asian legacy contexts), and unlisted code points take the `@missing` default ranges.
- ECMA-48 5th edition (1991), sections 5.3 to 5.6: a control sequence is CSI, parameter bytes
  0x30 to 0x3F, intermediate bytes 0x20 to 0x2F, one final byte 0x40 to 0x7E; a C1 function
  is ESC plus 0x40 to 0x5F in 7-bit form or 0x80 to 0x9F in 8-bit form; independent
  functions are ESC plus 0x60 to 0x7E; APC, DCS, OSC, PM and SOS open a control string that
  ends with ST. Ending an OSC with BEL is the xterm convention, not ECMA-48, and is accepted
  because terminals and hyperlink emitters use it.
- `wcwidth` 0.9.2 (`width(text, control_codes="ignore")`) is the reference for what real
  terminals draw; it is a test oracle only, never a runtime dependency.
- The texts are third-party and not committed: `scripts/fetch_sources.py` fetches them into a
  gitignored folder checked against a tracked MANIFEST; the tests that read them skip when the
  folder is absent. `scripts/gen_tables.py` derives the code point runs in `_tables.py` from
  them, and a test regenerates the module and compares.

## Ranked improvements

1. **Pinned Unicode tables.** Grapheme break classes, Extended_Pictographic, InCB, and width
   classes generated from Unicode 18.0.0 into a compact module, so every Python version
   measures the same string the same way.
2. **Grapheme clusters.** `graphemes(text)` implements the extended rules of UAX #29 and
   passes every line of `GraphemeBreakTest.txt`. Every cut, pad and wrap works on clusters.
3. **Width per cluster.** W and F are two columns; marks, format and default ignorable
   characters none (the soft hyphen one); a ZWJ emoji sequence, a flag and a modifier sequence two; the emoji
   presentation selector makes a base with variations two and the text selector one; a
   spacing mark or a conjunct makes its cluster two. Agreement with wcwidth on every code
   point and on every `emoji-test.txt` sequence except ZWJ and modifier sequences on a
   text-default base (two columns here, after UTS #51; one in wcwidth) is a test.
4. **Escape sequences.** CSI, the C1 forms, control strings with ST or BEL, and other escape
   sequences take no columns. When text is cut, the escape sequences of the removed part are
   kept after the ellipsis, so colours and links still close.
5. **Fit functions.** `truncate(text, width, *, ellipsis, side)` with `side` end, start or
   middle (the start keeps the larger half); `pad(text, width, *, align, fill)` (centre puts
   the odd column on the right); `fit` returns exactly `width` columns; `wrap(text, width, *,
   max_lines, ellipsis)` breaks at spaces, then at cluster boundaries, keeps paragraphs.
6. **Typed, strict API.** `Align`, `Side` and `Order` literal aliases; `TypeError` for
   non-strings and non-integer widths (bool included); `ValueError` for negative widths, a
   fill that is not one column, and control characters outside escape sequences in
   single-line text.
7. **Command line tool.** `colfit [-w COLS] [-g GAP] [--down] [ITEM...]`, lines from stdin
   without items, terminal width by default, exit 2 on bad input, quiet on a closed pipe.
8. **Contracts that bite.** Break test, emoji test, wcwidth oracle over code points and
   generated words, properties over fuzzed strings (never wider than the budget, never a split
   cluster, escapes kept in order), executed README, installed-wheel e2e, mutation run.
9. **Docs and packaging.** README with the rules, CHANGELOG 0.2.0, keywords, classifiers,
   console script.

Left out on purpose: line breaking by UAX #14 (CJK text without spaces breaks at any cluster),
ambiguous width as two columns (a terminal setting, not data), tab expansion (rejected with
a pointer to `str.expandtabs`), cursor movement sequences (counted as zero like every escape),
re-applying styles on each wrapped line.

## Verification

- Gates on a second machine (Python 3.14, fresh clone, sources fetched, `COLFIT_E2E=1`):
  `ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
  and `pytest` each exit 0; 290 passed, nothing skipped. The wheel test builds the wheel and
  the sdist, checks that no fetched source ships, installs the wheel in a fresh venv and
  drives the API, the `colfit` script and `python -m colfit` from an empty folder.
- Ground truth: all 853 lines of `GraphemeBreakTest.txt`, every fully qualified emoji and
  component of `emoji-test.txt`, every visible W, F and narrow code point of
  `EastAsianWidth.txt`, the UAX #29 rule texts, and a byte-for-byte regeneration of
  `_tables.py` from the sources.
- Oracle: wcwidth 0.9.2 agrees on every code point, on generated syllables of six scripts
  with conjuncts, Hangul, styled and linked text, and on every emoji sequence except ZWJ and
  modifier sequences on a text-default base (two columns here, one there).
- Mutations: 95 mutants, one at a time, bytecode cache disabled and purged, 240 s timeout,
  baseline green before and after; all killed. A first run left 10 survivors: Hangul syllable
  type ranges, an unfinished control string, the order of dropped escapes after the
  ellipsis, conjunct chains and an emoji after a prepend base got tests; a redundant text
  selector clamp, a redundant spacing mark class check (dropped, which also matches wcwidth
  for spacing letters) and a redundant escape branch were simplified.
- Independent review: 8 findings. Fixed with regression tests: stdin and stdout of the
  command line now UTF-8 (a pipe on Windows used the legacy code page), escape-only and
  zero-width words no longer make lines of their own or count against `max_lines`, line
  breaks inside escape sequences no longer split paragraphs, a stronger closed-pipe test; the
  soft hyphen exception, the GB9c wording, the wcwidth emoji difference and the tab hint were
  corrected in the docs.
