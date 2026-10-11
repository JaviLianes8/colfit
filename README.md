# colfit

Arrange strings into evenly sized terminal columns that fit a width, display-width aware.

## Install

```
pip install colfit
```

## Usage

```python
from colfit import columnize

fruits = ["apple", "fig", "cherry", "date", "elderberry", "kiwi", "lime"]

print(columnize(fruits, width=30))
# apple       fig   cherry  date
# elderberry  kiwi  lime

print(columnize(fruits, width=30, order="columns"))
# apple   date        lime
# fig     elderberry
# cherry  kiwi
```

`columnize(items, width=80, *, gap=2, order="rows")` picks the largest number of
columns that fits `width`, separates them by `gap` spaces, and pads each cell to
its column. `order="rows"` fills left to right; `order="columns"` fills top to
bottom like `ls`. Items wider than `width` fall back to a single column.

Widths are measured in terminal cells, so East Asian text lines up:

```python
from colfit import columnize, display_width

display_width("日本")  # 2 wide characters -> 4

print(columnize(["日", "x", "y", "z"], width=6))
# 日  x
# y   z
```

## Why

Splitting a list into aligned columns is a recurring need (think `ls`,
`cmd.Cmd.columnize`, a quick status dump), yet the character-count approach that
most snippets use misaligns the moment a value holds a wide or zero-width
character. `columnize` on PyPI stops at character counts and has not been
released since 2022; getting widths right otherwise means pulling in `wcwidth`.
`colfit` is a small, typed, zero-dependency library that does the width-aware
layout correctly and ships its own display-width helper.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
