"""The README examples run and print what they say; metadata agrees with the code."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

import colfit
from colfit._cli import main

ROOT = Path(__file__).resolve().parents[1]


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _blocks(name: str = "README.md") -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


def _expected(block: str) -> list[str]:
    # A run of comment lines right under code is the output of the code above it.
    results: list[str] = []
    open_run = False
    for line in block.splitlines():
        if line.startswith("# ") and open_run:
            results.append(line[2:])
        else:
            open_run = bool(line) and not line.startswith("#")
    return results


def test_the_readme_has_its_four_examples() -> None:
    assert len(_blocks()) == 4


@pytest.mark.parametrize("index", range(4))
def test_each_example_prints_what_its_comments_say(
    index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks()[index]
    exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
    printed = capsys.readouterr().out.splitlines()
    assert printed == _expected(block)
    assert len(printed) >= 1


def test_the_guide_has_its_six_examples() -> None:
    assert len(_blocks("GUIDE.md")) == 6


@pytest.mark.parametrize("index", range(6))
def test_each_guide_example_prints_what_its_comments_say(
    index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks("GUIDE.md")[index]
    exec(compile(block, "GUIDE.md", "exec"), {"__name__": "guide"})
    printed = capsys.readouterr().out.splitlines()
    assert printed == _expected(block)
    assert len(printed) >= 2


def test_readme_links_are_absolute_and_show_the_badge() -> None:
    targets = re.findall(r"\]\(([^)]*)\)", _readme())
    assert targets
    assert all(target.startswith("https://") for target in targets), targets
    assert "(https://lianes8studio.com/certified)" in _readme()
    for name in ("GUIDE.md", "CHANGELOG.md", "LICENSE"):
        assert f"https://github.com/JaviLianes8/colfit/blob/main/{name}" in _readme()


def test_the_command_line_examples_match_the_tool(capsys: pytest.CaptureFixture[str]) -> None:
    session = re.search(r"```\n(\$ colfit .*?)```", _readme(), flags=re.DOTALL)
    assert session is not None
    transcript: list[str] = []
    for line in session.group(1).splitlines():
        if line.startswith("$ colfit "):
            assert main(shlex.split(line[len("$ colfit ") :])) == 0
            transcript += [line, *capsys.readouterr().out.splitlines()]
    assert transcript == session.group(1).splitlines()
    assert len(transcript) == 7


def test_every_public_name_appears_in_the_readme() -> None:
    for name in colfit.__all__:
        assert f"`{name}" in _readme(), name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == colfit.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{colfit.__version__}]" in text


def _shipped() -> list[Path]:
    return [
        *ROOT.glob("*.md"),
        *ROOT.glob("*.toml"),
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("tests/*.py"),
        *ROOT.glob("scripts/*.p*"),
        ROOT / "tests" / "sources" / "MANIFEST.txt",
    ]


def test_no_em_dash_in_any_shipped_text() -> None:
    for path in _shipped():
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_every_source_file_stays_under_two_hundred_lines() -> None:
    for path in _shipped():
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path


def test_sources_are_ascii() -> None:
    for path in [*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/*.p*")]:
        assert path.read_text(encoding="utf-8").isascii(), path
