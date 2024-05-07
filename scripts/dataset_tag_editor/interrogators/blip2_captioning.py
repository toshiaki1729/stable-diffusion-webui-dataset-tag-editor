from transformers import Blip2Processor, Blip2ForConditionalGeneration

from modules import devices, shared
from scripts.paths import paths


class BLIP2Captioning:
    def __init__(self, model_repo: str):
        self.MODEL_REPO = model_repo
        self.processor: Blip2Processor = None
        self.model: Blip2ForConditionalGeneration = None

    def load(self):
        if self.model is None or self.processor is None:
            self.processor = Blip2Processor.from_pretrained(
                self.MODEL_REPO, cache_dir=paths.setting_model_path
            )
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                self.MODEL_REPO, cache_dir=paths.setting_model_path
            ).to(devices.device)

    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.model = None
            self.processor = None
            devices.torch_gc()

    def apply(self, image):
        if self.model is None or self.processor is None:
            return ""
        inputs = self.processor(images=image, return_tensors="pt").to(devices.device)
        ids = self.model.generate(**inputs)
        return self.processor.batch_decode(ids, skip_special_tokens=True)
