#!/usr/bin/env python3
"""Apply CLASS BUSTER's school-safe art theme to an existing WAD."""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from wadlib import Wad
from build_wad import customize

if len(sys.argv) != 3:
    raise SystemExit('usage: python3 tools/retheme_existing.py input.wad output.wad')

source, target = map(Path, sys.argv[1:])
if not source.is_file():
    raise SystemExit(f'WAD not found: {source}')
customize(Wad(str(source)), str(target))
