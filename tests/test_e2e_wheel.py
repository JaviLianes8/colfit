"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with COLFIT_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("COLFIT_E2E") != "1", reason="set COLFIT_E2E=1 to build"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
import colfit as c

assert "site-packages" in c.__file__, c.__file__
assert importlib.metadata.version("colfit") == c.__version__
assert importlib.resources.files("colfit").joinpath("py.typed").is_file()
assert sorted(c.__all__) == sorted(
    ["Align", "Order", "Side", "columnize", "display_width", "fit", "graphemes", "pad",
     "truncate", "wrap"]
)
family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
assert c.display_width(family + "\u65e5\x1b[31mx\x1b[0m") == 5
assert c.graphemes("e\u0301" + family) == ["e\u0301", family]
assert c.truncate("\x1b[31mred text\x1b[0m", 4) == "\x1b[31mred\u2026\x1b[0m"
assert c.truncate("abcdefghij", 7, side="middle") == "abc\u2026hij"
assert c.fit("\u65e5\u672c\u8a9e", 4) == "\u65e5\u2026 "
assert c.pad("ab", 5, align="center") == " ab  "
assert c.wrap("aa bb cc", 5, max_lines=1) == ["aa b\u2026"]
assert c.columnize(["a", "b", "c"], 4) == "a  b\nc"
for call, error in (
    (lambda: c.truncate(b"x", 1), TypeError),
    (lambda: c.pad("x", -1), ValueError),
    (lambda: c.wrap("x\ty", 5), ValueError),
):
    try:
        call()
    except error:
        pass
    else:
        raise AssertionError(error)
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None, stdin: bytes = b"") -> bytes:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [str(c) for c in cmd], cwd=cwd, input=stdin, capture_output=True, env=env, check=False
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    (wheel,) = dist.glob("colfit-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if "sources" in name or name.startswith("tests/")]
    assert {"colfit/py.typed", "colfit/__main__.py", "colfit/_tables.py"} <= set(names)

    _run(sys.executable, "-m", "build", "--sdist", "--outdir", dist, ROOT)
    (sdist,) = dist.glob("colfit-*.tar.gz")
    with tarfile.open(sdist) as archive:
        members = archive.getnames()
    data = [name for name in members if "/tests/sources/" in name]
    assert data == [name for name in data if name.endswith("/MANIFEST.txt")]

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    _run(python, "-m", "pip", "install", "-q", wheel)

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    assert _run(python, "-I", "-c", PROGRAM, cwd=work).decode().splitlines() == ["e2e ok"]

    script = bindir / ("colfit.exe" if sys.platform == "win32" else "colfit")
    out = _run(script, "-w", "10", "--down", "a", "b", "c", "d", "e", cwd=work)
    assert out.decode().splitlines() == ["a  c  e", "b  d"]
    out = _run(python, "-I", "-m", "colfit", "-w", "8", cwd=work, stdin=b"ab\ncd\nef\n")
    assert out.decode().splitlines() == ["ab  cd", "ef"]
    bad = subprocess.run([str(script), "-w", "0", "x"], cwd=work, capture_output=True, check=False)
    assert bad.returncode == 2
    assert b"must be at least 1" in bad.stderr
