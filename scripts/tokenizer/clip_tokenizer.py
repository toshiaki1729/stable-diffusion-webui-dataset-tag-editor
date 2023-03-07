# Brought from AUTOMATIC1111's stable-diffusion-webui-tokenizer and modified
# https://github.com/AUTOMATIC1111/stable-diffusion-webui-tokenizer/blob/master/scripts/tokenizer.py

from typing import List
from functools import reduce
from ldm.modules.encoders.modules import FrozenCLIPEmbedder, FrozenOpenCLIPEmbedder
from modules import shared, extra_networks, prompt_parser
from modules.sd_hijack import model_hijack
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

def tokenize(text:str, use_raw_clip:bool=True):
    if use_raw_clip:
        tokens = shared.sd_model.cond_stage_model.tokenize([text])[0]
        token_count = len(tokens)
    else:
        try:
            text, _ = extra_networks.parse_prompt(text)
            _, prompt_flat_list, _ = prompt_parser.get_multicond_prompt_list([text])
            prompt = reduce(lambda list1, list2: list1+list2, prompt_flat_list)
        except Exception:
            prompt = text
        token_chunks, token_count = model_hijack.clip.tokenize_line(prompt)
        tokens = reduce(lambda list1, list2: list1+list2, [tc.tokens for tc in token_chunks])
    return tokens, token_count

def get_target_token_count(token_count:int):
    return model_hijack.clip.get_target_prompt_token_count(token_count)