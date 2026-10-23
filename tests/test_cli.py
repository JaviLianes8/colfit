"""The command line tool, driven in process and once as a real subprocess."""

from __future__ import annotations

import errno
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

import colfit
from colfit._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
FRUITS = ["apple", "fig", "cherry", "date", "elderberry", "kiwi", "lime"]


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> list[str]:
    assert main(list(argv)) == 0
    return capsys.readouterr().out.splitlines()


def _fails(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    return capsys.readouterr().err


def test_items_are_laid_out_in_rows(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "-w", "30", *FRUITS)
    assert out == ["apple       fig   cherry  date", "elderberry  kiwi  lime"]


def test_down_fills_columns_first(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "--width", "30", "--down", *FRUITS)
    assert out == ["apple   date        lime", "fig     elderberry", "cherry  kiwi"]


def test_gap_option(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "-w", "80", "-g", "1", "a", "b") == ["a b"]


def test_items_come_from_stdin_and_empty_lines_are_skipped(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a\r\n\nbb\nc\n"))
    assert _run(capsys, "-w", "80") == ["a  bb  c"]


def test_no_items_print_nothing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["-w", "10"]) == 0
    assert capsys.readouterr().out == ""


def test_width_defaults_to_the_terminal(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLUMNS", "8")
    assert _run(capsys, "ab", "cd", "ef") == ["ab  cd", "ef"]


def test_a_terminal_that_reports_no_width_still_gets_one_column(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("shutil.get_terminal_size", lambda: os.terminal_size((0, 0)))
    assert _run(capsys, "ab", "cd") == ["ab", "cd"]


def test_input_and_output_are_utf8_with_bad_bytes_replaced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = io.BytesIO()
    stdin = io.TextIOWrapper(io.BytesIO(b"a\xff\n"), encoding="cp1252")
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(out, encoding="ascii", newline=""))
    assert main(["-w", "20", "--", "x", "\u65e5"]) == 0
    assert main(["-w", "20"]) == 0
    sys.stdout.flush()
    assert out.getvalue() == "x  \u65e5\na\ufffd\n".encode()


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-w", "0", "a"], "must be at least 1, not 0"),
        (["-w", "x", "a"], "expected a whole number, not 'x'"),
        (["-g", "-1", "a"], "must be at least 0, not -1"),
        (["-w", "9", "a\tb"], "str.expandtabs"),
    ],
)
def test_bad_options_and_items_exit_two(
    capsys: pytest.CaptureFixture[str], argv: list[str], message: str
) -> None:
    assert message in _fails(capsys, *argv)


def test_tabs_from_stdin_are_rejected(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a\tb\n"))
    assert "control characters" in _fails(capsys, "-w", "9")


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out == f"colfit {colfit.__version__}\n"


class _ClosedPipe(io.StringIO):
    def __init__(self, error: OSError) -> None:
        super().__init__()
        self.error = error

    def write(self, text: str) -> int:
        raise self.error

    def fileno(self) -> int:
        return self.descriptor

    descriptor = -1


@pytest.mark.parametrize("code", [errno.EPIPE, errno.EINVAL])
def test_a_closed_pipe_is_quiet(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, code: int) -> None:
    error: OSError = BrokenPipeError() if code == errno.EPIPE else OSError(code, "closed")
    sink = _ClosedPipe(error)
    with open(tmp_path / "out", "w") as handle:
        sink.descriptor = handle.fileno()
        monkeypatch.setattr(sys, "stdout", sink)
        assert main(["-w", "10", "a"]) == 0
        # The descriptor now points at the null device: later writes vanish quietly.
        os.write(handle.fileno(), b"late")
    assert (tmp_path / "out").read_bytes() == b""


def test_other_write_errors_are_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _ClosedPipe(OSError(errno.ENOSPC, "full")))
    with pytest.raises(OSError, match="full"):
        main(["-w", "10", "a"])


def test_module_entry_point_in_a_subprocess_reads_and_writes_utf8() -> None:
    # No encoding variables: a pipe gets the platform default unless the tool sets UTF-8.
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    env["PYTHONPATH"] = str(SRC)
    result = subprocess.run(
        [sys.executable, "-m", "colfit", "-w", "12"],
        input="\u65e5\u672c\nx\ny\n".encode(),
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().splitlines() == ["\u65e5\u672c  x  y"]
