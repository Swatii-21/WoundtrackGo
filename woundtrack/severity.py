"""Model 3: severity grade (Grade 1-4), diabetic foot only.
Ported from severity_resnet50_baseline.ipynb (build() + final-model inference)."""
from __future__ import annotations

import json
import re

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

from .utils import normalise


def _build(arch: str, n_classes: int):
    if arch == "resnet50":
        m = models.resnet50(weights=None)
        m.fc = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.fc.in_features, n_classes))
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=None)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, n_classes)
    elif arch == "densenet121":
        m = models.densenet121(weights=None)
        m.classifier = nn.Linear(m.classifier.in_features, n_classes)
    else:
        raise ValueError(f"Unknown severity architecture: {arch}")
    return m


class SeverityClassifier:
    def __init__(self, weights, meta, device, size=224, low_conf=0.5):
        self.device, self.size, self.low_conf = device, size, low_conf
        with open(meta) as f:
            info = json.load(f)
        self.classes = info["classes"]  # e.g. ["Grade 1", "Grade 2", "Grade 3", "Grade 4"]
        self.name = info.get("name", info["arch"])
        self.net = _build(info["arch"], len(self.classes))
        self.net.load_state_dict(torch.load(str(weights), map_location=device, weights_only=False))
        self.net.to(device).eval()

    @torch.no_grad()
    def predict(self, image_rgb: np.ndarray) -> dict:
        # Whole image resized to 224x224, no crop: this is how the model was trained and evaluated.
        resized = cv2.resize(image_rgb, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
        x = torch.from_numpy(normalise(resized)).unsqueeze(0).to(self.device)
        p = torch.softmax(self.net(x), dim=1)[0].cpu().numpy()
        j = int(p.argmax())
        label = self.classes[j]
        digit = re.search(r"\d", label)
        return {
            "grade_label": label,
            "grade_num": int(digit.group()) if digit else j + 1,
            "confidence": round(float(p[j]), 3),
            "low_confidence": bool(p[j] < self.low_conf),
            "probs": {c: round(float(s), 3) for c, s in zip(self.classes, p)},
            "model": self.name,
        }
