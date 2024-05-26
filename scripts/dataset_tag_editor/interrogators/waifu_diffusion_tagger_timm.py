from PIL import Image
from typing import Tuple

import torch
from torch.nn import functional as F
import torchvision.transforms as tf
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from modules import shared, devices
import launch


class ImageDataset(Dataset):
    def __init__(self, images:list[Image.Image], transforms:tf.Compose=None):
        self.images = images
        self.transforms = transforms

    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, i):
        img = self.images[i]
        if self.transforms is not None:
            img = self.transforms(img)
        return img



class WaifuDiffusionTaggerTimm:
    # some codes are brought from https://github.com/neggles/wdv3-timm and modified

    def __init__(self, model_repo, label_filename="selected_tags.csv"):
        self.LABEL_FILENAME = label_filename
        self.MODEL_REPO = model_repo
        self.model = None
        self.transform = None
        self.labels = []

    def load(self):
        import huggingface_hub
        
        if not launch.is_installed("timm"):
            launch.run_pip(
                "install -U timm",
                "requirements for dataset-tag-editor [timm]",
            )
        import timm
        from timm.data import create_transform, resolve_data_config

        if not self.model:
            self.model: torch.nn.Module = timm.create_model(
                "hf-hub:" + self.MODEL_REPO
            ).eval()
            state_dict = timm.models.load_state_dict_from_hf(self.MODEL_REPO)
            self.model.load_state_dict(state_dict)
            self.model.to(devices.device)
            self.transform = create_transform(
                **resolve_data_config(self.model.pretrained_cfg, model=self.model)
            )

        path_label = huggingface_hub.hf_hub_download(
            self.MODEL_REPO, self.LABEL_FILENAME
        )
        import pandas as pd

        self.labels = pd.read_csv(path_label)["name"].tolist()

    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.model = None
            devices.torch_gc()

    def apply(self, image: Image.Image):
        if not self.model:
            return []

        image_t: torch.Tensor = self.transform(image).unsqueeze(0)
        image_t = image_t[:, [2, 1, 0]]
        image_t = image_t.to(devices.device)
        
        with torch.inference_mode():
            features = self.model.forward(image_t)
            probs = F.sigmoid(features).detach().cpu().numpy()

        labels: list[Tuple[str, float]] = list(zip(self.labels, probs[0].astype(float)))

        return labels
    

    def apply_multi(self, images: list[Image.Image], batch_size: int):
        if not self.model:
            return []

        dataset = ImageDataset(images, self.transform)
        dataloader = DataLoader(dataset, batch_size=batch_size)
        
        with torch.inference_mode():
            for batch in tqdm(dataloader):
                batch = batch[:, [2, 1, 0]].to(devices.device)
                features = self.model.forward(batch)
                probs = F.sigmoid(features).detach().cpu().numpy()
                labels: list[Tuple[str, float]] = [list(zip(self.labels, probs[i].astype(float))) for i in range(probs.shape[0])]
                yield labels
