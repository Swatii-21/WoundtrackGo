"""Person A - wound boundary (U-Net, ResNet34). Already filled in.
CHECK these 3 things against your training notebook (marked VERIFY):
"""
import numpy as np
from PIL import Image
from config import BOUNDARY_WEIGHTS
from backend.models.base import BaseModel, BoundaryResult, get_device


class BoundaryModel(BaseModel):
    name = "boundary"
    INPUT_SIZE = 512                      # VERIFY: size used in training/inference
    MEAN = (0.485, 0.456, 0.406)          # VERIFY: ImageNet normalisation (albumentations default)
    STD = (0.229, 0.224, 0.225)
    THRESHOLD = 0.5                       # fixed at 0.5 so areas are comparable across visits

    def load(self):
        self._check_weights()
        import torch, segmentation_models_pytorch as smp
        self.device = get_device()
        ck = torch.load(self.weights_path, map_location=self.device)
        if isinstance(ck, torch.nn.Module):
            net = ck
        else:
            net = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=1)
            if isinstance(ck, dict):       # VERIFY: key name of your saved checkpoint
                ck = ck.get("model_state_dict", ck.get("state_dict", ck))
            net.load_state_dict(ck)
        self.net = net.to(self.device).eval()
        self.ready = True

    def predict(self, img: Image.Image) -> BoundaryResult:
        import torch
        w, h = img.size
        x = np.asarray(img.convert("RGB").resize((self.INPUT_SIZE, self.INPUT_SIZE)), dtype=np.float32) / 255.0
        x = (x - np.array(self.MEAN, dtype=np.float32)) / np.array(self.STD, dtype=np.float32)
        t = torch.from_numpy(x.transpose(2, 0, 1))[None].to(self.device)
        with torch.no_grad():
            p = torch.sigmoid(self.net(t))[0, 0].cpu().numpy().astype(np.float32)
        p = np.asarray(Image.fromarray(p).resize((w, h), Image.BILINEAR))
        return BoundaryResult(mask=p >= self.THRESHOLD)
