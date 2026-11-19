"""Create RANDOM-weight checkpoints in the same formats as the real ones, so the pipeline plumbing can be tested
without the trained files. The predictions from these are meaningless. Never use them for real results.

    python tests/make_dummy_weights.py <output_folder>
"""
import json
import sys
from pathlib import Path

import segmentation_models_pytorch as smp
import torch
from torchvision import models
import torch.nn as nn


def main(out):
    out = Path(out)
    (out / "boundary").mkdir(parents=True, exist_ok=True)
    (out / "tissue").mkdir(parents=True, exist_ok=True)
    (out / "severity").mkdir(parents=True, exist_ok=True)

    # Model 1: plain state_dict, as saved by torch.save(model.state_dict(), ...)
    m = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=1)
    torch.save(m.state_dict(), out / "boundary" / "boundary_model_final_all46.pth")

    # Model 2: dict checkpoints with state_dict/arch/encoder (experiment format) and one Part-1 style (no arch key)
    for name, with_meta in (("sup_ctrl", True), ("sup_lovasz", True), ("part1_supervised", False)):
        t = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=4)
        ck = {"state_dict": t.state_dict(), "epoch": 1}
        if with_meta:
            ck.update(arch="unet", encoder="resnet34")
        torch.save(ck, out / "tissue" / f"{name}.pt")

    # Model 3: DenseNet121 + meta json
    d = models.densenet121(weights=None)
    d.classifier = nn.Linear(d.classifier.in_features, 4)
    torch.save(d.state_dict(), out / "severity" / "severity_final.pt")
    json.dump({"name": "densenet121_strongaug", "arch": "densenet121",
               "classes": ["Grade 1", "Grade 2", "Grade 3", "Grade 4"]},
              open(out / "severity" / "severity_final_meta.json", "w"))
    print("dummy weights written to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dummy_weights")
