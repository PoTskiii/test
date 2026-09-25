"""Hordejakten 2026 localisation engine.

Evidence layers (each a log-likelihood surface on a common lat/lon grid) are
combined into a posterior over where the box stands; see README.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MAGNUS = RAW / "magnus"
DEFAULTNO = MAGNUS / "public" / "data" / "defaultno"
EVIDENCE = ROOT / "evidence"
OUTPUT = ROOT / "output"
