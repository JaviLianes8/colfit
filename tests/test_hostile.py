"""Hostile input: seeded random junk and huge input, no crash, no surprise error, no blowup."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from functools import partial

import pytest

from colfit import Side, columnize, display_width, fit, graphemes, pad, truncate, wrap
from colfit._width import units

NASTY = [
    *"ab ",
    "\x00",
    "\x07",
    "\t",
    "\n",
    "\r",
    "\x1b",
    "\x1b[",
    "\x1b]",
    "\x1bP",
    "\x1b[38;5;",
    "m",
    "\x9b",
    "\x9c",
    "\x9d",
    "\x85",
    "\u2028",
    "\u0301",
    "\u200d",
    "\u200b",
    "\ufe0f",
    "\ufe0e",
    "\u094d",
    "\u0915",
    "\u1100",
    "\u1161",
    "\u11a8",
    "\ud55c",
    "\ud800",
    "\udfff",
    "\U0001f1ea",
    "\U0001f3fb",
    "\U0001f468",
    "\u65e5",
    "\ue000",
    "\U000e0001",
    "\U0010ffff",
    "\u0378",
]


def _junk(rng: random.Random) -> str:
    return "".join(rng.choices(NASTY, k=rng.randint(0, 16)))


def _width_or_one_cluster(line: str, width: int) -> bool:
    return display_width(line) <= width or len([u for u in units(line) if u[1]]) == 1


def _attempt(call: Callable[[], object]) -> object:
    """The result, or None when the call raised the promised ValueError."""
    try:
        return call()
    except ValueError as error:
        assert len(str(error)) < 200
        return None


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_junk_gives_a_result_or_a_value_error(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        text, width = _junk(rng), rng.randint(0, 12)
        assert "".join(graphemes(text)) == text
        assert display_width(text) >= 0
        side: Side = rng.choice(["end", "start", "middle"])
        cut = _attempt(partial(truncate, text, width, side=side))
        assert cut is None or display_width(str(cut)) <= width, (text, width)
        padded = _attempt(partial(pad, text, width))
        assert padded is None or display_width(str(padded)) >= width
        fitted = _attempt(partial(fit, text, width, align="center"))
        assert fitted is None or display_width(str(fitted)) == width, (text, width)
        lines = _attempt(partial(wrap, text, width + 1, max_lines=rng.choice([None, 1, 2])))
        assert lines is None or all(_width_or_one_cluster(x, width + 1) for x in lines)  # type: ignore[attr-defined]
        laid = _attempt(partial(columnize, text.split("a"), width + 1))
        assert laid is None or isinstance(laid, str)


def _seconds(call: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        call()
        best = min(best, time.perf_counter() - start)
    return best


SHAPES: dict[str, Callable[[int], str]] = {
    "plain": lambda n: "a" * n,
    "words": lambda n: "ab " * (n // 3),
    "wide": lambda n: "\u65e5" * n,
    "marks on one base": lambda n: "e" + "\u0301" * n,
    "zwj chain": lambda n: "\U0001f468\u200d" * (n // 2),
    "regional indicators": lambda n: "\U0001f1ea" * n,
    "unfinished string": lambda n: "\x1b]" + "a" * n,
    "long string": lambda n: "\x1b]" + "a" * n + "\x07",
    "escapes": lambda n: "\x1b[1m" * (n // 4),
    "mixed": lambda n: "a\u0301\x1b[1m\u65e5 " * (n // 7),
}

OPERATIONS: dict[str, Callable[[str], object]] = {
    "display_width": display_width,
    "graphemes": graphemes,
    "truncate": lambda text: truncate(text, 50, side="middle"),
    "fit": lambda text: fit(text, 30, side="start"),
    "wrap": lambda text: wrap(text, 1),
    "wrap max_lines": lambda text: wrap(text, 40, max_lines=3),
}


@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("operation", sorted(OPERATIONS))
def test_time_grows_linearly_with_the_input(shape: str, operation: str) -> None:
    small, large = SHAPES[shape](5_000), SHAPES[shape](40_000)
    run = OPERATIONS[operation]
    # Eight times the input: linear work takes about eight times longer, quadratic 64.
    # A text that ends inside an escape sequence is refused, and the refusal is timed.
    slow = _seconds(partial(_attempt, partial(run, large)))
    assert slow < 24 * _seconds(partial(_attempt, partial(run, small))) + 0.05


@pytest.mark.parametrize("order", ["rows", "columns"])
@pytest.mark.parametrize("width", [80, 400])
def test_columnize_time_grows_linearly_with_the_items(order: str, width: int) -> None:
    rng = random.Random(width)
    items = ["x" * rng.choice([1, 2, 5, 9, 30]) for _ in range(80_000)]
    small, large = items[:10_000], items

    def run(chosen: list[str]) -> object:
        return columnize(chosen, width, order=order)  # type: ignore[arg-type]

    assert _seconds(lambda: run(large)) < 24 * _seconds(lambda: run(small)) + 0.05
