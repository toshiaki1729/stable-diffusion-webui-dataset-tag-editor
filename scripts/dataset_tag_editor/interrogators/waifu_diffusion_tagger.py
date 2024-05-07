from PIL import Image
import numpy as np
from typing import List, Tuple
from modules import shared, devices
import launch


class WaifuDiffusionTagger:
    # brought from https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py and modified
    def __init__(
        self,
        model_name,
        model_filename="model.onnx",
        label_filename="selected_tags.csv",
    ):
        self.MODEL_FILENAME = model_filename
        self.LABEL_FILENAME = label_filename
        self.MODEL_REPO = model_name
        self.model = None
        self.labels = []

    def load(self):
        import huggingface_hub

        if not self.model:
            path_model = huggingface_hub.hf_hub_download(
                self.MODEL_REPO, self.MODEL_FILENAME
            )
            if (
                "all" in shared.cmd_opts.use_cpu
                or "interrogate" in shared.cmd_opts.use_cpu
            ):
                providers = ["CPUExecutionProvider"]
            else:
                providers = [
                    "CUDAExecutionProvider",
                    "DmlExecutionProvider",
                    "CPUExecutionProvider",
                ]

            def check_available_device():
                import torch

                if torch.cuda.is_available():
                    return "cuda"
                elif launch.is_installed("torch-directml"):
                    # This code cannot detect DirectML available device without pytorch-directml
                    try:
                        import torch_directml

                        torch_directml.device()
                    except:
                        pass
                    else:
                        return "directml"
                return "cpu"

            if not launch.is_installed("onnxruntime"):
                dev = check_available_device()
                if dev == "cuda":
                    launch.run_pip(
                        "install -U onnxruntime-gpu",
                        "requirements for dataset-tag-editor [onnxruntime-gpu]",
                    )
                elif dev == "directml":
                    launch.run_pip(
                        "install -U onnxruntime-directml",
                        "requirements for dataset-tag-editor [onnxruntime-directml]",
                    )
                else:
                    print(
                        "Your device is not compatible with onnx hardware acceleration. CPU only version will be installed and it may be very slow."
                    )
                    launch.run_pip(
                        "install -U onnxruntime",
                        "requirements for dataset-tag-editor [onnxruntime for CPU]",
                    )
            import onnxruntime as ort

            self.model = ort.InferenceSession(path_model, providers=providers)

        path_label = huggingface_hub.hf_hub_download(
            self.MODEL_REPO, self.LABEL_FILENAME
        )
        import pandas as pd

        self.labels = pd.read_csv(path_label)["name"].tolist()

    def unload(self):
        if not shared.opts.interrogate_keep_models_in_memory:
            self.model = None
            devices.torch_gc()

    # brought from https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py and modified
    def apply(self, image: Image.Image):
        if not self.model:
            return dict()

        from modules import images

        _, height, width, _ = self.model.get_inputs()[0].shape

        # the way to fill empty pixels is quite different from original one;
        # original: fill by white pixels
        # this: repeat the pixels on the edge
        image = images.resize_image(2, image.convert("RGB"), width, height)
        image_np = np.array(image, dtype=np.float32)
        # PIL RGB to OpenCV BGR
        image_np = image_np[:, :, ::-1]
        image_np = np.expand_dims(image_np, 0)

        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        probs = self.model.run([label_name], {input_name: image_np})[0]
        labels: List[Tuple[str, float]] = list(zip(self.labels, probs[0].astype(float)))

        return labels
