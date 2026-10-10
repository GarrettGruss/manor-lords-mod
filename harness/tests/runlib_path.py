"""Import this first in a test file. It makes the runlib package importable."""

import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))
