# colfit 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to colfit. Nothing is on PyPI yet (the
project page and the names `col-fit`, `col_fit` and `col.fit` returned 404 on
2026-10-23), so 1.0.0 is the first release and there is no upgrade path to test; every
change against `main` (0.2.0, never published) is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (c2f5f19), baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: Unicode data fetched live, reference programs (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [x] Gates (item 15), final run; PR #3 and trace guard CLEAN
- [x] QA rounds 1 to 5: every finding fixed (e97dc62, b105d51, 9b1342f, 1e15265, 8f2c1ad),
  none disputed
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Scorecard (author; items 16, 17 and 19 belong to the reviewer, maintainer and QA lenses)

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
| 14 | sdist and wheel contents | PASS: asserted file by file in `tests/test_e2e_wheel.py`; the Unicode License v3 notice ships (QA round 1) |
| 15 | Gates each exit 0 | PASS: see Gates |
| 18 | Contracts bite (mutations) | PASS: 41 author mutants, 37 killed at once, 3 killed after new contracts, 1 equivalent |

## Baseline on 0.2.0 (before any change)

Fresh clone at 77be5c8 elsewhere (CPython 3.14.2, sources and `wcwidth` present): ruff,
mypy exit 0; `pytest` 289 passed, 1 skipped (opt-in wheel test); no doctests. Defects
found, each now covered by a test: `wrap("  abcdefgh", 8)` split a word that fits a line
because of its indent; a text ending inside an unfinished escape sequence passed `pad`,
`fit` and `columnize`, and what followed vanished into it; `wrap` was quadratic in a long
word (80,000 characters at width 1: 13.5 s, now 0.13 s); `columnize` built every candidate
layout; `side=1` raised `ValueError`; huge arguments went whole into messages; an
`annotations` name leaked; no docstring had an example; no GUIDE.

## API review (item 1)

Kept: the ten public names and the `colfit` command with their 0.2.0 signatures and
defaults. Every behaviour change is in the CHANGELOG 1.0.0 entry, the faster column search
checked against the plain search on 3,000 random cases. `release.ps1` refuses a version
already on PyPI and builds only from a clean tree.

## Ground truth (item 7)

- Unicode 18.0.0 data, UAX #29 rev. 49, UAX #11 rev. 46 and ECMA-48 fetched live by
  `scripts/fetch_sources.py`, checked against `tests/sources/MANIFEST.txt` before every
  read, never committed or shipped: every line of `GraphemeBreakTest.txt`, every fully
  qualified emoji, the annex rule list (GB9c in its Unicode 18 form), the tables rebuilt.
- `wcwidth` 0.9.2 as an independent oracle: every code point alone, the emoji test file,
  Devanagari, Bengali, Gujarati, Oriya, Telugu and Malayalam syllables, the 31 spacing
  marks UAX #29 leaves alone, Hangul, styled text, `wrap` (8,000 one-line paragraphs whose
  words fit), `ljust` and `rjust` (8,000 strings), and each difference the README lists.
- Real programs: GNU coreutils 8.32 `ls -C` and `ls -x` on 60 generated folders (`ls -w W`
  equals `columnize(names, W - 1)`), `textwrap.wrap` on 20,000 ASCII paragraphs, `format()`
  on 20,000 `pad` calls. Differences by design are in the GUIDE.

## Fuzz and hostile input (item 9)

`tests/test_hostile.py`: 9,000 strings of 40 hostile pieces through every function (a
result that keeps its promise, or the promised short `ValueError`) and ten input shapes at
5,000 and 40,000 characters (linear time). `tests/test_contract_joins.py` fuzzes text,
ellipsis and fill made of joining characters; `tests/test_contract_limits.py` times the
adversarial shapes of QA round 1 and bounds memory; `tests/test_properties.py` checks the
cut, fit, wrap and column rules on seeded mixes of every cluster kind.

## Author mutation round (item 18)

