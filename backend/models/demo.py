"""Fallback used ONLY while a real model is missing. Crude colour rules, not real predictions."""
import numpy as np
from backend.models.base import BoundaryResult, TissueResult, SeverityResult


def boundary(img):
    a = np.asarray(img.convert("RGB")).astype(int)
    return BoundaryResult(mask=(a[..., 0] > a[..., 1] + 45) & (a[..., 0] > a[..., 2] + 35))


def tissue(img, mask):
    a = np.asarray(img.convert("RGB")).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    dark = mask & (a.sum(-1) < 200); yel = mask & ~dark & (r > 150) & (g > 130) & (b < 110); gr = mask & ~dark & ~yel
    seg = np.zeros((*mask.shape, 3), "uint8"); seg[gr] = (59, 178, 115); seg[yel] = (245, 200, 66); seg[dark] = (229, 72, 61)
    n = max(int(mask.sum()), 1)
    return TissueResult(gran=gr.sum() / n * 100, slough=yel.sum() / n * 100, necro=dark.sum() / n * 100, seg=seg)


def severity(img, features):
    p = features["area_pct"]
    return SeverityResult(grade=1 if p < 5 else 2 if p < 15 else 3, confidence=None)
