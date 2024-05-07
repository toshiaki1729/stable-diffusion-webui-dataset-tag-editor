from transformers import AutoProcessor, AutoModelForCausalLM
from modules import shared, devices, lowvram

from scripts.paths import paths


# brought from https://huggingface.co/docs/transformers/main/en/model_doc/git and modified
class GITLargeCaptioning:
    MODEL_REPO = "microsoft/git-large-coco"

    def __init__(self):
        self.processor: AutoProcessor = None
        self.model: AutoModelForCausalLM = None

    def load(self):
        if self.model is None or self.processor is None:
            self.processor = AutoProcessor.from_pretrained(self.MODEL_REPO)
            self.model = AutoModelForCausalLM.from_pretrained(self.MODEL_REPO).to(shared.device)
        lowvram.send_everything_to_cpu()

    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.model = None
            self.processor = None
            devices.torch_gc()

    def apply(self, image):
        if self.model is None or self.processor is None:
            return ""
        inputs = self.processor(images=image, return_tensors="pt").to(shared.device)
        ids = self.model.generate(
            pixel_values=inputs.pixel_values,
            max_length=shared.opts.interrogate_clip_max_length,
        )
        return self.processor.batch_decode(ids, skip_special_tokens=True)[0]