41 mutants over every module, each applied alone to a fresh clone at 0096625 on another
machine (CPython 3.14.2, fetched sources, `wcwidth` 0.9.2, no GNU ls), the full suite run
with `-x` and a 300 s per-test limit: 37 killed at once; three survivors (E4, W4, K3)
showed missing contracts, now in `tests/test_contract_mutants.py` (f25d2c4) and killing
them; F3 is equivalent (an ellipsis exactly as wide as the width keeps every unit when cut).

| Mutant | Change | Caught by | Mutant | Change | Caught by |
| --- | --- | --- | --- | --- | --- |
| C1 | `_check`: width limit off by one | `test_cli.py::test_a_terminal_that_reports_no_width_still_gets_one_column` | C2 | `_check`: `bool` taken as a width | `test_errors.py::test_width_must_be_an_int` |
| C3 | `_check`: long arguments quoted in errors | `test_contract_edges.py::test_error_messages_stay_short_for_huge_arguments` | C4 | `_check`: unfinished escape accepted | `test_contract_edges.py::test_text_ending_inside_an_escape_sequence_is_refused` |
| C5 | `_check`: C1 controls and DEL accepted | `test_errors.py::test_single_line_text_rejects_control_characters` | C6 | `_check`: wrong choice type gives `ValueError` | `test_contract_edges.py::test_a_choice_of_the_wrong_type_is_a_type_error` |
| E1 | `_escapes`: BEL no longer ends an OSC | `test_contract_edges.py::test_finished_or_cut_short_sequences_are_fine` | E2 | `_escapes`: CSI final byte range short by one | `test_escapes.py::test_each_sequence_is_one_escape_piece` |
| E3 | `_escapes`: every sequence counted as open | `test_columnize.py::test_coloured_items_are_padded_by_their_visible_width` | E4 | `_escapes`: 8-bit DCS skipped by the fast path | survived; now `test_contract_mutants.py::test_an_8_bit_control_string_runs_to_its_terminator_or_the_end` |
| F1 | `_fit`: `take` keeps one cluster less | doctest of `fit` | F2 | `_fit`: middle cut gives the odd column to the end | doctest of `truncate` |
| F3 | `_fit`: ellipsis exactly as wide as the width cut | equivalent (see above) | F4 | `_fit`: text exactly the width truncated | `test_properties.py::test_truncate_fits_keeps_whole_units_and_every_escape` |
| F5 | `_fit`: centring puts the odd column on the left | doctest of `pad` | F6 | `_fit`: zero-width fill accepted | `test_errors.py::test_fill_must_be_one_character_one_column_wide` |
| F7 | `_fit`: `fit` ignores `side` | `test_contract_edges.py::test_a_choice_of_the_wrong_type_is_a_type_error` | G1 | `_graphemes`: GB9c joins any character after a linker | `test_graphemes.py::test_linker_before_a_non_consonant_breaks` |
| G2 | `_graphemes`: regional indicators paired wrongly | doctest of `graphemes` | G3 | `_graphemes`: GB11 without the emoji before the ZWJ | doctest of `graphemes` |
| G4 | `_graphemes`: linker state dropped after an extend | `test_graphemes.py::test_conjunct_joins_across_the_linker` | U1 | `_unicode`: Hangul LV and LVT syllables swapped | `test_graphemes.py::test_hangul_syllable_types_decide_what_joins` |
| U2 | `_unicode`: spacing marks alone take a column | `test_oracle.py::test_every_code_point_alone_measures_as_in_wcwidth` | W1 | `_width`: emoji selector widens any base | `test_hostile.py::test_junk_gives_a_result_or_a_value_error` |
| W2 | `_width`: darkest skin tone not a modifier | `test_oracle.py::test_emoji_sequences_agree_except_text_default_sequences` | W3 | `_width`: ASCII controls measured as one column | `test_oracle.py::test_every_code_point_alone_measures_as_in_wcwidth` |
| W4 | `_width`: conjunct counted on a zero-width base | survived; now `test_contract_mutants.py::test_a_linker_with_no_consonant_before_it_makes_no_conjunct` | R1 | `_wrap`: trailing marks split from their word | `test_contract_edges.py::test_the_indent_stays_before_a_word_that_must_break_anyway` |
| R2 | `_wrap`: indent kept before a word exactly the width | GUIDE example 5 | R3 | `_wrap`: a trailing line break adds an empty line | `test_contract_edges.py::test_spaces_alone_are_one_empty_line_and_no_text_no_line` |
| R4 | `_wrap`: `max_lines` cuts text that fits | `test_wrap.py::test_escape_sequences_between_spaces_never_make_a_line_of_their_own` | R5 | `_wrap`: a cluster wider than the line never placed | suite stopped with an error (endless loop) |
| R6 | `_wrap`: a word that exactly fills the line moves down | README example 2 | K1 | `_columns`: first-row bound rejects an exact fit | `test_columnize.py::test_row_order_fills_left_to_right` |
| K2 | `_columns`: fewer columns tried | `test_columnize.py::test_row_order_fills_left_to_right` | K3 | `_columns`: other trailing whitespace stripped | survived; now `test_contract_mutants.py::test_columnize_strips_only_ascii_spaces_at_line_ends` |
| K4 | `_columns`: exact fit rejected | `test_cli.py::test_items_are_laid_out_in_rows` | K5 | `_columns`: column order skips items | doctest of `columnize` |
| L1 | `_cli`: command line gap default | `test_cli.py::test_items_are_laid_out_in_rows` | L2 | `_cli`: empty stdin lines become items | `test_cli.py::test_items_come_from_stdin_and_empty_lines_are_skipped` |
| L3 | `_cli`: empty output prints a blank line | `test_cli.py::test_no_items_print_nothing` | | | |

