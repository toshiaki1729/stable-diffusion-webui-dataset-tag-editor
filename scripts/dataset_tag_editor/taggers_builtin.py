from typing import Optional

from PIL import Image
import numpy as np
import torch

from modules import devices, shared
from modules import deepbooru as db

from scripts.tagger import Tagger, get_replaced_tag
from .interrogators import BLIP2Captioning, GITLargeCaptioning, WaifuDiffusionTagger, WaifuDiffusionTaggerTimm


class BLIP(Tagger):
    def start(self):
        shared.interrogator.load()
    
    def stop(self):
        shared.interrogator.unload()

    def predict(self, image:Image.Image, threshold=None):
        tags = shared.interrogator.generate_caption(image).split(',')
        return [t for t in tags if t]
    
    def name(self):
        return 'BLIP'



class BLIP2(Tagger):
    def __init__(self, repo_name):
        self.interrogator = BLIP2Captioning("Salesforce/" + repo_name)
        self.repo_name = repo_name
    
    def start(self):
        self.interrogator.load()

    def stop(self):
        self.interrogator.unload()

    def predict(self, image:Image, threshold=None):
        tags = self.interrogator.apply(image)[0].split(",")
        return [t for t in tags if t]
    
    # def predict_multi(self, images:list):
    #     captions = self.interrogator.apply(images)
    #     return [[t for t in caption.split(',') if t] for caption in captions]

    def name(self):
        return self.repo_name


class GITLarge(Tagger):
    def __init__(self):
        self.interrogator = GITLargeCaptioning()

    def start(self):
        self.interrogator.load()

    def stop(self):
        self.interrogator.unload()

    def predict(self, image:Image, threshold=None):
        tags = self.interrogator.apply(image)[0].split(",")
        return [t for t in tags if t]
    
    # def predict_multi(self, images:list):
    #     captions = self.interrogator.apply(images)
    #     return [[t for t in caption.split(',') if t] for caption in captions]

    def name(self):
        return "GIT-large-COCO"


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

        tags = []

        for tag, probability in zip(db.model.model.tags, y):
            if threshold and probability < threshold:
                continue
            if not shared.opts.dataset_editor_use_rating and tag.startswith("rating:"):
                continue
            tags.append(get_replaced_tag(tag))

        return tags

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
        
        if not shared.opts.dataset_editor_use_rating:
            labels = labels[4:]

        if threshold is not None:
            if threshold < 0:
                threshold = self.threshold
            tags = [get_replaced_tag(tag) for tag, value in labels if value > threshold]
        else:
            tags = [get_replaced_tag(tag) for tag, _ in labels]

        return tags

    def name(self):
        return self.repo_name


class WaifuDiffusionTimm(WaifuDiffusion):
    def __init__(self, repo_name, threshold, batch_size=4):
        super().__init__(repo_name, threshold)
        self.tagger_inst = WaifuDiffusionTaggerTimm("SmilingWolf/" + repo_name)
        self.batch_size = batch_size
    
    def predict_pipe(self, data: list[Image.Image], threshold: Optional[float] = None):
        for labels_list in self.tagger_inst.apply_multi(data, batch_size=self.batch_size):
            for labels in labels_list:
                if not shared.opts.dataset_editor_use_rating:
                    labels = labels[4:]

                if threshold is not None:
                    if threshold < 0:
                        threshold = self.threshold
                    tags = [get_replaced_tag(tag) for tag, value in labels if value > threshold]
                else:
                    tags = [get_replaced_tag(tag) for tag, _ in labels]

                yield tags


class Z3D_E621(Tagger):
    def __init__(self):
        self.tagger_inst = WaifuDiffusionTagger("toynya/Z3D-E621-Convnext", label_filename="tags-selected.csv")

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
            tags = [get_replaced_tag(tag) for tag, value in labels if value > threshold]
        else:
            tags = [get_replaced_tag(tag) for tag, _ in labels]

        return tags

    def name(self):
        return "Z3D-E621-Convnext"