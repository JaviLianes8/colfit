import importlib.resources

import colfit

PUBLIC_API: list[str] = ["columnize", "display_width"]


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