## QA round 1 (item 19)

Five lenses (a API and docs, b ground truth, c adversarial, d packaging, e mutations) ran
on e57a74b. Every finding is fixed in e97dc62, each behaviour bug with a contract shown to
fail on e57a74b first; the mutants of the three mutation findings (R02, S15, S22) are killed.

| Lens | What changed |
| --- | --- |
| a (A1 to A9) | `cut` measures the result with its ellipsis and keeps less until it fits; `pad` measures the fill joined to the text; a joining `fill` or item is refused (`test_contract_joins.py`, seeded fuzz included) (A1, with c C4); `wrap` docstring states the indent rule (A2); README and GUIDE name `break_on_hyphens=False`, spaces alone and line breaks (A3, A4, with b F5); GUIDE errors table complete for `pad` (A5); CHANGELOG on docstrings and the `Literal` aliases (A6); 0.2.0 and 0.1.0 dated and marked never uploaded (A7); CONTRIBUTING names the tests that run real programs (A8); `truncate` says how short a result can be (A9) |
| b (F1 to F5) | a spacing mark in a cluster of its own widens the syllable before it (F1, 31 code points, `wcwidth` oracle); README "Why" states what was measured and each difference, pinned in `test_oracle.py` (F2); a ZWJ makes one emoji only before a pictograph (F3); control strings end before an ESC that does not start ST, and before CAN or SUB (F4) |
| c (C1 to C9) | `wrap` joins each paragraph once (C1, C2); `columnize` skips counts its 16 widest items or a row make too wide and pads no last cell (C3); clusters are found in the visible text (C5); the gap is built only between columns (C6, with d F1); `pad` and `fit` refuse a width above `sys.maxsize` (C7); the CLI quotes at most 40 characters of a bad number (C8); `truncate` slices ASCII and `display_width` streams (C9); the limit of `columnize` added then (the items times `width // (gap + 1)`) failed item 9, and round 2 removed it |
| d (F1 to F3) | the Unicode License v3 notice ships (`LICENSES/Unicode-3.0.txt`, fetched from unicode.org/license.txt, sha256 e7a93b00...), licence `MIT AND Unicode-3.0` (F2); stdin split only at line ends, other controls exit 2, a leading BOM dropped (F3) |
| e (E-1 to E-3) | contracts: only U+0020 breaks, ellipsis before dropped escapes, the 40/41 boundary |

