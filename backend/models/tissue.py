"""Person B - tissue segmentation. TEMPLATE: fill the 3 marked places.
Until load() works, the app uses demo output for this stage.
"""
import numpy as np
from PIL import Image
from config import TISSUE_WEIGHTS
from backend.models.base import BaseModel, TissueResult, ModelNotReady

COLORS = {"gran": (59, 178, 115), "slough": (245, 200, 66), "necro": (229, 72, 61)}


class TissueModel(BaseModel):
    name = "tissue"

    def load(self):
        self._check_weights()
        # 1) PERSON B: load your model here, e.g. self.net = ...; self.net.eval()
        raise ModelNotReady("tissue: load() not implemented yet")
        # self.ready = True   <- enable after step 1 works

    def predict(self, img: Image.Image, mask: np.ndarray) -> TissueResult:
        # 2) PERSON B: run your model on `img` (PIL RGB). `mask` is Person A's wound mask (bool HxW).
        #    Get a label map `lab` (HxW ints): 0=background, 1=granulation, 2=slough, 3=necrotic.
        lab = ...
        # 3) Convert to the output contract (leave this part as is)
        wound = (lab > 0) if mask is None else mask & (lab > 0)
        n = max(int(wound.sum()), 1)
        pct = {k: float(((lab == i) & wound).sum()) / n * 100 for i, k in enumerate(["gran", "slough", "necro"], 1)}
        seg = np.zeros((*lab.shape, 3), "uint8")
        for i, k in enumerate(["gran", "slough", "necro"], 1):
            seg[(lab == i) & wound] = COLORS[k]
        return TissueResult(gran=pct["gran"], slough=pct["slough"], necro=pct["necro"], seg=seg)
