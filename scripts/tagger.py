import re
from typing import Optional, Generator, Any

from PIL import Image

from modules import shared, lowvram, devices
from modules import deepbooru as db

# Custom tagger classes have to inherit from this class
class Tagger:
    def __enter__(self):
        lowvram.send_everything_to_cpu()
        devices.torch_gc()
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()
        pass

    def start(self):
        pass

    def stop(self):
        pass

    # predict tags of one image
    def predict(self, image: Image.Image, threshold: Optional[float] = None) -> list[str]:
        raise NotImplementedError()
    
    # Please implement if you want to use more efficient data loading system
    # None input will come to check if this function is implemented
    def predict_pipe(self, data: list[Image.Image], threshold: Optional[float] = None) -> Generator[list[str], Any, None]:
        raise NotImplementedError()

    # Visible name in UI
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


def get_arranged_tags(probs: dict[str, float]):
    return [tag for tag, _ in sorted(probs.items(), key=lambda x: -x[1])]
