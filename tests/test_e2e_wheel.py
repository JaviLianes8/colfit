"""Build the wheel and sdist, install the wheel in a throwaway venv and use it from outside.

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

import colfit

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("COLFIT_E2E") != "1", reason="set COLFIT_E2E=1 to build"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
import colfit as c

assert "site-packages" in c.__file__, c.__file__
assert importlib.metadata.version("colfit") == c.__version__ == "1.0.0"
assert importlib.resources.files("colfit").joinpath("py.typed").is_file()
public = sorted(name for name in dir(c) if not name.startswith("_"))
assert sorted(c.__all__) == public == sorted(
    ["Align", "Order", "Side", "columnize", "display_width", "fit", "graphemes", "pad",
     "truncate", "wrap"]
), public
meta = importlib.metadata.metadata("colfit")
assert "Development Status :: 5 - Production/Stable" in meta.get_all("Classifier")
assert meta["Requires-Python"] == ">=3.10"
assert meta["License-Expression"] == "MIT AND Unicode-3.0"
assert all("extra ==" in need for need in meta.get_all("Requires-Dist") or [])
family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
assert c.display_width(family + "\u65e5\x1b[31mx\x1b[0m") == 5
assert c.graphemes("e\u0301" + family) == ["e\u0301", family]
assert c.truncate("\x1b[31mred text\x1b[0m", 4) == "\x1b[31mred\u2026\x1b[0m"
assert c.truncate("abcdefghij", 7, side="middle") == "abc\u2026hij"
assert c.fit("\u65e5\u672c\u8a9e", 4) == "\u65e5\u2026 "
assert c.pad("ab", 5, align="center") == " ab  "
assert c.wrap("aa bb cc", 5, max_lines=1) == ["aa b\u2026"]
assert c.wrap("   abcd ef", 5) == ["abcd", "ef"]
assert c.columnize(["a", "b", "c"], 4) == "a  b\nc"
for call, error in (
    (lambda: c.truncate(b"x", 1), TypeError),
    (lambda: c.truncate("x", 1, side=1), TypeError),
    (lambda: c.pad("x", -1), ValueError),
    (lambda: c.wrap("x\ty", 5), ValueError),
    (lambda: c.pad("x\x1b]8;;u", 5), ValueError),
):
    try:
        call()
    except error:
        pass
    else:
        raise AssertionError(error)
print("e2e ok")
"""

CONSUMER = """
from colfit import Align, columnize, fit

def cells(names: list[str], align: Align) -> str:
    return columnize([fit(name, 8, align=align) for name in names], 40)

print(cells(["a", "b"], "right"))
"""


def _run(*cmd: str | Path, cwd: Path | None = None, stdin: bytes = b"") -> bytes:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [str(c) for c in cmd], cwd=cwd, input=stdin, capture_output=True, env=env, check=False
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_built_artifacts_hold_what_they_should(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    _run(sys.executable, "-m", "twine", "check", "--strict", *dist.iterdir())
    (wheel,) = dist.glob("colfit-1.0.0-py3-none-any.whl")
    names = set(zipfile.ZipFile(wheel).namelist())
    package = {name for name in names if not name.startswith("colfit-1.0.0.dist-info/")}
    shipped = {p.relative_to(ROOT / "src").as_posix() for p in (ROOT / "src").rglob("*")}
    assert package == {name for name in shipped if name.endswith((".py", ".typed"))}
    assert "colfit-1.0.0.dist-info/licenses/LICENSE" in names
    assert "colfit-1.0.0.dist-info/licenses/LICENSES/Unicode-3.0.txt" in names
    (sdist,) = dist.glob("colfit-1.0.0.tar.gz")
    with tarfile.open(sdist) as archive:
        members = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}
    assert {"LICENSE", "README.md", "GUIDE.md", "CHANGELOG.md", "pyproject.toml"} <= members
    assert "LICENSES/Unicode-3.0.txt" in members
    assert "tests/sources/MANIFEST.txt" in members
    assert not [m for m in members if m.startswith("tests/sources/") and "MANIFEST" not in m]
    assert not [m for m in members if "IMPROVEMENTS" in m or "CERT-1.0" in m or ".github" in m]
    assert not [m for m in members if "__pycache__" in m or m.endswith(".pyc")]


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    (wheel,) = dist.glob("colfit-*.whl")
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    _run(python, "-m", "pip", "install", "-q", wheel)

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    assert _run(python, "-I", "-c", PROGRAM, cwd=work).decode().splitlines() == ["e2e ok"]

    # The installed type information is what a consumer's type checker sees.
    (work / "consumer.py").write_text(CONSUMER, encoding="utf-8")
    _run(
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--python-executable",
        python,
        "consumer.py",
        cwd=work,
    )
    assert _run(python, "-I", "consumer.py", cwd=work).decode().rstrip() == "       a         b"

    script = bindir / ("colfit.exe" if sys.platform == "win32" else "colfit")
    out = _run(script, "-w", "10", "--down", "a", "b", "c", "d", "e", cwd=work)
    assert out.decode().splitlines() == ["a  c  e", "b  d"]
    out = _run(python, "-I", "-m", "colfit", "-w", "8", cwd=work, stdin=b"ab\ncd\nef\n")
    assert out.decode().splitlines() == ["ab  cd", "ef"]
    out = _run(script, "-w", "9", cwd=work, stdin="\u65e5\u672c\nx\n".encode())
    assert out.decode("utf-8").splitlines() == ["\u65e5\u672c  x"]
    assert _run(script, "--version", cwd=work).decode().strip() == f"colfit {colfit.__version__}"
    bad = subprocess.run([str(script), "-w", "0", "x"], cwd=work, capture_output=True, check=False)
    assert bad.returncode == 2
    assert b"must be at least 1" in bad.stderr
    bad = subprocess.run(
        [str(script), "-w", "9"], cwd=work, input=b"a\tb\n", capture_output=True, check=False
    )
    assert bad.returncode == 2
    assert b"expand tabs" in bad.stderr
