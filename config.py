"""Shared constants (no streamlit)."""
from pathlib import Path

NAVY, TEAL, MINT, BG = "#0F2A3D", "#1B6B5F", "#E3F3F0", "#F0F6F6"

ROOT = Path(__file__).resolve().parent
WEIGHTS_DIR = ROOT / "weights"
BOUNDARY_WEIGHTS = WEIGHTS_DIR / "boundary_model_final_all46.pth"   # Person A
TISSUE_WEIGHTS = WEIGHTS_DIR / "tissue_model.pth"                   # Person B (rename to your file)
SEVERITY_WEIGHTS = WEIGHTS_DIR / "severity_model.pth"               # Person C (rename to your file)
