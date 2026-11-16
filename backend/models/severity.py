"""Person C - severity classifier. TEMPLATE: fill the 3 marked places."""
import numpy as np
from PIL import Image
from config import SEVERITY_WEIGHTS
from backend.models.base import BaseModel, SeverityResult, ModelNotReady

CLASS_TO_GRADE = {0: 1, 1: 2, 2: 3, 3: 4}   # PERSON C: map your class index -> grade shown in the app


class SeverityModel(BaseModel):
    name = "severity"

    def load(self):
        self._check_weights()
        # 1) PERSON C: load your classifier here, e.g. self.net = ...; self.net.eval()
        raise ModelNotReady("severity: load() not implemented yet")
        # self.ready = True   <- enable after step 1 works

    def predict(self, img: Image.Image, features: dict) -> SeverityResult:
        # 2) PERSON C: run your classifier on `img` (PIL RGB) -> probs (numpy array, one value per class).
        #    `features` has area_pct, area_px, gran, slough, necro if your model wants them.
        probs = ...
        # 3) Convert to the output contract (leave this part as is)
        k = int(np.argmax(probs))
        return SeverityResult(grade=CLASS_TO_GRADE[k], confidence=round(float(probs[k]) * 100, 1))
