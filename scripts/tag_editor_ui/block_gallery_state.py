from __future__ import annotations
from typing import TYPE_CHECKING
import gradio as gr

from .ui_common import *
from .uibase import UIBase

if TYPE_CHECKING:
    from .ui_classes import *

class GalleryStateUI(UIBase):
    def __init__(self):
        self.texts = dict()
    
    def register_value(self, key:str, value:str):
        self.texts[key] = value

    def remove_key(self, key:str):
        del self.texts[key]

    def get_current_gallery_txt(self):
        res = ''
        for k, v in self.texts.items():
            res += f'{k} : {v} <br>'
        return res
    
    def create_ui(self):
        self.txt_gallery = gr.HTML(value=self.get_current_gallery_txt())

    def set_callbacks(self, dataset_gallery:DatasetGalleryUI):
        dataset_gallery.nb_hidden_image_index.change(fn=lambda:None).then(
            fn=self.update_gallery_txt,
            inputs=None,
            outputs=self.txt_gallery
        )
    
    def update_gallery_txt(self):
        return self.get_current_gallery_txt()


