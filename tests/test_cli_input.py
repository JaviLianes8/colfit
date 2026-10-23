"""What the command line reads and how it refuses: items, stdin bytes, huge numbers."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from colfit._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _tool(*argv: str, stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    return subprocess.run(
        [sys.executable, "-m", "colfit", *argv], input=stdin, capture_output=True, env=env
    )


def _stdin(monkeypatch: pytest.MonkeyPatch, data: bytes, newline: str | None = "\n") -> None:
    # POSIX opens stdin with newline="\n", so a CR reaches the tool; Windows translates it.
    stream = io.TextIOWrapper(io.BytesIO(data), encoding="cp1252", newline=newline)
    monkeypatch.setattr(sys, "stdin", stream)


@pytest.mark.parametrize("control", ["\f", "\v", "\x1c", "\x1e", "\x85", "\u2028", "\u2029"])
def test_stdin_items_are_split_only_at_line_ends_and_other_controls_refused(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, control: str
) -> None:
    _stdin(monkeypatch, f"a{control}b\nc\n".encode())
    with pytest.raises(SystemExit) as stop:
        main(["-w", "40"])
    assert stop.value.code == 2
    assert "control characters" in capsys.readouterr().err


@pytest.mark.parametrize("newline", ["\n", None], ids=["posix", "windows"])
def test_stdin_line_ends_of_every_platform_still_separate_items(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, newline: str | None
) -> None:
    _stdin(monkeypatch, b"a\r\nb\rc\n\nd", newline)
    assert main(["-w", "40"]) == 0
    assert capsys.readouterr().out == "a  b  c  d\n"


def test_a_byte_order_mark_at_the_start_of_stdin_is_dropped(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _stdin(monkeypatch, b"\xef\xbb\xbfapple\nfig\n")
    assert main(["-w", "40"]) == 0
    assert capsys.readouterr().out == "apple  fig\n"


def test_a_form_feed_read_from_a_real_pipe_exits_two() -> None:
    result = _tool("-w", "40", stdin=b"a\x0cb\n")
    assert result.returncode == 2
    assert b"control characters" in result.stderr


@pytest.mark.parametrize("gap", ["9223372036854775807", "4000000000"])
def test_a_huge_gap_gives_one_column_without_a_traceback(gap: str) -> None:
    result = _tool("-g", gap, "-w", "5", "a", "b")
    assert (result.returncode, result.stdout.split(), result.stderr) == (0, [b"a", b"b"], b"")


@pytest.mark.parametrize("gap", ["9223372036854775808", "1" + "0" * 30])
def test_a_gap_past_sys_maxsize_exits_two_with_a_short_message(gap: str) -> None:
    result = _tool("-g", gap, "-w", "5", "a", "b")
    assert (result.returncode, result.stdout) == (2, b"")
    assert b"gap must be at most sys.maxsize" in result.stderr
    assert b"Traceback" not in result.stderr


@pytest.mark.parametrize(
    "value", ["SECRET" * 3000, "9" * 5000, "-" + "9" * 4000], ids=["text", "digits", "negative"]
)
def test_a_bad_number_is_quoted_short_in_the_error(
    capsys: pytest.CaptureFixture[str], value: str
) -> None:
    with pytest.raises(SystemExit) as stop:
        main(["-w", value, "a"])
    assert stop.value.code == 2
    assert len(capsys.readouterr().err) < 400
