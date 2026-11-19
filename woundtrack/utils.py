"""Image loading and overlay helpers shared by all stages."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

# Tissue class ids follow the DFUTissue annotation order used in the tissue notebook.
TISSUE_CLASS_NAMES = ["background", "fibrin", "granulation", "callus"]
# RGB palette shared with the Streamlit legend (config.TISSUE in the frontend): granulation green,
# fibrin yellow, callus blue. Callus is NOT necrotic tissue, so it deliberately does not use a red.
TISSUE_COLORS = np.array([(0, 0, 0), (245, 200, 66), (59, 178, 115), (91, 141, 239)], dtype=np.uint8)

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load_rgb(source, max_side: int | None = None) -> np.ndarray:
    """Accept a path, bytes, file-like object, PIL image or HxWx3 array; return uint8 RGB."""
    if isinstance(source, (str, Path)):
        bgr = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"Could not read image: {source}")
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(source, (bytes, bytearray)) or hasattr(source, "read"):
        data = bytes(source) if isinstance(source, (bytes, bytearray)) else source.read()
        bgr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image bytes")
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(source, np.ndarray):
        img = source
        if img.ndim == 2:
            img = np.stack([img] * 3, -1)
        if img.shape[2] == 4:
            img = img[:, :, :3]
        img = img.astype(np.uint8)
    else:  # PIL image
        img = np.array(source.convert("RGB"))

    if max_side and max(img.shape[:2]) > max_side:
        s = max_side / max(img.shape[:2])
        img = cv2.resize(img, (int(round(img.shape[1] * s)), int(round(img.shape[0] * s))),
                         interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(img)


def normalise(rgb_uint8: np.ndarray) -> np.ndarray:
    """uint8 RGB -> float32 CHW, ImageNet-normalised (identical to the training notebooks)."""
    x = (rgb_uint8.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
    return np.ascontiguousarray(x.transpose(2, 0, 1))


def boundary_overlay(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = image.copy()
    if mask.any():
        sel = mask.astype(bool)
        tint = np.zeros_like(out)
        tint[..., 0] = 255
        out[sel] = (0.65 * out[sel] + 0.35 * tint[sel]).astype(np.uint8)
        cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cnts, -1, (255, 255, 0), max(1, image.shape[1] // 300))
    return out


def tissue_overlay(image: np.ndarray, label_map: np.ndarray) -> np.ndarray:
    colour = TISSUE_COLORS[label_map]
    out = (0.55 * image.astype(np.float32) + 0.45 * colour.astype(np.float32)).astype(np.uint8)
    out[label_map == 0] = image[label_map == 0]
    return out


def tissue_color_map(label_map: np.ndarray) -> np.ndarray:
    """Class-id map -> RGB picture (colour per tissue class on black), as shown in the UI."""
    return TISSUE_COLORS[label_map]


def save_rgb(path, rgb: np.ndarray) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    return str(path)