## QA round 2 (item 19)

The same five lenses re-ran on 1c0a3b7 and confirmed the round 1 fixes but for b F2, c C3
and d F1 (in part, see b R1, c N1 and d F1b). Every finding is fixed in b105d51; each
behaviour bug got a contract first (`tests/test_contract_qa2.py` and the tests named
below): 19 failed on 1c0a3b7, all pass on b105d51, and the four lens e survivors are killed.

| Finding | What changed |
| --- | --- |
| a N1 | Option (b), documented: `truncate` and the GUIDE say that a joining ellipsis can leave more columns free than the cut cluster, and that with an empty ellipsis in the middle the kept ends can join (two lone regional indicators make a flag); contracts pin the three cases of the report |
| b R1 | README: after a two-column syllable ending in a virama, `wcwidth` gives the next character no column (checked in all six scripts); two cases added to the README differences in `test_oracle.py` |
| b N1 | A spacing mark right after a visible prepended character widens it to two, as in 0.2.0 (Kawi, U+0600, U+0D4E and Sharada pinned); all 27 x 477 Prepend and spacing mark pairs give 2, as `wcwidth` does apart from its 162 spacing viramas, a listed difference |
| b N2 | README: the comparison is with `control_codes="ignore"`, under which escapes inside clusters agree (25,454 fuzzed strings, 0 differences); with the default `"parse"` `wcwidth` splits a cluster at an escape, now a listed and pinned difference |
| b N3 | The column bound comes from the narrowest items (each column is as wide as a different item), so empty and escape-only items let more columns fit; the plain-search oracle tries every count and runs on 3,000 cases with such items |
| c N1 | `columnize` takes at once a count where every column could be as wide as the widest item, and caps its search at 32 passes over the items beyond about four million item visits, then takes the most columns that fit at the widest item's width (docstring, GUIDE, CHANGELOG). 64,000 items 1 or 2 wide at width 64,000: 0.57 s, was 20 s; a contract counts the item visits in both orders |
| c N2 | `units` collects the pieces of a cluster in a list and joins them once: 800,000 escapes inside one cluster cost what as many between clusters cost |
| d F1b | `columnize` refuses a `gap` above `sys.maxsize` with `ValueError`; the `colfit` command reports it, and a `MemoryError`, with exit status 2; docstring, GUIDE, README and CHANGELOG updated |
| e E2-1 to E2-4 | Contracts: Thai and Lao AM refused as a first character, stdin read with POSIX line ends too, escapes kept when no visible cluster can stay, a fill joining the end of the text for each `align` |

## QA rounds 3 to 5 (item 19)

Round 3: lenses b, d and e reported on f64a51f: b N2 and N3, d F1b and e's four round 2
mutants confirmed fixed, and the first five rows below, fixed in 9b1342f. The N1 contract
in `tests/test_contract_qa3.py` failed on f64a51f; lens e's five survivors (C09, C13, C16,
C20, W12) and W13 (the new rule cut to spacing marks), each applied alone to 9b1342f, are
killed by that file. W11 is equivalent: no prepended character takes zero columns. Round
4: lenses d and e reported on 537fc3e: d N1 and e's round 3 mutants confirmed fixed, and
the next two rows, fixed in 1e15265 with contracts in `tests/test_contract_qa4.py`. Round
5: lens e reported on 9a652eb: every round 4 finding confirmed fixed, and the last three
rows, closed in 8f2c1ad by `tests/test_contract_qa5.py` with no behaviour change; each of
the six survivors (S05 to S09, S13), applied alone to 9a652eb, fails that file (two to
four tests each).

