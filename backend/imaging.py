"""Image helpers + procedural placeholder wound pictures (demo only)."""
import base64, io
import numpy as np
from PIL import Image, ImageFilter

def uri(img):
    b = io.BytesIO(); img.save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()

def synth(seed, pct, mode, n=200):
    """Procedural placeholder wound pictures (demo only)."""
    r = np.random.RandomState(seed); y, x = np.mgrid[0:n, 0:n]; cx, cy = n / 2 + r.randn() * 6, n / 2 + r.randn() * 6
    ang = np.arctan2(y - cy, x - cx); rad = n * .30 * np.sqrt(pct / 12.4) * (1 + .18 * np.sin(3 * ang + seed) + .1 * np.sin(5 * ang + 2 * seed))
    d = np.hypot(x - cx, y - cy); w = d < rad; t = d / rad + .18 * np.sin(x / 9 + seed) * np.cos(y / 11)
    if mode == "mask": return Image.fromarray((w * 255).astype("uint8")).convert("RGB")
    if mode == "seg":
        o = np.zeros((n, n, 3), "uint8"); o[w & (t >= .55)] = (59, 178, 115); o[w & (t < .55)] = (245, 200, 66); o[w & (t < .3)] = (91, 141, 239); return Image.fromarray(o)
    skin = np.array([224, 172, 148]) + r.randn(n, n, 1) * 5
    core = np.clip(np.array([150, 40, 50]) + t[..., None] * np.array([60, 60, 40]), 0, 255)
    m = np.asarray(Image.fromarray((w * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(2)))[..., None] / 255
    return Image.fromarray((skin * (1 - m) + core * m).clip(0, 255).astype("uint8"))

def vimgs(pid, i, v):
    if "img" not in v:
        s = pid * 10 + i; v.update(img=uri(synth(s, v["pct"], "photo")), mask=uri(synth(s, v["pct"], "mask")), seg=uri(synth(s, v["pct"], "seg")))
    return v
