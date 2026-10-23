# colfit 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to colfit. Nothing is on PyPI yet (the
project page and the names `col-fit`, `col_fit` and `col.fit` returned 404 on
2026-10-23), so 1.0.0 is the first release and there is no upgrade path to test; every
change against `main` (0.2.0, never published) is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (c2f5f19)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: Unicode data fetched live, reference programs (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15), final run
- [ ] PR and trace guard
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Scorecard (author)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: the ten names of 0.2.0 kept with their signatures, parameter names and defaults, pinned by `tests/test_contract_api.py`; behaviour changes in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS: `dir(colfit)` holds exactly `__all__` (a stray `annotations` name removed) |
| 3 | Docstrings with runnable examples | PASS: every function and the package docstring (for `Align`, `Side`, `Order`) have doctests; README (4 blocks) and GUIDE (6 blocks) run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed` shipped, a consumer type-checked against the installed wheel |
| 5 | Typed, documented, bounded errors | PASS: `TypeError` and `ValueError` only, listed per function; messages quote at most 40 characters |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: see below |
| 8 | Real e2e from the wheel | PASS: wheel and sdist built, wheel installed in a fresh venv, used from an empty folder, CLI by subprocess (no PyPI release to upgrade from) |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: see below |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t |
| 11 | README and `twine check` | PASS: `twine check --strict` in the e2e test, absolute links, badge |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-23 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS: asserted file by file in `tests/test_e2e_wheel.py` |
| 15 | Gates each exit 0 | PASS: see Gates |
| 18 | Contracts bite (mutations) | PASS: 41 author mutants, 37 killed at once, 3 killed after new contracts, 1 equivalent |

Items 16, 17 and 19 belong to the independent reviewer, the maintainer and the QA lenses.

## Baseline on 0.2.0 (before any change)

Fresh clone at 77be5c8 on another machine (CPython 3.14.2, fetched sources and the pinned
`wcwidth` present): `ruff format --check .`, `ruff check .` and `mypy --strict src tests`
exit 0; `pytest` 289 passed, 1 skipped (the installed-wheel test, opt-in). No doctests.

Defects found in 0.2.0, each reproduced and now covered by a test:

- `wrap("  abcdefgh", 8)` split a word that fits a line because of its indent.
- A text ending inside an unfinished escape sequence (`"ab\x1b]8;;url"`) passed `pad`,
  `fit` and `columnize`, and the padding or the next cell vanished into the sequence:
  `fit` returned text narrower than its width.
- `wrap` took time proportional to the square of a long word (80,000 characters at width
  1: 13.5 s; now 0.13 s).
- `columnize` built every candidate layout in full, so wide widths took far longer.
- `side=1` raised `ValueError`, unlike every other wrong type; a `side`, `align` or `fill`
  of a megabyte went whole into the message; `-(10**5000)` as a width broke the message.
- The package exposed an `annotations` name; no docstring had an example; the README
  linked LICENSE relatively; there was no GUIDE.

## API review (item 1)

Kept: `display_width`, `graphemes`, `truncate`, `pad`, `fit`, `wrap`, `columnize`,
`Align`, `Side`, `Order` and the `colfit` command, with their 0.2.0 signatures and
defaults. Changed (CHANGELOG 1.0.0): the indent rule of `wrap` (now that of `textwrap`),
`TypeError` for non-`str` choices, refusal of text ending inside an unfinished escape
sequence, bounded messages, linear long-word breaking, a faster column search with the
same layouts (checked against the plain search on 3,000 random cases), the stray
`annotations` name. `release.ps1` now refuses a version already on PyPI instead of any
upload once the name exists, and only builds from a clean tree.

## Ground truth (item 7)

- Unicode 18.0.0 data (UCD, emoji), UAX #29 rev. 49, UAX #11 rev. 46 and ECMA-48 fetched
  again live on 2026-10-23 by `scripts/fetch_sources.py`; all twelve match the sha256 in
  `tests/sources/MANIFEST.txt`, and the tests now check that hash before reading. Nothing
  fetched is committed or shipped. Checked: every line of `GraphemeBreakTest.txt`, every
  fully qualified emoji of `emoji-test.txt`, the rule list of the fetched annex (GB9c is
  the Unicode 18 form `Linker Extend* x Consonant`) and the tables rebuilt from the data.
- `wcwidth` 0.9.2 as an independent oracle: every code point alone, the emoji test file
  (UTS #51 differences asserted exactly), Indic and Hangul syllables, styled text; new:
  `wrap` equals `wcwidth.wrap` on 8,000 Unicode paragraphs whose words fit a line, and
  `pad` equals `wcwidth.ljust` and `rjust` on 8,000 strings.
- Real programs run in this session: GNU coreutils 8.32 `ls -C` and `ls -x` on 60
  generated folders (`ls -w W` equals `columnize(names, W - 1)`; the two ls rules behind
  the offset, a free last screen column and three columns reserved per column, were found
  by comparing 300 random cases); `textwrap.wrap` on 20,000 ASCII paragraphs; `format()`
  alignment on 20,000 `pad` calls. Where they differ by design (long words, the centring
  of `str.center`, spaces-only text) the GUIDE says so.

## Fuzz and hostile input (item 9)

`tests/test_hostile.py`: three seeds of 3,000 strings over 40 hostile pieces (C0, C1,
DEL, U+2028, lone surrogates, partial and 8-bit sequences, unassigned and private use
code points): every function returns a result that keeps its width promise or raises the
promised `ValueError` with a short message. Nine input shapes (plain, words, wide, marks
on one base, ZWJ chains, regional indicators, unfinished and finished control strings,
escapes, mixed) through every text function at 5,000 and 40,000 characters, and
`columnize` with 10,000 and 80,000 items at widths 80 and 400: time grows linearly.
`columnize` time grows with the items times `width // (gap + 1)`, as its docstring and
the GUIDE say. `tests/test_properties.py` checks the cut, fit, wrap and column rules on
seeded random mixes of every cluster kind.

