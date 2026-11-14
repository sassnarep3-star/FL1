"""Make the repo root importable for pytest without packaging the whole tree."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
