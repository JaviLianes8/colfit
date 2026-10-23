"""The stable 1.0 surface: signatures, parameter names, defaults and documented examples."""

from __future__ import annotations

import doctest
import inspect

import pytest

import colfit

POS = inspect.Parameter.POSITIONAL_OR_KEYWORD
KW = inspect.Parameter.KEYWORD_ONLY
EMPTY = inspect.Parameter.empty
ELLIPSIS = chr(0x2026)

SIGNATURES: dict[str, list[tuple[str, inspect._ParameterKind, object]]] = {
    "display_width": [("text", POS, EMPTY)],
    "graphemes": [("text", POS, EMPTY)],
    "truncate": [
        ("text", POS, EMPTY),
        ("width", POS, EMPTY),
        ("ellipsis", KW, ELLIPSIS),
        ("side", KW, "end"),
    ],
    "pad": [("text", POS, EMPTY), ("width", POS, EMPTY), ("align", KW, "left"), ("fill", KW, " ")],
    "fit": [
        ("text", POS, EMPTY),
        ("width", POS, EMPTY),
        ("align", KW, "left"),
        ("ellipsis", KW, ELLIPSIS),
        ("side", KW, "end"),
        ("fill", KW, " "),
    ],
    "wrap": [
        ("text", POS, EMPTY),
        ("width", POS, EMPTY),
        ("max_lines", KW, None),
        ("ellipsis", KW, ELLIPSIS),
    ],
    "columnize": [("items", POS, EMPTY), ("width", POS, 80), ("gap", KW, 2), ("order", KW, "rows")],
}

RETURNS = {
    "display_width": "int",
    "graphemes": "list[str]",
    "truncate": "str",
    "pad": "str",
    "fit": "str",
    "wrap": "list[str]",
    "columnize": "str",
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_signature_is_pinned(name: str) -> None:
    signature = inspect.signature(getattr(colfit, name))
    found = [(p.name, p.kind, p.default) for p in signature.parameters.values()]
    assert found == SIGNATURES[name]
    assert signature.return_annotation == RETURNS[name]


def test_every_function_of_the_api_is_pinned() -> None:
    functions = {name for name in colfit.__all__ if inspect.isfunction(getattr(colfit, name))}
    assert functions == set(SIGNATURES)


def test_public_functions_report_the_package_as_their_module() -> None:
    # Pickles and tracebacks name a private module; the promise is only the package name.
    for name in SIGNATURES:
        assert getattr(colfit, name).__module__.startswith("colfit.")


def _examples(obj: object) -> list[doctest.Example]:
    tests = doctest.DocTestFinder(recurse=False).find(obj)
    return [example for test in tests for example in test.examples]


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_every_function_documents_its_errors_and_has_examples(name: str) -> None:
    function = getattr(colfit, name)
    assert len(_examples(function)) >= 2, name
    assert "Raise" in (function.__doc__ or ""), name


def test_the_package_docstring_shows_the_literal_types() -> None:
    sources = "".join(example.source for example in _examples(colfit))
    for alias in ("Align", "Side", "Order"):
        assert alias in sources


@pytest.mark.parametrize("name", [*sorted(SIGNATURES), "colfit"])
def test_the_examples_pass(name: str) -> None:
    obj = colfit if name == "colfit" else getattr(colfit, name)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    for test in doctest.DocTestFinder(recurse=False).find(obj, globs=vars(colfit)):
        runner.run(test)
    assert runner.summarize(verbose=False).failed == 0
