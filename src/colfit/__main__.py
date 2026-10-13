"""Run the command line tool with ``python -m colfit``."""

from __future__ import annotations

import sys

from colfit._cli import main

if __name__ == "__main__":
    sys.exit(main())