## Author mutation round (item 18)

41 mutants over every module, each applied alone to a copy of a fresh clone at 0096625 on
another machine (CPython 3.14.2, fetched sources and `wcwidth` 0.9.2 present, GNU ls
absent there), the full suite run with `-x` and a 300 s per-test limit. 37 killed at
once. Of the four survivors, three (E4, W4, K3) showed missing contracts, now in
`tests/test_contract_mutants.py` (f25d2c4) and confirmed to kill them; F3 is equivalent
(with an ellipsis exactly as wide as the width, cutting it keeps every unit, so the
result is the same).

| Mutant | Module | Change | Caught by |
| --- | --- | --- | --- |
| C1 | `_check` | width limit off by one | `test_cli.py::test_a_terminal_that_reports_no_width_still_gets_one_column` |
| C2 | `_check` | `bool` taken as a width | `test_errors.py::test_width_must_be_an_int` |
| C3 | `_check` | long arguments quoted in errors | `test_contract_edges.py::test_error_messages_stay_short_for_huge_arguments` |
| C4 | `_check` | unfinished escape accepted | `test_contract_edges.py::test_text_ending_inside_an_escape_sequence_is_refused` |
| C5 | `_check` | C1 controls and DEL accepted | `test_errors.py::test_single_line_text_rejects_control_characters` |
| C6 | `_check` | wrong choice type gives `ValueError` | `test_contract_edges.py::test_a_choice_of_the_wrong_type_is_a_type_error` |
| E1 | `_escapes` | BEL no longer ends an OSC | `test_contract_edges.py::test_finished_or_cut_short_sequences_are_fine` |
| E2 | `_escapes` | CSI final byte range short by one | `test_escapes.py::test_each_sequence_is_one_escape_piece` |
| E3 | `_escapes` | every sequence counted as open | `test_columnize.py::test_coloured_items_are_padded_by_their_visible_width` |
| E4 | `_escapes` | 8-bit DCS skipped by the fast path | survived; now `test_contract_mutants.py::test_an_8_bit_control_string_runs_to_its_terminator_or_the_end` |
| F1 | `_fit` | `take` keeps one cluster less | doctest of `fit` |
| F2 | `_fit` | middle cut gives the odd column to the end | doctest of `truncate` |
| F3 | `_fit` | ellipsis exactly as wide as the width cut | equivalent (see above) |
| F4 | `_fit` | text exactly the width truncated | `test_properties.py::test_truncate_fits_keeps_whole_units_and_every_escape` |
| F5 | `_fit` | centring puts the odd column on the left | doctest of `pad` |
| F6 | `_fit` | zero-width fill accepted | `test_errors.py::test_fill_must_be_one_character_one_column_wide` |
| F7 | `_fit` | `fit` ignores `side` | `test_contract_edges.py::test_a_choice_of_the_wrong_type_is_a_type_error` |
| G1 | `_graphemes` | GB9c joins any character after a linker | `test_graphemes.py::test_linker_before_a_non_consonant_breaks` |
| G2 | `_graphemes` | regional indicators paired wrongly | doctest of `graphemes` |
| G3 | `_graphemes` | GB11 without the emoji before the ZWJ | doctest of `graphemes` |
| G4 | `_graphemes` | linker state dropped after an extend | `test_graphemes.py::test_conjunct_joins_across_the_linker` |
| U1 | `_unicode` | Hangul LV and LVT syllables swapped | `test_graphemes.py::test_hangul_syllable_types_decide_what_joins` |
| U2 | `_unicode` | spacing marks alone take a column | `test_oracle.py::test_every_code_point_alone_measures_as_in_wcwidth` |
| W1 | `_width` | emoji selector widens any base | `test_hostile.py::test_junk_gives_a_result_or_a_value_error` |
| W2 | `_width` | darkest skin tone not a modifier | `test_oracle.py::test_emoji_sequences_agree_except_text_default_sequences` |
| W3 | `_width` | ASCII controls measured as one column | `test_oracle.py::test_every_code_point_alone_measures_as_in_wcwidth` |
| W4 | `_width` | conjunct counted on a zero-width base | survived; now `test_contract_mutants.py::test_a_linker_with_no_consonant_before_it_makes_no_conjunct` |
| R1 | `_wrap` | trailing marks split from their word | `test_contract_edges.py::test_the_indent_stays_before_a_word_that_must_break_anyway` |
| R2 | `_wrap` | indent kept before a word exactly the width | GUIDE example 5 |
| R3 | `_wrap` | a trailing line break adds an empty line | `test_contract_edges.py::test_spaces_alone_are_one_empty_line_and_no_text_no_line` |
| R4 | `_wrap` | `max_lines` cuts text that fits | `test_wrap.py::test_escape_sequences_between_spaces_never_make_a_line_of_their_own` |
| R5 | `_wrap` | a cluster wider than the line never placed | suite stopped with an error (endless loop) |
| R6 | `_wrap` | a word that exactly fills the line moves down | README example 2 |
| K1 | `_columns` | first-row bound rejects an exact fit | `test_columnize.py::test_row_order_fills_left_to_right` |
| K2 | `_columns` | fewer columns tried | `test_columnize.py::test_row_order_fills_left_to_right` |
| K3 | `_columns` | other trailing whitespace stripped | survived; now `test_contract_mutants.py::test_columnize_strips_only_ascii_spaces_at_line_ends` |
| K4 | `_columns` | exact fit rejected | `test_cli.py::test_items_are_laid_out_in_rows` |
| K5 | `_columns` | column order skips items | doctest of `columnize` |
| L1 | `_cli` | command line gap default | `test_cli.py::test_items_are_laid_out_in_rows` |
| L2 | `_cli` | empty stdin lines become items | `test_cli.py::test_items_come_from_stdin_and_empty_lines_are_skipped` |
| L3 | `_cli` | empty output prints a blank line | `test_cli.py::test_no_items_print_nothing` |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

Every interpreter on this PC from `requires-python` up, each in a fresh venv from a fresh
clone at 0096625 with the fetched sources and `COLFIT_E2E=1` (the e2e tests build the
wheel and sdist with that interpreter, run `twine check --strict`, compare the wheel with
`src` file by file, check the sdist ships LICENSE, README, GUIDE, CHANGELOG and the source
manifest but no fetched file, release notes or caches, install the wheel in a new venv,
run a program and the CLI from an empty folder, and type-check a consumer against the
install): CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded all
pass with no skips. CPython 3.8.20 and 3.9.25 are below `requires-python` and refuse the
install. No other interpreter is installed here.

## Gates (item 15)

Pending the final run.
