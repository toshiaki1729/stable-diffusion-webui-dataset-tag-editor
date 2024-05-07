from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable
import gradio as gr

from .ui_common import *
from .uibase import UIBase

if TYPE_CHECKING:
    from .ui_classes import *

filters = dte_module.filters


class FilterBySelectionUI(UIBase):
    def __init__(self):
        self.path_filter = filters.PathFilter()
        self.selected_index = -1
        self.selected_path = ''
        self.tmp_selection = set()
        
    def get_current_txt_selection(self):
        return f"""Selected Image : {self.selected_path}"""

    def create_ui(self, image_columns:int):
        with gr.Row(visible=False):
            self.btn_hidden_set_selection_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_selection_index")
            self.nb_hidden_selection_image_index = gr.Number(value=-1)
        gr.HTML("""Select images from the left gallery.""")
        
        with gr.Column(variant='panel'):
            with gr.Row():
                self.btn_add_image_selection = gr.Button(value='Add selection [Enter]', elem_id='dataset_tag_editor_btn_add_image_selection')    
                self.btn_add_all_displayed_image_selection = gr.Button(value='Add ALL Displayed')    

            self.gl_filter_images = gr.Gallery(label='Filter Images', elem_id="dataset_tag_editor_filter_gallery", columns=image_columns)
            self.txt_selection = gr.HTML(value=self.get_current_txt_selection())

            with gr.Row():
                self.btn_remove_image_selection = gr.Button(value='Remove selection [Delete]', elem_id='dataset_tag_editor_btn_remove_image_selection')
                self.btn_invert_image_selection = gr.Button(value='Invert selection')
                self.btn_clear_image_selection = gr.Button(value='Clear selection')

        self.btn_apply_image_selection_filter = gr.Button(value='Apply selection filter', variant='primary')

    def set_callbacks(self, o_update_filter_and_gallery:List[gr.components.Component], dataset_gallery:DatasetGalleryUI, filter_by_tags:FilterByTagsUI, get_filters:Callable[[], List[dte_module.filters.Filter]], update_filter_and_gallery:Callable[[], List]):
        def selection_index_changed(idx:int = -1):
            idx = int(idx) if idx is not None else -1
            img_paths = arrange_selection_order(self.tmp_selection)
            if idx < 0 or len(img_paths) <= idx:
                self.selected_path = ''
                idx = -1
            else:
                self.selected_path = img_paths[idx]
            self.selected_index = idx
            return [self.get_current_txt_selection(), idx]
        
        self.btn_hidden_set_selection_index.click(
            fn=selection_index_changed,
            _js="(x) => dataset_tag_editor_gl_filter_images_selected_index()",
            inputs=[self.nb_hidden_selection_image_index],
            outputs=[self.txt_selection, self.nb_hidden_selection_image_index]
        )

        def add_image_selection():
            img_path = dataset_gallery.selected_path
            if img_path:
                self.tmp_selection.add(img_path)
            return [dte_instance.images[p] for p in arrange_selection_order(self.tmp_selection)]

        self.btn_add_image_selection.click(
            fn=add_image_selection,
            outputs=[self.gl_filter_images]
        )

        def add_all_displayed_image_selection():
            img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())
            self.tmp_selection |= set(img_paths)
            return [dte_instance.images[p] for p in arrange_selection_order(self.tmp_selection)]
        
        self.btn_add_all_displayed_image_selection.click(
            fn=add_all_displayed_image_selection,
            outputs=self.gl_filter_images
        )

        def invert_image_selection():
            img_paths = dte_instance.get_img_path_set()
            self.tmp_selection = img_paths - self.tmp_selection
            return [dte_instance.images[p] for p in arrange_selection_order(self.tmp_selection)]

        self.btn_invert_image_selection.click(
            fn=invert_image_selection,
            outputs=self.gl_filter_images
        )

        def remove_image_selection():
            img_path = self.selected_path
            if img_path:
                self.tmp_selection.remove(img_path)
                self.selected_path = ''
                self.selected_index = -1

            return [
                [dte_instance.images[p] for p in arrange_selection_order(self.tmp_selection)],
                self.get_current_txt_selection(),
                -1
            ]

        self.btn_remove_image_selection.click(
            fn=remove_image_selection,
            outputs=[self.gl_filter_images, self.txt_selection, self.nb_hidden_selection_image_index]
        )

        def clear_image_selection():
            self.tmp_selection.clear()
            self.selected_path = ''
            self.selected_index = -1
            return[
                [],
                self.get_current_txt_selection(),
                -1
            ]

        self.btn_clear_image_selection.click(
            fn=clear_image_selection,
            outputs=
            [self.gl_filter_images, self.txt_selection, self.nb_hidden_selection_image_index]
        )
        
        def clear_image_filter():
            self.path_filter = filters.PathFilter()
            return clear_image_selection() + update_filter_and_gallery()

        filter_by_tags.btn_clear_all_filters.click(lambda:None).then(
            fn=clear_image_filter,
            outputs=
            [self.gl_filter_images, self.txt_selection, self.nb_hidden_selection_image_index] +
            o_update_filter_and_gallery
        )

        def apply_image_selection_filter():
            if len(self.tmp_selection) > 0:
                self.path_filter = filters.PathFilter(self.tmp_selection, filters.PathFilter.Mode.INCLUSIVE)
            else:
                self.path_filter = filters.PathFilter()
            return update_filter_and_gallery()
        
        self.btn_apply_image_selection_filter.click(
            fn=apply_image_selection_filter,
            outputs=o_update_filter_and_gallery
        ).then(
            fn=None,
            _js='() => dataset_tag_editor_gl_dataset_images_close()'
        )


def arrange_selection_order(paths: List[str]):
    return sorted(paths)

    