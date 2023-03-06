# Brought from AUTOMATIC1111's stable-diffusion-webui-tokenizer and modified
# https://github.com/AUTOMATIC1111/stable-diffusion-webui-tokenizer/blob/master/scripts/tokenizer.py

from ldm.modules.encoders.modules import FrozenCLIPEmbedder, FrozenOpenCLIPEmbedder
from modules import shared
import open_clip.tokenizer

class VanillaClip:
    def __init__(self, clip):
        self.clip = clip

    def vocab(self):
        return self.clip.tokenizer.get_vocab()

    def byte_decoder(self):
        return self.clip.tokenizer.byte_decoder

class OpenClip:
    def __init__(self, clip):
        self.clip = clip
        self.tokenizer = open_clip.tokenizer._tokenizer

    def vocab(self):
        return self.tokenizer.encoder

    def byte_decoder(self):
        return self.tokenizer.byte_decoder

def tokenize(text:str):
    clip = shared.sd_model.cond_stage_model.wrapped
    if isinstance(clip, FrozenCLIPEmbedder):
        clip = VanillaClip(shared.sd_model.cond_stage_model.wrapped)
    elif isinstance(clip, FrozenOpenCLIPEmbedder):
        clip = OpenClip(shared.sd_model.cond_stage_model.wrapped)
    else:
        raise RuntimeError(f'Unknown CLIP model: {type(clip).__name__}')

    tokens = shared.sd_model.cond_stage_model.tokenize([text])[0]
    return tokens

def token_count(text:str):
    return len(tokenize(text))
