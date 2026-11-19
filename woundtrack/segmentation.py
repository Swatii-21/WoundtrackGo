"""Model 1: wound boundary (U-Net, ResNet encoder).
Ported from WOUNDTRACK_PRO_cleaned.ipynb (load_unet + segment_wound)."""
from __future__ import annotations

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch

from .utils import normalise


def _load_unet(path, encoder, device):
    net = smp.Unet(encoder, encoder_weights=None, in_channels=3, classes=1)
    ckpt = torch.load(str(path), map_location=device, weights_only=False)
    state = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
    net.load_state_dict(state)
    return net.to(device).eval()


class BoundarySegmenter:
    """One checkpoint, or several (probabilities are averaged, as in the R34+R50 ensemble)."""

    def __init__(self, models, device, size=512, threshold=0.5, min_wound_px=300):
        if not models:
            raise ValueError("No boundary checkpoint configured")
        self.device, self.size, self.thr, self.min_px = device, size, threshold, min_wound_px
        self.nets = [_load_unet(p, enc, device) for p, enc in models]

    @torch.no_grad()
    def predict(self, image_rgb: np.ndarray) -> dict:
        h, w = image_rgb.shape[:2]
        size = self.size
        scale = size / max(h, w)
        nh, nw = int(round(h * scale)), int(round(w * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        resized = cv2.resize(image_rgb, (nw, nh), interpolation=interp)

        canvas = np.zeros((size, size, 3), dtype=np.uint8)  # letterbox: black padding, aspect ratio kept
        canvas[:nh, :nw] = resized
        x = torch.from_numpy(normalise(canvas)).unsqueeze(0).to(self.device)

        probs = torch.stack([torch.sigmoid(n(x))[0, 0] for n in self.nets]).mean(0).cpu().numpy()
        prob = cv2.resize(probs[:nh, :nw], (w, h), interpolation=cv2.INTER_LINEAR)  # drop padding, original size
        mask = (prob > self.thr).astype(np.uint8)

        area_px = int(mask.sum())
        return {
            "mask": mask,
            "area_px": area_px,
            "area_frac": float(mask.mean()),
            "max_prob": float(prob.max()),
            "detected": area_px >= self.min_px,
        }
