"""Runs A -> B -> C. Loads each model once; falls back to demo per stage if a model is not ready."""
import logging
import numpy as np
from PIL import Image
from config import BOUNDARY_WEIGHTS, TISSUE_WEIGHTS, SEVERITY_WEIGHTS
from backend.imaging import uri
from backend.models import demo
from backend.models.base import ModelNotReady
from backend.models.boundary import BoundaryModel
from backend.models.tissue import TissueModel
from backend.models.severity import SeverityModel

log = logging.getLogger("woundtrack")
DISPLAY = (256, 256)


class Pipeline:
    def __init__(self):
        self.boundary = BoundaryModel(BOUNDARY_WEIGHTS)
        self.tissue = TissueModel(TISSUE_WEIGHTS)
        self.severity = SeverityModel(SEVERITY_WEIGHTS)
        self.status, self.errors = {}, {}

    def load(self):
        for m in (self.boundary, self.tissue, self.severity):
            try:
                m.load(); self.status[m.name] = "model"
            except (ModelNotReady, NotImplementedError, ImportError) as e:
                self.status[m.name] = "demo"; self.errors[m.name] = str(e); log.warning("%s -> demo (%s)", m.name, e)
        return self.status

    def _stage(self, m, real_fn, demo_fn, used):
        if m.ready:
            try:
                return real_fn()
            except Exception as e:                      # inference failed: log it, keep the app alive
                log.exception("%s inference failed", m.name); self.errors[m.name] = repr(e)
        used.append(m.name)
        return demo_fn()

    def run(self, img: Image.Image, date: str) -> dict:
        img = img.convert("RGB"); used = []
        mask = self._stage(self.boundary, lambda: self.boundary.predict(img), lambda: demo.boundary(img), used).mask
        px, pct = int(mask.sum()), float(mask.mean() * 100)
        t = self._stage(self.tissue, lambda: self.tissue.predict(img, mask), lambda: demo.tissue(img, mask), used)
        feats = dict(area_px=px, area_pct=pct, gran=t.gran, slough=t.slough, necro=t.necro)
        s = self._stage(self.severity, lambda: self.severity.predict(img, feats), lambda: demo.severity(img, feats), used)
        return dict(date=date, pct=round(pct, 1), px=px, gran=round(t.gran), slough=round(t.slough), necro=round(t.necro),
                    grade=s.grade, conf=s.confidence, demo=used,
                    img=uri(img.resize(DISPLAY)),
                    mask=uri(Image.fromarray((mask * 255).astype("uint8")).convert("RGB").resize(DISPLAY, Image.NEAREST)),
                    seg=uri(Image.fromarray(np.asarray(t.seg, "uint8")).resize(DISPLAY, Image.NEAREST)))


_P = None


def get_pipeline() -> Pipeline:
    global _P
    if _P is None:
        _P = Pipeline(); _P.load()
    return _P
