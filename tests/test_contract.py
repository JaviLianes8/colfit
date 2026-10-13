"""The public surface: exactly these names, a version, and type information."""

from __future__ import annotations

import importlib.resources
import typing

import colfit

PUBLIC_API: list[str] = [
    "Align",
    "Order",
    "Side",
    "columnize",
    "display_width",
    "fit",
    "graphemes",
    "pad",
    "truncate",
    "wrap",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(colfit.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in colfit.__all__:
        assert hasattr(colfit, name)


def test_version_is_a_three_part_string() -> None:
    parts = colfit.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("colfit").joinpath("py.typed").is_file()


def test_the_literal_aliases_list_every_accepted_value() -> None:
    assert typing.get_args(colfit.Align) == ("left", "center", "right")
    assert typing.get_args(colfit.Side) == ("end", "start", "middle")
    assert typing.get_args(colfit.Order) == ("rows", "columns")


def test_the_public_functions_are_documented() -> None:
    for name in colfit.__all__:
        if callable(getattr(colfit, name)) and name[0].islower():
            assert getattr(colfit, name).__doc__, name
