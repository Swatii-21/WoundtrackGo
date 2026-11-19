Put the trained model files here (folders are read by woundtrack/config.py):

  weights/boundary/boundary_model_final_all46.pth      Model 1, wound boundary (U-Net ResNet34)
  weights/tissue/*.pt                                  Model 2, the 3 ensemble members (every *.pt in the folder is used)
  weights/severity/severity_final.pt                   Model 3, severity grade (DenseNet121)
  weights/severity/severity_final_meta.json            ... and its meta file ({"arch": ..., "classes": [...]})

To keep the weights elsewhere set the WOUNDTRACK_WEIGHTS environment variable to that folder.
If any file is missing the app runs in DEMO MODE (placeholder results, shown with a banner).
Set WOUNDTRACK_REQUIRE_MODELS=1 to make the app refuse to start instead.
