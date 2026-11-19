"""Demo fallback, used ONLY when the real models cannot load. Crude colour rules, NOT real predictions."""
import numpy as np
from PIL import Image

from backend.imaging import uri
from backend.models.base import BoundaryResult, SeverityResult, TissueResult

DISPLAY = (256, 256)
GREEN, YELLOW, BLUE = (59, 178, 115), (245, 200, 66), (91, 141, 239)


def boundary(img):
    a = np.asarray(img.convert("RGB")).astype(int)
    return BoundaryResult(mask=(a[..., 0] > a[..., 1] + 45) & (a[..., 0] > a[..., 2] + 35))


def tissue(img, mask):
    a = np.asarray(img.convert("RGB")).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    dark = mask & (a.sum(-1) < 200); yel = mask & ~dark & (r > 150) & (g > 130) & (b < 110); gr = mask & ~dark & ~yel
    seg = np.zeros((*mask.shape, 3), "uint8"); seg[gr] = GREEN; seg[yel] = YELLOW; seg[dark] = BLUE
    n = max(int(mask.sum()), 1)
    return TissueResult(gran=gr.sum() / n * 100, fibrin=yel.sum() / n * 100, callus=dark.sum() / n * 100, seg=seg)


def severity(img, features):
    p = features["area_pct"]
    return SeverityResult(grade=1 if p < 5 else 2 if p < 15 else 3, confidence=None)


def run(img: Image.Image, date: str) -> dict:
    """All three stages in demo mode; returns the visit dict the pages expect."""
    img = img.convert("RGB")
    mask = boundary(img).mask
    px, pct = int(mask.sum()), float(mask.mean() * 100)
    t = tissue(img, mask)
    s = severity(img, dict(area_pct=pct))
    return dict(date=date, pct=round(pct, 1), px=px, gran=round(t.gran), fibrin=round(t.fibrin), callus=round(t.callus),
                grade=s.grade, conf=s.confidence, demo=["boundary", "tissue", "severity"],
                img=uri(img.resize(DISPLAY)),
                mask=uri(Image.fromarray((mask * 255).astype("uint8")).convert("RGB").resize(DISPLAY, Image.NEAREST)),
                seg=uri(Image.fromarray(np.asarray(t.seg, "uint8")).resize(DISPLAY, Image.NEAREST)))
