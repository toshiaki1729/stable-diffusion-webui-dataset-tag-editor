from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable
import gradio as gr

from modules import shared
from modules.call_queue import wrap_queued_call
from scripts.dte_instance import dte_module

from .ui_common import *
from .uibase import UIBase
from scripts.tokenizer import clip_tokenizer

if TYPE_CHECKING:
    from .ui_classes import *

SortBy = dte_instance.SortBy
SortOrder = dte_instance.SortOrder

class EditCaptionOfSelectedImageUI(UIBase):
    def __init__(self):
        self.change_is_saved = True
    
    def create_ui(self, cfg_edit_selected):
        with gr.Row(visible=False):
            self.nb_hidden_image_index_save_or_not = gr.Number(value=-1, label='hidden_s_or_n')
            self.tb_hidden_edit_caption = gr.Textbox()
            self.btn_hidden_save_caption = gr.Button(elem_id="dataset_tag_editor_btn_hidden_save_caption")
        with gr.Tab(label='Read Caption from Selected Image'):
            self.tb_caption = gr.Textbox(label='Caption of Selected Image', interactive=False, lines=6, elem_id='dte_caption')
            self.token_counter_caption = gr.HTML(value='<span>0/75</span>', elem_id='dte_caption_counter', elem_classes=["token-counter-dte"])
            with gr.Row():
                self.btn_copy_caption = gr.Button(value='Copy and Overwrite')
                self.btn_prepend_caption = gr.Button(value='Prepend')
                self.btn_append_caption = gr.Button(value='Append')
            
        with gr.Tab(label='Interrogate Selected Image'):
            with gr.Row():
                self.dd_intterogator_names_si = gr.Dropdown(label = 'Interrogator', choices=dte_instance.INTERROGATOR_NAMES, value=cfg_edit_selected.use_interrogator_name, interactive=True, multiselect=False)
                self.btn_interrogate_si = gr.Button(value='Interrogate')
            with gr.Column():
                self.tb_interrogate = gr.Textbox(label='Interrogate Result', interactive=True, lines=6, elem_id='dte_interrogate')
                self.token_counter_interrogate = gr.HTML(value='<span></span>', elem_id='dte_interrogate_counter')
            with gr.Row():
                self.btn_copy_interrogate = gr.Button(value='Copy and Overwrite')
                self.btn_prepend_interrogate = gr.Button(value='Prepend')
                self.btn_append_interrogate = gr.Button(value='Append')
        with gr.Column():
            self.cb_copy_caption_automatically = gr.Checkbox(value=cfg_edit_selected.auto_copy, label='Copy caption from selected images automatically')
            self.cb_sort_caption_on_save = gr.Checkbox(value=cfg_edit_selected.sort_on_save, label='Sort caption on save')
            with gr.Row(visible=cfg_edit_selected.sort_on_save) as self.sort_settings:
                self.rb_sort_by = gr.Radio(choices=[e.value for e in SortBy], value=cfg_edit_selected.sort_by, interactive=True, label='Sort by')
                self.rb_sort_order = gr.Radio(choices=[e.value for e in SortOrder], value=cfg_edit_selected.sort_order, interactive=True, label='Sort Order')
            self.cb_ask_save_when_caption_changed = gr.Checkbox(value=cfg_edit_selected.warn_change_not_saved, label='Warn if changes in caption is not saved')
        with gr.Column():
            self.tb_edit_caption = gr.Textbox(label='Edit Caption', interactive=True, lines=6, elem_id= 'dte_edit_caption')
            self.token_counter_edit_caption = gr.HTML(value='<span>0/75</span>', elem_id='dte_edit_caption_counter', elem_classes=["token-counter-dte"])
        self.btn_apply_changes_selected_image = gr.Button(value='Apply changes to selected image', variant='primary')
        self.btn_apply_changes_all_images = gr.Button(value='Apply changes to ALL displayed images', variant='primary')

        gr.HTML("""Changes are not applied to the text files until the "Save all changes" button is pressed.""")
    
    def set_callbacks(self, o_update_filter_and_gallery:List[gr.components.Component], dataset_gallery:DatasetGalleryUI, load_dataset:LoadDatasetUI, get_filters:Callable[[], List[dte_module.filters.Filter]], update_filter_and_gallery:Callable[[], List]):
        load_dataset.btn_load_datasets.click(
            fn=lambda:['', -1],
            outputs=[self.tb_caption, self.nb_hidden_image_index_save_or_not]
        )

        def gallery_index_changed(next_idx:int, prev_idx:int, edit_caption: str, copy_automatically: bool, warn_change_not_saved: bool):
            next_idx = int(next_idx) if next_idx is not None else -1
            prev_idx = int(prev_idx) if prev_idx is not None else -1
            img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())
            prev_tags_txt = ''
            if 0 <= prev_idx and prev_idx < len(img_paths):
                prev_tags_txt = ', '.join(dte_instance.get_tags_by_image_path(img_paths[prev_idx]))
            else:
                prev_idx = -1
            
            next_tags_txt = ''
            if 0 <= next_idx and next_idx < len(img_paths):
                next_tags_txt = ', '.join(dte_instance.get_tags_by_image_path(img_paths[next_idx]))
                
            return\
                [prev_idx if warn_change_not_saved and edit_caption != prev_tags_txt and not self.change_is_saved else -1] +\
                [next_tags_txt, next_tags_txt if copy_automatically else edit_caption] +\
                [edit_caption]

        self.nb_hidden_image_index_save_or_not.change(
            fn=lambda a:None,
            _js='(a) => dataset_tag_editor_ask_save_change_or_not(a)',
            inputs=self.nb_hidden_image_index_save_or_not
        )
        dataset_gallery.nb_hidden_image_index.change(lambda:None).then(
            fn=gallery_index_changed,
            inputs=[dataset_gallery.nb_hidden_image_index, dataset_gallery.nb_hidden_image_index_prev, self.tb_edit_caption, self.cb_copy_caption_automatically, self.cb_ask_save_when_caption_changed],
            outputs=[self.nb_hidden_image_index_save_or_not] + [self.tb_caption, self.tb_edit_caption] + [self.tb_hidden_edit_caption]
        )

        def change_selected_image_caption(tags_text: str, idx:int, sort: bool, sort_by:str, sort_order:str):
            idx = int(idx)
            img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())

            edited_tags = [t.strip() for t in tags_text.split(',')]
            edited_tags = [t for t in edited_tags if t]

            if sort:
                edited_tags = dte_instance.sort_tags(edited_tags, SortBy(sort_by), SortOrder(sort_order))

            if 0 <= idx and idx < len(img_paths):
                dte_instance.set_tags_by_image_path(imgpath=img_paths[idx], tags=edited_tags)
            return update_filter_and_gallery()
        
        self.btn_hidden_save_caption.click(
            fn=change_selected_image_caption,
            inputs=[self.tb_hidden_edit_caption, self.nb_hidden_image_index_save_or_not, self.cb_sort_caption_on_save, self.rb_sort_by, self.rb_sort_order],
            outputs=o_update_filter_and_gallery
        )

        self.btn_copy_caption.click(
            fn=lambda a:a,
            inputs=[self.tb_caption],
            outputs=[self.tb_edit_caption]
        )

        self.btn_append_caption.click(
            fn=lambda a, b : b + (', ' if a and b else '') + a,
            inputs=[self.tb_caption, self.tb_edit_caption],
            outputs=[self.tb_edit_caption]
        )

        self.btn_prepend_caption.click(
            fn=lambda a, b : a + (', ' if a and b else '') + b,
            inputs=[self.tb_caption, self.tb_edit_caption],
            outputs=[self.tb_edit_caption]
        )

        def interrogate_selected_image(interrogator_name: str, use_threshold_booru: bool, threshold_booru: float, use_threshold_waifu: bool, threshold_waifu: float, threshold_z3d: float):
            
            if not interrogator_name:
                return ''
            threshold_booru = threshold_booru if use_threshold_booru else shared.opts.interrogate_deepbooru_score_threshold
            threshold_waifu = threshold_waifu if use_threshold_waifu else -1
            return dte_instance.interrogate_image(dataset_gallery.selected_path, interrogator_name, threshold_booru, threshold_waifu, threshold_z3d)

        self.btn_interrogate_si.click(
            fn=interrogate_selected_image,
            inputs=[self.dd_intterogator_names_si, load_dataset.cb_use_custom_threshold_booru, load_dataset.sl_custom_threshold_booru, load_dataset.cb_use_custom_threshold_waifu, load_dataset.sl_custom_threshold_waifu, load_dataset.sl_custom_threshold_z3d],
            outputs=[self.tb_interrogate]
        )

        self.btn_copy_interrogate.click(
            fn=lambda a:a,
            inputs=[self.tb_interrogate],
            outputs=[self.tb_edit_caption]
        )

        self.btn_append_interrogate.click(
            fn=lambda a, b : b + (', ' if a and b else '') + a,
            inputs=[self.tb_interrogate, self.tb_edit_caption],
            outputs=[self.tb_edit_caption]
        )
        
        self.btn_prepend_interrogate.click(
            fn=lambda a, b : a + (', ' if a and b else '') + b,
            inputs=[self.tb_interrogate, self.tb_edit_caption],
            outputs=[self.tb_edit_caption]
        )

        def change_in_caption():
            self.change_is_saved = False

        self.tb_edit_caption.change(
            fn=change_in_caption
        )

        self.tb_caption.change(
            fn=change_in_caption
        )

        def apply_changes(edited:str, sort:bool, sort_by:str, sort_order:str):
            self.change_is_saved = True
            return change_selected_image_caption(edited, dataset_gallery.selected_index, sort, sort_by, sort_order)

        self.btn_apply_changes_selected_image.click(
            fn=apply_changes,
            inputs=[self.tb_edit_caption, self.cb_sort_caption_on_save, self.rb_sort_by, self.rb_sort_order],
            outputs=o_update_filter_and_gallery,
            _js='(a,b,c,d) => {dataset_tag_editor_gl_dataset_images_close(); return [a, b, c, d]}'
        )

        def apply_chages_all(tags_text: str, sort: bool, sort_by:str, sort_order:str):
            self.change_is_saved = True
            img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())

            edited_tags = [t.strip() for t in tags_text.split(',')]
            edited_tags = [t for t in edited_tags if t]

            if sort:
                edited_tags = dte_instance.sort_tags(edited_tags, SortBy(sort_by), SortOrder(sort_order))

            for img_path in img_paths:
                dte_instance.set_tags_by_image_path(imgpath=img_path, tags=edited_tags)
            return update_filter_and_gallery()

        self.btn_apply_changes_all_images.click(
            fn=apply_chages_all,
            inputs=[self.tb_edit_caption, self.cb_sort_caption_on_save, self.rb_sort_by, self.rb_sort_order],
            outputs=o_update_filter_and_gallery,
            _js='(a,b,c,d) => {dataset_tag_editor_gl_dataset_images_close(); return [a, b, c, d]}'
        )

        self.cb_sort_caption_on_save.change(
            fn=lambda x:gr.update(visible=x),
            inputs=self.cb_sort_caption_on_save,
            outputs=self.sort_settings
        )

        def update_token_counter(text:str):
            _, token_count = clip_tokenizer.tokenize(text, shared.opts.dataset_editor_use_raw_clip_token)
            max_length = clip_tokenizer.get_target_token_count(token_count)
            return f"<span class='gr-box gr-text-input'>{token_count}/{max_length}</span>"

        update_caption_token_counter_args = {
            'fn' : wrap_queued_call(update_token_counter),
            'inputs' : [self.tb_caption],
            'outputs' : [self.token_counter_caption]
        }
        update_edit_caption_token_counter_args = {
            'fn' : wrap_queued_call(update_token_counter),
            'inputs' : [self.tb_edit_caption],
            'outputs' : [self.token_counter_edit_caption]
        }
        update_interrogate_token_counter_args = {
            'fn' : wrap_queued_call(update_token_counter),
            'inputs' : [self.tb_interrogate],
            'outputs' : [self.token_counter_interrogate]
        }

        self.tb_caption.change(**update_caption_token_counter_args)
        self.tb_edit_caption.change(**update_edit_caption_token_counter_args)
        self.tb_interrogate.change(**update_interrogate_token_counter_args)
