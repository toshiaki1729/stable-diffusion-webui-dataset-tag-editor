from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable
import gradio as gr

from .ui_common import *
from .uibase import UIBase
from .block_tag_filter import TagFilterUI

if TYPE_CHECKING:
    from .ui_classes import *

filters = dte_module.filters

class FilterByTagsUI(UIBase):
    def __init__(self):        
        self.tag_filter_ui = TagFilterUI(tag_filter_mode=filters.TagFilter.Mode.INCLUSIVE)
        self.tag_filter_ui_neg = TagFilterUI(tag_filter_mode=filters.TagFilter.Mode.EXCLUSIVE)

    def create_ui(self, cfg_filter_p, cfg_filter_n, get_filters):
        with gr.Row():
            self.btn_clear_tag_filters = gr.Button(value='Clear tag filters')
            self.btn_clear_all_filters = gr.Button(value='Clear ALL filters')

        with gr.Tab(label='Positive Filter'):
            with gr.Column(variant='panel'):
                gr.HTML(value='Search tags / Filter images by tags <b>(INCLUSIVE)</b>')
                logic_p = filters.TagFilter.Logic.OR if cfg_filter_p.logic=='OR' else filters.TagFilter.Logic.NONE if cfg_filter_p.logic=='NONE' else filters.TagFilter.Logic.AND
                self.tag_filter_ui.create_ui(get_filters, logic_p, cfg_filter_p.sort_by, cfg_filter_p.sort_order, cfg_filter_p.sw_prefix, cfg_filter_p.sw_suffix, cfg_filter_p.sw_regex)

        with gr.Tab(label='Negative Filter'):
            with gr.Column(variant='panel'):
                gr.HTML(value='Search tags / Filter images by tags <b>(EXCLUSIVE)</b>')
                logic_n = filters.TagFilter.Logic.AND if cfg_filter_n.logic=='AND' else filters.TagFilter.Logic.NONE if cfg_filter_n.logic=='NONE' else filters.TagFilter.Logic.OR
                self.tag_filter_ui_neg.create_ui(get_filters, logic_n, cfg_filter_n.sort_by, cfg_filter_n.sort_order, cfg_filter_n.sw_prefix, cfg_filter_n.sw_suffix, cfg_filter_n.sw_regex)
    
    def set_callbacks(self, o_update_gallery:List[gr.components.Component], o_update_filter_and_gallery:List[gr.components.Component], batch_edit_captions:BatchEditCaptionsUI, move_or_delete_files:MoveOrDeleteFilesUI, update_gallery:Callable[[], List], update_filter_and_gallery:Callable[[], List], get_filters:Callable[[], List[dte_module.filters.Filter]]):
        common_callback = lambda : \
            update_gallery() + \
            batch_edit_captions.get_common_tags(get_filters, self) + \
            [move_or_delete_files.update_current_move_or_delete_target_num()] + \
            [batch_edit_captions.tag_select_ui_remove.cbg_tags_update()]
        
        common_callback_output = \
            o_update_gallery + \
            [batch_edit_captions.tb_common_tags, batch_edit_captions.tb_edit_tags] + \
            [move_or_delete_files.ta_move_or_delete_target_dataset_num]+ \
            [batch_edit_captions.tag_select_ui_remove.cbg_tags]
        

        self.tag_filter_ui.on_filter_update(
            fn=lambda :
            common_callback() +
            [', '.join(self.tag_filter_ui.filter.tags)],
            inputs=None,
            outputs=common_callback_output + [batch_edit_captions.tb_sr_selected_tags],
            _js='(...args) => {dataset_tag_editor_gl_dataset_images_close(); return args}'
        )

        self.tag_filter_ui_neg.on_filter_update(
            fn=common_callback,
            inputs=None,
            outputs=common_callback_output,
            _js='(...args) => {dataset_tag_editor_gl_dataset_images_close(); return args}'
        )

        self.tag_filter_ui.set_callbacks()
        self.tag_filter_ui_neg.set_callbacks()

        self.btn_clear_tag_filters.click(
            fn=lambda:self.clear_filters(update_filter_and_gallery),
            outputs=o_update_filter_and_gallery
        )
        
        self.btn_clear_all_filters.click(
            fn=lambda:self.clear_filters(update_filter_and_gallery),
            outputs=o_update_filter_and_gallery
        )

    def clear_filters(self, update_filter_and_gallery):
        self.tag_filter_ui.clear_filter()
        self.tag_filter_ui_neg.clear_filter()
        return update_filter_and_gallery()
