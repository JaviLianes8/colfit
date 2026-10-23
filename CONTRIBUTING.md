# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/colfit/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Most tests call the functions on strings. A
  few run real programs: the command line as a subprocess, GNU `ls` when it is installed,
  and, with `COLFIT_E2E=1`, a wheel built and installed in a throwaway venv. The Unicode
  tests read the sources that `python scripts/fetch_sources.py` downloads into
  `tests/sources` and are skipped until then.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
