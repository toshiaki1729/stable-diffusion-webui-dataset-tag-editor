import math

from PIL import Image
from transformers import pipeline
import torch

from modules import devices, shared
from scripts.tagger import Tagger

# brought and modified from https://huggingface.co/spaces/cafeai/cafe_aesthetic_demo/blob/main/app.py

# I'm not sure if this is really working
BATCH_SIZE = 8

class CafeAIAesthetic(Tagger):
    def load(self):
        if devices.device.index is None:
            dev = torch.device(devices.device.type, 0)
        else:
            dev = devices.device
        self.pipe_aesthetic = pipeline("image-classification", "cafeai/cafe_aesthetic", device=dev, batch_size=BATCH_SIZE)
    
    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.pipe_aesthetic = None
            devices.torch_gc()

    def start(self):
        self.load()
        return self

    def stop(self):
        self.unload()

    def _get_score(self, data):
        final = {}
        for d in data:
            final[d["label"]] = d["score"]
        ae = final['aesthetic']

        # edit here to change tag
        return [f"[CAFE]score_{math.floor(ae*10)}"]

    def predict(self, image: Image.Image, threshold=None):
        data = self.pipe_aesthetic(image, top_k=2)
        return self._get_score(data)
    
    def predict_pipe(self, data: list[Image.Image], threshold=None):
        if data is None:
            return
        for out in self.pipe_aesthetic(data, batch_size=BATCH_SIZE):
            yield self._get_score(out)

    def name(self):
        return "cafeai aesthetic classifier"