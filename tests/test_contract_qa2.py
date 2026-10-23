"""Contracts from the second QA round: each one failed on the code before its fix."""

from __future__ import annotations

import random
import time
from collections.abc import Callable

import pytest
from test_cli_input import _tool

from colfit import Align, Order, _columns, columnize, display_width, fit, pad, truncate
from colfit._width import units


def _seconds(call: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        call()
        best = min(best, time.perf_counter() - start)
    return best


def test_an_empty_ellipsis_in_the_middle_lets_the_kept_ends_join() -> None:
    # Documented: the start and end kept meet, and Unicode may join them into one cluster.
    flag = truncate("\U0001f1ea\u65e5\u65e5\u65e5\U0001f1f8", 5, ellipsis="", side="middle")
    assert (flag, display_width(flag)) == ("\U0001f1ea\U0001f1f8", 2)
    zwj = truncate("\U0001f600\u200d\u65e5\u65e5\u65e5\U0001f600", 5, ellipsis="", side="middle")
    assert (zwj, display_width(zwj)) == ("\U0001f600\u200d\U0001f600", 2)


def test_a_joining_ellipsis_can_leave_the_result_shorter_than_the_cut_cluster() -> None:
    # The selector widens the "#" before it, so "#" goes too and one column stays free.
    cut = truncate("ab#cdef", 5, ellipsis="\ufe0f..")
    assert (cut, display_width(cut)) == ("ab\ufe0f..", 4)


@pytest.mark.parametrize(
    "text",
    ["\U00011f02\U00011f03", "\u0600\u093e", "\u0d4e\u0d3e", "\U000111c2\U000111b3"],
    ids=["kawi", "arabic-number-sign", "malayalam-dot-reph", "sharada"],
)
def test_a_spacing_mark_after_a_prepended_character_widens_it(text: str) -> None:
    # As after any other visible character: one column for the base, one for the mark.
    assert display_width(text) == 2
    assert display_width(text[0] + text) == 3
    assert display_width(text + text[-1]) == 2


def test_units_keep_a_cluster_full_of_escape_sequences_in_linear_time() -> None:
    # Escapes inside one cluster cost what as many escapes between clusters cost; adding
    # each piece to the cluster's string made the first case quadratic on Windows.
    count = 800_000
    inside, between = "a" + "\u0301\x1b[1m" * count, "a" + "b\x1b[1m" * count
    slow, fast = _seconds(lambda: units(inside)), _seconds(lambda: units(between))
    assert slow < 1.3 * fast + 0.05, (slow, fast)
    assert units("a\u0301\x1b[1m\u0301") == [("a\u0301\x1b[1m\u0301", 1, False)]


def test_columnize_stays_linear_when_the_width_grows_with_the_items() -> None:
    def make(n: int) -> Callable[[], object]:
        rng = random.Random(1)
        items = [rng.choice(["a", "bb"]) for _ in range(n)]
        return lambda: columnize(items, n, gap=0)

    fast, slow = _seconds(make(4_000)), _seconds(make(32_000))
    assert slow < 24 * fast + 0.05, (fast, slow)


@pytest.mark.parametrize(("order", "width"), [("rows", 64_000), ("columns", 357)])
def test_the_column_search_visits_each_item_a_bounded_number_of_times(
    monkeypatch: pytest.MonkeyPatch, order: Order, width: int
) -> None:
    rng = random.Random(1)
    items = [rng.choice(["a", "bb"]) for _ in range(64_000)]
    visits = 0
    real = _columns._column_widths

    def counted(widths: list[int], ncols: int, order: str) -> list[int]:
        nonlocal visits
        visits += len(widths)
        return real(widths, ncols, order)

    monkeypatch.setattr(_columns, "_column_widths", counted)
    columnize(items, width, gap=0, order=order)
    # 32 passes and the fixed allowance for the search, one more pass to lay it out.
    assert visits <= 33 * len(items) + 2**22


def test_a_search_cut_short_takes_the_most_columns_as_wide_as_the_widest_item() -> None:
    rng = random.Random(1)
    items = [rng.choice(["a", "bb"]) for _ in range(64_000)]
    lines = columnize(items, 64_000, gap=0).split("\n")
    # 64,000 // 2 columns, so the first line holds the first 32,000 items.
    assert [line.replace(" ", "") for line in lines] == [
        "".join(items[:32_000]),
        "".join(items[32_000:]),
    ]
    assert all(display_width(line) <= 64_000 for line in lines)


def test_zero_width_items_let_more_columns_fit() -> None:
    assert columnize(["a", "", "b", ""], 4, gap=1) == "a  b\n"
    assert columnize(["", "", "", ""], 4, gap=1) == ""
    assert columnize(["", "\x1b[1m\x1b[0m"], 1, gap=1) == " \x1b[1m\x1b[0m"
    assert columnize(["", ""], 1, gap=2) == "\n"


@pytest.mark.parametrize(
    "call",
    [
        lambda: columnize(["a", "b"], 2**64, gap=2**63),
        lambda: columnize(["a", "b"], 10**31, gap=10**30),
        lambda: columnize(["a"], 80, gap=2**63),
    ],
)
def test_a_gap_past_sys_maxsize_is_a_value_error(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=r"gap must be at most sys.maxsize"):
        call()


@pytest.mark.parametrize(
    "argv",
    [
        ["-w", "99999999999999999999", "-g", "9999999999999999999"],
        ["-w", "2000000000000", "-g", "1000000000000"],
    ],
    ids=["past-maxsize", "past-memory"],
)
def test_a_gap_too_large_to_build_exits_two_without_a_traceback(argv: list[str]) -> None:
    result = _tool(*argv, "a", "b")
    assert result.returncode == 2
    assert b"Traceback" not in result.stderr
    assert len(result.stderr) < 400


def test_truncate_keeps_every_escape_when_no_visible_cluster_can_stay() -> None:
    # The lone spacing mark takes no column after the wide character, but widens the
    # ellipsis, so it goes too: only the ellipsis and the escape sequences are left.
    assert truncate("\x1b[31m\u65e5\u102c\x1b[0m", 1, side="start") == "\u2026\x1b[31m\x1b[0m"


@pytest.mark.parametrize(
    ("align", "expected"),
    [
        ("center", "\u2764\u2764\U0001f600\u200d\u2764\u2764\u2764"),
        ("left", "\U0001f600\u200d\u2764\u2764\u2764\u2764\u2764"),
        ("right", "\u2764\u2764\u2764\u2764\U0001f600\u200d"),
    ],
)
def test_a_fill_that_joins_the_end_of_the_text_still_goes_where_align_asks(
    align: Align, expected: str
) -> None:
    # An emoji and a ZWJ join the pictograph after them, so the fill on the right
    # loses a column to the join.
    assert pad("\U0001f600\u200d", 6, align=align, fill="\u2764") == expected
    assert fit("\U0001f600\u200d", 6, align=align, fill="\u2764") == expected
    assert display_width(expected) == 6
