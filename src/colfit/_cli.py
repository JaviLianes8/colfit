"""Command line tool: lay out items given as arguments or read one per line from stdin."""

from __future__ import annotations

import argparse
import errno
import io
import os
import shutil
import sys
from collections.abc import Callable, Sequence

from ._columns import Order, columnize


def _number(minimum: int) -> Callable[[str], int]:
    def parse(text: str) -> int:
        try:
            value = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"expected a whole number, not {text!r}") from None
        if value < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}, not {value}")
        return value

    return parse


def _parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="colfit",
        description="Lay items out in the most columns that fit the terminal. Without ITEM "
        "arguments, items are read one per line from standard input; empty lines are skipped.",
        epilog="examples:\n  colfit -w 40 apple fig cherry date elderberry\n  ls | colfit --down",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("items", nargs="*", metavar="ITEM", help="items to lay out")
    parser.add_argument(
        "-w", "--width", type=_number(1), metavar="COLS", help="total width (default: terminal)"
    )
    parser.add_argument(
        "-g", "--gap", type=_number(0), default=2, metavar="N", help="spaces between columns"
    )
    parser.add_argument(
        "-d", "--down", action="store_true", help="fill columns top to bottom, like ls"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _read_stdin() -> list[str]:
    if isinstance(sys.stdin, io.TextIOWrapper):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    return [line for line in sys.stdin.read().splitlines() if line]


def _emit(text: str) -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        # A pipe on Windows defaults to a legacy code page, which cannot hold most text.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        sys.stdout.write(text + "\n" if text else "")
        sys.stdout.flush()
    except OSError as error:
        # The reader went away (``| head``). Windows reports EINVAL rather than EPIPE.
        if not isinstance(error, BrokenPipeError) and error.errno != errno.EINVAL:
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``colfit`` and ``python -m colfit``; returns the exit code."""
    parser = _parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    width = args.width if args.width is not None else shutil.get_terminal_size().columns
    items = args.items or _read_stdin()
    order: Order = "columns" if args.down else "rows"
    try:
        text = columnize(items, max(width, 1), gap=args.gap, order=order)
    except ValueError as error:
        parser.error(str(error))
    _emit(text)
    return 0
