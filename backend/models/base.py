"""Result containers for the demo fallback. NO streamlit here.

The real models live in the top-level `woundtrack` package (see backend/service.py). This module and demo.py are used
only when that package cannot load (weights or torch missing), so the screens can still be developed.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class BoundaryResult:
    mask: np.ndarray             # bool, shape (H, W), same size as the input image


@dataclass
class TissueResult:
    gran: float                  # % of the analysed region (0-100)
    fibrin: float
    callus: float
    seg: np.ndarray              # uint8 RGB picture: green=granulation, yellow=fibrin, blue=callus


@dataclass
class SeverityResult:
    grade: Optional[int]
    confidence: Optional[float]  # 0-100, or None