| Finding | What changed |
| --- | --- |
| b R1 | README: after a syllable ending in a virama, `wcwidth` gives it and the next character at most two columns together (20,000 seeded syllables in the six scripts, no exception); the agreement claim is for syllables measured alone; three more pinned differences in `test_oracle.py` |
| b N1 | Marks with no base after a visible prepended character sit on it, so a spacing mark among them widens it (`cluster_width`). Of 64,800 sequences of a prepended character, a nonspacing mark and a spacing mark, every one that forms one cluster now measures as in 0.2.0, and differs from `wcwidth` only where the same marks after a letter do; comment, GUIDE and CHANGELOG updated |
| b N4 | GUIDE and README: the GNU `ls` match holds as long as the column search does not stop early |
| d N1, e E3-0 | This report is back under 200 lines (two mutants per table row, round 1 grouped by lens); the gates ran at 9b1342f and again on the tree of this record commit (see Gates) |
| e E3-1 to E3-5 | Contracts: 500 mixed items equal the plain search in both orders; the fallback with `gap=1` takes 30,665 columns at width 91,994; skewed widths in column order give the 11 rows of a search with no limit; a gap of 4,000 or 5,000 digits is quoted in at most 100 characters; U+102C U+0E33 measures 1, as in `wcwidth` |
| d Q1, e E4-1 | A ZWJ right after a visible prepended character is one more mark on it (`_is_mark`), so a spacing mark after it widens it whatever the order of the marks: `"\u0600\u200d\u093e"` measures 2, as `"a\u200d\u093e"` does and as in 0.2.0. Its contracts failed on 537fc3e; 40,000 seeded tails of marks and ZWJ after the 27 prepended characters now measure as after `a`; GUIDE and CHANGELOG updated |
| e E4-2 to E4-4 | Contracts, each killing its survivor applied alone to 1e15265: U+102B and U+102C (Mc, not SpacingMark) after U+0600 measure 2 (N02); Thai and Lao AM after U+0600, before a vowel sign or a virama and consonant, measure as after `a` (N04); two to four prepended characters before nonspacing marks or a ZWJ count once each (N13) |
| e E5-1 | Contracts: a regional indicator or a flag after U+0600 or U+0D4E keeps its two columns (3, and 4 after two prepended characters) |
| e E5-2 | Contracts: a Hangul LV or LVT syllable or a leading jamo after U+0600 or U+0D4E, before a vowel sign or a virama and consonant, measures 3: 1 plus its own 2 |
| e E5-3 | Value kept at 1 and pinned: a medial or final jamo is a letter (gc Lo), a base in UAX #29, not Extend, so after a prepended character it is the zero-width base of the rest, as alone (U+1161 U+093E measures 0, U+0600 U+1161 U+093E measures 1); a ZWJ there still gives 2. The code comment and the GUIDE now say any jamo is a base |

## Disputed findings

None, in any round.

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

Every interpreter on this PC from `requires-python` up, each in a fresh venv from a fresh
clone at 0096625 with the fetched sources and `COLFIT_E2E=1` (the e2e tests build the
wheel and sdist with that interpreter, run `twine check --strict`, compare the wheel with
`src` file by file, check the sdist ships LICENSE, README, GUIDE, CHANGELOG and the source
manifest but no fetched file, release notes or caches, install the wheel in a new venv,
run a program and the CLI from an empty folder, and type-check a consumer against the
install): CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded all
pass with no skips. CPython 3.8.20 and 3.9.25 are below `requires-python` and refuse the
install. No other interpreter is installed here. At 537fc3e: 690 passed, 2 skipped on each.

## Gates (item 15)

Each run on another machine from a fresh clone (CPython 3.14.2, fetched sources, `wcwidth`
0.9.2, `COLFIT_E2E=1`), each on its own: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, `mypy --strict src tests` and `pytest` exit 0, one skip there (no `ls`;
`test_reference_programs.py` passes on this PC). `pytest` passed: 501 at 5af1a32, 653 at
5faad35 (QA round 1), 684 at b105d51 (round 2), 698 at 9b1342f (round 3), 711 at 1e15265
(round 4), 731 at 8f2c1ad (round 5). Each record commit changes only this report; the same
five ran on its tree before it was pushed: all exit 0.
