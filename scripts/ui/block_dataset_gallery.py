import gradio as gr

from .ui_common import *
from .uibase import UIBase

class DatasetGalleryUI(UIBase):
    def __init__(self):
        self.selected_path = ''
        self.selected_index = -1
        self.selected_index_prev = -1

    def create_ui(self, image_columns):
        with gr.Row(visible=False):
            self.btn_hidden_set_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_index")
            self.nb_hidden_image_index = gr.Number(value=None, label='hidden_idx_next')
            self.nb_hidden_image_index_prev = gr.Number(value=None, label='hidden_idx_prev')
        self.gl_dataset_images = gr.Gallery(label='Dataset Images', elem_id="dataset_tag_editor_dataset_gallery").style(grid=image_columns)
    
    def set_callbacks(self, load_dataset, gallery_state, get_filters):
        gallery_state.register_value('Selected Image', self.selected_path)

        load_dataset.btn_load_datasets.click(
            fn=lambda:[-1, -1],
            outputs=[self.nb_hidden_image_index, self.nb_hidden_image_index_prev]
        )

        def set_index_clicked(next_idx: int, prev_idx: int):
            prev_idx = int(prev_idx) if prev_idx is not None else -1
            next_idx = int(next_idx) if next_idx is not None else -1
            img_paths = dte_instance.get_filtered_imgpaths(filters=get_filters())
            
            if prev_idx < 0 or len(img_paths) <= prev_idx:
                prev_idx = -1

            if 0 <= next_idx and next_idx < len(img_paths):
                self.selected_path = img_paths[next_idx]
            else:
                next_idx = -1
                self.selected_path = ''

            gallery_state.register_value('Selected Image', self.selected_path)
            return [next_idx, prev_idx]
        
        self.btn_hidden_set_index.click(
            fn=set_index_clicked,
            _js="(x, y) => [dataset_tag_editor_gl_dataset_images_selected_index(), x]",
            inputs=[self.nb_hidden_image_index, self.nb_hidden_image_index_prev],
            outputs=[self.nb_hidden_image_index, self.nb_hidden_image_index_prev]
        )
        self.nb_hidden_image_index.change(
            fn=self.func_to_set_value('selected_index', int),
            inputs=self.nb_hidden_image_index
        )
        self.nb_hidden_image_index_prev.change(
            fn=self.func_to_set_value('selected_index_prev', int),
            inputs=self.nb_hidden_image_index_prev
        )
    


