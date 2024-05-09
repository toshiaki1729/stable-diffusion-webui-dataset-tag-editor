from PIL import Image
import torch
import torch.nn as nn
import numpy as np
import math

from transformers import CLIPModel, CLIPProcessor

from modules import devices, shared
from scripts import model_loader
from scripts.paths import paths
from scripts.tagger import Tagger

# brought from https://github.com/christophschuhmann/improved-aesthetic-predictor/blob/main/simple_inference.py and modified
class Classifier(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.input_size = input_size
        self.layers = nn.Sequential(
            nn.Linear(self.input_size, 1024),
            nn.Dropout(0.2),
            nn.Linear(1024, 128),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.Dropout(0.1),
            nn.Linear(64, 16),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        return self.layers(x)

# brought and modified from https://github.com/waifu-diffusion/aesthetic/blob/main/aesthetic.py
def image_embeddings(image:Image, model:CLIPModel, processor:CLIPProcessor):
    inputs = processor(images=image, return_tensors='pt')['pixel_values']
    inputs = inputs.to(devices.device)
    result:np.ndarray = model.get_image_features(pixel_values=inputs).cpu().detach().numpy()
    return (result / np.linalg.norm(result)).squeeze(axis=0)


class ImprovedAestheticPredictor(Tagger):
    def load(self):
        MODEL_VERSION = "sac+logos+ava1-l14-linearMSE"
        file = model_loader.load(
            model_path=paths.models_path / "aesthetic" / f"{MODEL_VERSION}.pth",
            model_url=f'https://github.com/christophschuhmann/improved-aesthetic-predictor/raw/main/{MODEL_VERSION}.pth'
        )
        CLIP_REPOS = 'openai/clip-vit-large-patch14'
        self.model = Classifier(768)
        self.model.load_state_dict(torch.load(file))
        self.model = self.model.to(devices.device)
        self.clip_processor = CLIPProcessor.from_pretrained(CLIP_REPOS)
        self.clip_model = CLIPModel.from_pretrained(CLIP_REPOS).to(devices.device).eval()
    
    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.model = None
            self.clip_processor = None
            self.clip_model = None
            devices.torch_gc()

    def start(self):
        self.load()
        return self

    def stop(self):
        self.unload()

    def predict(self, image: Image.Image, threshold=None):
        image_embeds = image_embeddings(image, self.clip_model, self.clip_processor)
        prediction:torch.Tensor = self.model(torch.from_numpy(image_embeds).float().to(devices.device))
        # edit here to change tag
        return [f"[IAP]score_{math.floor(prediction.item())}"]

    def name(self):
        return "Improved Aesthetic Predictor"