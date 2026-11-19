"""Model 2: tissue segmentation (4 classes), ensemble of the top-3 models by validation Dice.
Ported from WoundTrack_Person_B.ipynb (load_checkpoint_model, make_predictor, ens_top3)."""
from __future__ import annotations

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn.functional as F

from .utils import TISSUE_CLASS_NAMES, normalise

_ARCHS = {"unet": smp.Unet, "unetplusplus": smp.UnetPlusPlus}


def _load_member(path, device):
    ck = torch.load(str(path), map_location=device, weights_only=False)
    arch, enc = ck.get("arch", "unet"), ck.get("encoder", "resnet34")  # Part-1 checkpoints carry no arch key
    m = _ARCHS[arch](encoder_name=enc, encoder_weights=None, in_channels=3, classes=4)
    m.load_state_dict(ck["state_dict"])
    return m.to(device).eval()


class TissueEnsemble:
    def __init__(self, checkpoints, device, size=512, tta=False):
        if not checkpoints:
            raise ValueError("No tissue checkpoints found (expected the 3 ensemble .pt files in weights/tissue/)")
        self.device, self.size, self.tta = device, size, tta
        self.members = [_load_member(p, device) for p in checkpoints]

    def _probs(self, x):
        views = [lambda t: t]
        if self.tta:  # horizontal-flip TTA (self-inverse), optional
            views.append(lambda t: t.flip(-1))
        acc = 0
        for v in views:
            for m in self.members:
                acc = acc + v(F.softmax(m(v(x)).float(), dim=1))
        return acc / (len(views) * len(self.members))

    @torch.no_grad()
    def predict(self, image_rgb: np.ndarray, wound_mask: np.ndarray | None = None) -> dict:
        h, w = image_rgb.shape[:2]
        resized = cv2.resize(image_rgb, (self.size, self.size), interpolation=cv2.INTER_LINEAR)  # plain resize, as trained
        x = torch.from_numpy(normalise(resized)).unsqueeze(0).to(self.device)
        probs = F.interpolate(self._probs(x), size=(h, w), mode="bilinear", align_corners=False)
        label_map = probs.argmax(1)[0].cpu().numpy().astype(np.uint8)

        counted = label_map
        if wound_mask is not None:  # optional: only count tissue inside the Model 1 wound mask
            counted = np.where(wound_mask.astype(bool), label_map, 0)

        counts = {name: int((counted == i).sum()) for i, name in enumerate(TISSUE_CLASS_NAMES) if i > 0}
        total = sum(counts.values())  # percentages are over tissue pixels (classes 1-3), as in the notebook
        pct = {f"{k}_pct": (round(100.0 * v / total, 2) if total else None) for k, v in counts.items()}
        return {"label_map": label_map, "tissue_px": total, **pct}
