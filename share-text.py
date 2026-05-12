#!/usr/bin/env python3
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"

if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]])

from share_text.main import main


if __name__ == "__main__":
    raise SystemExit(main())
