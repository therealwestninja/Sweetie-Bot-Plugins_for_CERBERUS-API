#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in sorted(ROOT.rglob("*")):
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1
    indent = "  " * depth
    print(f"{indent}{rel.name}/" if path.is_dir() else f"{indent}{rel.name}")
