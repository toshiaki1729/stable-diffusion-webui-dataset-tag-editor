from __future__ import annotations
from typing import TYPE_CHECKING
import gradio as gr

from .ui_common import *
from .uibase import UIBase

if TYPE_CHECKING:
    from .ui_classes import *


class ToprowUI(UIBase):
    def create_ui(self, cfg_general):
        with gr.Column(variant='panel'):
            with gr.Row():
                with gr.Column(scale=1):
                    self.btn_save_all_changes = gr.Button(value='Save all changes', variant='primary')
                with gr.Column(scale=2):
                    self.cb_backup = gr.Checkbox(value=cfg_general.backup, label='Backup original text file (original file will be renamed like filename.000, .001, .002, ...)', interactive=True)
            gr.HTML(value='<b>Note:</b> New text file will be created if you are using filename as captions.')
            with gr.Row():
                self.cb_save_kohya_metadata = gr.Checkbox(value=cfg_general.save_kohya_metadata, label="Use kohya-ss's finetuning metadata json", interactive=True)
            with gr.Row():
                with gr.Column(variant='panel', visible=cfg_general.save_kohya_metadata) as self.cl_kohya_metadata:
                    self.tb_metadata_output = gr.Textbox(label='json path', placeholder='C:\\path\\to\\metadata.json',value=cfg_general.meta_output_path)
                    self.tb_metadata_input = gr.Textbox(label='json input path (Optional, only for append results)', placeholder='C:\\path\\to\\metadata.json',value=cfg_general.meta_input_path)
                    with gr.Row():
                        self.cb_metadata_overwrite = gr.Checkbox(value=cfg_general.meta_overwrite, label="Overwrite if output file exists", interactive=True)
                        self.cb_metadata_as_caption = gr.Checkbox(value=cfg_general.meta_save_as_caption, label="Save metadata as caption", interactive=True)
                        self.cb_metadata_use_fullpath = gr.Checkbox(value=cfg_general.meta_use_full_path, label="Save metadata image key as fullpath", interactive=True)
            with gr.Row(visible=False):
                self.txt_result = gr.Textbox(label='Results', interactive=False)
    
    def set_callbacks(self, load_dataset:LoadDatasetUI):
        
        def save_all_changes(backup: bool, save_kohya_metadata:bool, metadata_output:str, metadata_input:str, metadata_overwrite:bool, metadata_as_caption:bool, metadata_use_fullpath:bool, caption_file_ext:str):
            if not metadata_input:
                metadata_input = None
            dte_instance.save_dataset(backup, caption_file_ext, save_kohya_metadata, metadata_output, metadata_input, metadata_overwrite, metadata_as_caption, metadata_use_fullpath)

        self.btn_save_all_changes.click(
            fn=save_all_changes,
            inputs=[self.cb_backup, self.cb_save_kohya_metadata, self.tb_metadata_output, self.tb_metadata_input, self.cb_metadata_overwrite, self.cb_metadata_as_caption, self.cb_metadata_use_fullpath, load_dataset.tb_caption_file_ext]
        )

        self.cb_save_kohya_metadata.change(
            fn=lambda x:gr.update(visible=x),
            inputs=self.cb_save_kohya_metadata,
            outputs=self.cl_kohya_metadata
        )

