from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable

import gradio as gr

from .ui_common import *
from .uibase import UIBase

if TYPE_CHECKING:
    from .ui_classes import *


class MoveOrDeleteFilesUI(UIBase):
    def __init__(self):
        self.target_data = 'Selected One'
        self.current_target_txt = ''

    def create_ui(self, cfg_file_move_delete):
        gr.HTML(value='<b>Note: </b>Moved or deleted images will be unloaded.')
        self.target_data = cfg_file_move_delete.range
        self.rb_move_or_delete_target_data = gr.Radio(choices=['Selected One', 'All Displayed Ones'], value=cfg_file_move_delete.range, label='Move or Delete')
        self.cbg_move_or_delete_target_file = gr.CheckboxGroup(choices=['Image File', 'Caption Text File', 'Caption Backup File'], label='Target', value=cfg_file_move_delete.target)
        self.tb_move_or_delete_caption_ext = gr.Textbox(label='Caption File Ext', placeholder='txt', value=cfg_file_move_delete.caption_ext)
        self.ta_move_or_delete_target_dataset_num = gr.HTML(value='Target dataset num: 0')
        self.tb_move_or_delete_destination_dir = gr.Textbox(label='Destination Directory', value=cfg_file_move_delete.destination)
        self.btn_move_or_delete_move_files = gr.Button(value='Move File(s)', variant='primary')
        gr.HTML(value='<b>Note: </b>DELETE cannot be undone. The files will be deleted completely.')
        self.btn_move_or_delete_delete_files = gr.Button(value='DELETE File(s)', variant='primary')
    
    def get_current_move_or_delete_target_num(self):
        return self.current_target_txt

    def set_callbacks(self, o_update_filter_and_gallery:List[gr.components.Component], dataset_gallery:DatasetGalleryUI, filter_by_tags:FilterByTagsUI, batch_edit_captions:BatchEditCaptionsUI, filter_by_selection:FilterBySelectionUI, edit_caption_of_selected_image:EditCaptionOfSelectedImageUI, get_filters:Callable[[], List[dte_module.filters.Filter]], update_filter_and_gallery:Callable[[], List]):
        def _get_current_move_or_delete_target_num():
            if self.target_data == 'Selected One':
                self.current_target_txt = f'Target dataset num: {1 if dataset_gallery.selected_index != -1 else 0}'
            elif self.target_data == 'All Displayed Ones':
                img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())
                self.current_target_txt = f'Target dataset num: {len(img_paths)}'
            else:
                self.current_target_txt =  f'Target dataset num: 0'
            return self.current_target_txt
        
        update_args = {
            'fn' : _get_current_move_or_delete_target_num,
            'inputs' : None,
            'outputs' : [self.ta_move_or_delete_target_dataset_num]
        }

        batch_edit_captions.btn_apply_edit_tags.click(**update_args)

        batch_edit_captions.btn_apply_sr_tags.click(**update_args)

        filter_by_selection.btn_apply_image_selection_filter.click(**update_args)

        filter_by_tags.btn_clear_tag_filters.click(**update_args)

        filter_by_tags.btn_clear_all_filters.click(**update_args)
        
        edit_caption_of_selected_image.btn_apply_changes_selected_image.click(**update_args)

        self.rb_move_or_delete_target_data.change(**update_args)

        def move_files(
                target_data: str,
                target_file, #: List[str], : to avoid error on gradio v3.23.0
                caption_ext: str,
                dest_dir: str):
            move_img = 'Image File' in target_file
            move_txt = 'Caption Text File' in target_file
            move_bak = 'Caption Backup File' in target_file
            if target_data == 'Selected One':
                img_path = dataset_gallery.selected_path
                if img_path:
                    dte_instance.move_dataset_file(img_path, caption_ext, dest_dir, move_img, move_txt, move_bak)
                    dte_instance.construct_tag_infos()
                
            elif target_data == 'All Displayed Ones':
                dte_instance.move_dataset(dest_dir, caption_ext, get_filters(), move_img, move_txt, move_bak)

            return update_filter_and_gallery()

        self.btn_move_or_delete_move_files.click(
            fn=move_files,
            inputs=[self.rb_move_or_delete_target_data, self.cbg_move_or_delete_target_file, self.tb_move_or_delete_caption_ext, self.tb_move_or_delete_destination_dir],
            outputs=o_update_filter_and_gallery
        )
        self.btn_move_or_delete_move_files.click(**update_args)
        self.btn_move_or_delete_move_files.click(
            fn=None,
            _js='() => dataset_tag_editor_gl_dataset_images_close()'
        )

        def delete_files(
                target_data: str,
                target_file, #: List[str], : to avoid error on gradio v3.23.0
                caption_ext: str):
            delete_img = 'Image File' in target_file
            delete_txt = 'Caption Text File' in target_file
            delete_bak = 'Caption Backup File' in target_file
            if target_data == 'Selected One':
                img_path = dataset_gallery.selected_path
                if img_path:
                    dte_instance.delete_dataset_file(img_path, delete_img, caption_ext, delete_txt, delete_bak)
                    dte_instance.construct_tag_infos()
            
            elif target_data == 'All Displayed Ones':
                dte_instance.delete_dataset(caption_ext, get_filters(), delete_img, delete_txt, delete_bak)

            return update_filter_and_gallery()

        self.btn_move_or_delete_delete_files.click(
            fn=delete_files,
            inputs=[self.rb_move_or_delete_target_data, self.cbg_move_or_delete_target_file, self.tb_move_or_delete_caption_ext],
            outputs=o_update_filter_and_gallery
        )
        self.btn_move_or_delete_delete_files.click(**update_args)
        self.btn_move_or_delete_delete_files.click(
            fn=None,
            _js='() => dataset_tag_editor_gl_dataset_images_close()'
        )
        