"""Shared constants (no streamlit)."""
from pathlib import Path

NAVY, TEAL, MINT, BG = "#0F2A3D", "#1B6B5F", "#E3F3F0", "#F0F6F6"

ROOT = Path(__file__).resolve().parent

# Tissue classes predicted by the model: (label, visit key, colour). Callus is thickened skin, NOT necrotic tissue.
# Keep these colours in sync with TISSUE_COLORS in woundtrack/utils.py.
TISSUE = [("Granulation", "gran", "#3BB273"), ("Fibrin", "fibrin", "#F5C842"), ("Callus", "callus", "#5B8DEF")]

# Model weights live in weights/boundary, weights/tissue and weights/severity (see weights/README.txt and
# woundtrack/config.py). Set WOUNDTRACK_WEIGHTS to use another folder.
