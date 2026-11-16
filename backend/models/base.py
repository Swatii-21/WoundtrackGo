"""Contracts every model must follow. NO streamlit here."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import numpy as np


class ModelNotReady(Exception):
    """Weights missing or model not implemented yet -> pipeline falls back to demo."""


@dataclass
class BoundaryResult:        # Person A
    mask: np.ndarray         # bool, shape (H, W), SAME size as the input image


@dataclass
class TissueResult:          # Person B
    gran: float              # % of wound area (0-100)
    slough: float
    necro: float
    seg: np.ndarray          # uint8 RGB picture (any size): green=granulation, yellow=slough, red=necrotic


@dataclass
class SeverityResult:        # Person C
    grade: int               # severity class as a number, e.g. 1-4
    confidence: Optional[float]  # 0-100, or None if the model gives no probability


def get_device():
    import torch
    if torch.cuda.is_available(): return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available(): return "mps"
    return "cpu"


class BaseModel:
    name = "base"

    def __init__(self, weights_path):
        self.weights_path = Path(weights_path)
        self.ready = False

    def _check_weights(self):
        if not self.weights_path.exists():
            raise ModelNotReady(f"{self.name}: weights not found at {self.weights_path}")

    def load(self):
        """Load weights, then set self.ready = True."""
        raise NotImplementedError
