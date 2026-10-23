"""Results compared with independent programs run live: GNU ls, textwrap and format().

GNU ls (coreutils) lays file names out with the same rule as ``columnize``: the most
columns that fit, two spaces apart. It keeps the last screen column free, so ``ls -w W``
matches ``columnize(names, W - 1)``, and it reserves at least three columns per column,
so the names here are three characters or more. The test skips when no GNU ls is found.
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from colfit import Align, columnize, pad, wrap

FORMAT_ALIGN: dict[Align, str] = {"left": "<", "center": "^", "right": ">"}


def _gnu_ls() -> str:
    found = shutil.which("ls")
    if found is None:
        pytest.skip("no ls on PATH")
    version = subprocess.run([found, "--version"], capture_output=True, text=True, check=False)
    if "GNU coreutils" not in version.stdout:
        pytest.skip("ls is not GNU coreutils")
    return found


def _ls(ls: str, folder: Path, flag: str, width: int) -> str:
    env = {**os.environ, "LC_ALL": "C", "QUOTING_STYLE": "literal"}
    done = subprocess.run(
        [ls, flag, "-T", "0", "-w", str(width), str(folder)],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return done.stdout.rstrip("\n")


def test_columnize_lays_names_out_as_gnu_ls_does(tmp_path: Path) -> None:
    ls = _gnu_ls()
    rng = random.Random(1991)
    for case in range(60):
        folder = tmp_path / str(case)
        folder.mkdir()
        names: set[str] = set()
        count = rng.randint(1, 40)
        while len(names) < count:
            names.add("".join(rng.choices("abcdefgh", k=rng.choice([3, 3, 4, 6, 9, 15, 24]))))
        for name in names:
            (folder / name).touch()
        width = rng.randint(4, 120)
        ordered = sorted(names)
        assert _ls(ls, folder, "-C", width) == columnize(ordered, width - 1, order="columns")
        assert _ls(ls, folder, "-x", width) == columnize(ordered, width - 1, order="rows")


def test_wrap_matches_textwrap_on_plain_words() -> None:
    # Within its domain: ASCII words no wider than the line, an indent no wider than the
    # line, one paragraph. textwrap breaks long words to fill a line; wrap starts them anew.
    rng = random.Random(7)
    checked = 0
    for _ in range(20000):
        width = rng.randint(1, 30)
        words = ["".join(rng.choices("abcde", k=rng.randint(1, width))) for _ in range(12)]
        spaces = [" " * rng.choice([1, 1, 1, 2, 3]) for _ in words]
        text = " " * rng.randint(0, width) + "".join(
            w + s for w, s in zip(words, spaces, strict=True)
        )
        text = text[: rng.randint(0, len(text))]
        if not text.strip() or any(len(word) > width for word in text.split()):
            continue  # spaces alone are one empty line here and no line in textwrap
        assert wrap(text, width) == textwrap.wrap(text, width, break_on_hyphens=False), text
        checked += 1
    assert checked > 15000


def test_pad_matches_format_alignment() -> None:
    rng = random.Random(3)
    for _ in range(20000):
        text = "".join(rng.choices("ab -", k=rng.randint(0, 9)))
        width, fill = rng.randint(0, 14), rng.choice(" .*-")
        align = rng.choice(list(FORMAT_ALIGN))
        expected = format(text, f"{fill}{FORMAT_ALIGN[align]}{width}")
        assert pad(text, width, align=align, fill=fill) == expected
