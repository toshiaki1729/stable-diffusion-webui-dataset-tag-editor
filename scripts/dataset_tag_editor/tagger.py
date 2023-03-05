from PIL import Image
import re
import torch
import numpy as np
from typing import Optional, Dict
from modules import devices, shared
from modules import deepbooru as db

from .interrogator import Interrogator
from .interrogators import WaifuDiffusionTagger


class Tagger(Interrogator):
    def start(self):
        pass
    def stop(self):
        pass
    def predict(self, image: Image.Image, threshold: Optional[float]):
        raise NotImplementedError()
    def name(self):
        raise NotImplementedError()


def get_replaced_tag(tag: str):
    use_spaces = shared.opts.deepbooru_use_spaces
    use_escape = shared.opts.deepbooru_escape   
    if use_spaces:
        tag = tag.replace('_', ' ')
    if use_escape:
        tag = re.sub(db.re_special, r'\\\1', tag)
    return tag


def get_arranged_tags(probs: Dict[str, float]):
    alpha_sort = shared.opts.deepbooru_sort_alpha
    if alpha_sort:
        return sorted(probs)
    else:
        return [tag for tag, _ in sorted(probs.items(), key=lambda x: -x[1])]


class DeepDanbooru(Tagger):
    def start(self):
        db.model.start()

    def stop(self):
        db.model.stop()

    # brought from webUI modules/deepbooru.py and modified
    def predict(self, image: Image.Image, threshold: Optional[float] = None):
        from modules import images
        
        pic = images.resize_image(2, image.convert("RGB"), 512, 512)
        a = np.expand_dims(np.array(pic, dtype=np.float32), 0) / 255

        with torch.no_grad(), devices.autocast():
            x = torch.from_numpy(a).to(devices.device)
            y = db.model.model(x)[0].detach().cpu().numpy()

        probability_dict = dict()

        for tag, probability in zip(db.model.model.tags, y):
            if threshold and probability < threshold:
                continue
            if tag.startswith("rating:"):
                continue
            probability_dict[get_replaced_tag(tag)] = probability

        return probability_dict

    def name(self):
        return 'DeepDanbooru'


class WaifuDiffusion(Tagger):
    def __init__(self, repo_name, threshold):
        self.repo_name = repo_name
        self.tagger_inst = WaifuDiffusionTagger("SmilingWolf/" + repo_name)
        self.threshold = threshold

    def start(self):
        self.tagger_inst.load()
        return self

    def stop(self):
        self.tagger_inst.unload()

    # brought from https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py and modified
    # set threshold<0 to use default value for now...
    def predict(self, image: Image.Image, threshold: Optional[float] = None):        
        # may not use ratings
        # rating = dict(labels[:4])
        
        labels = self.tagger_inst.apply(image)
        
        if threshold is not None:
            if threshold < 0:
                threshold = self.threshold
            probability_dict = dict([(get_replaced_tag(x[0]), x[1]) for x in labels[4:] if x[1] > threshold])
        else:
            probability_dict = dict([(get_replaced_tag(x[0]), x[1]) for x in labels[4:]])

        return probability_dict

    def name(self):
        return self.repo_name