#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
dirs = [
    "var/log",
    "var/run",
    "var/tmp",
]
for d in dirs:
    path = ROOT / d
    path.mkdir(parents=True, exist_ok=True)
    print(f"created: {path}")
print("bootstrap complete")
