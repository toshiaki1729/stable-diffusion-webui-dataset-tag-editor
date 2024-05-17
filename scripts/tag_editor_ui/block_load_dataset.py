from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable
import gradio as gr

from modules import shared
from modules.shared import opts

from .ui_common import *
from .uibase import UIBase

if TYPE_CHECKING:
    from .ui_classes import *


class LoadDatasetUI(UIBase):
    def __init__(self):
        self.caption_file_ext = ""

    def create_ui(self, cfg_general):
        with gr.Column(variant="panel"):
            with gr.Row():
                with gr.Column(scale=3):
                    self.tb_img_directory = gr.Textbox(
                        label="Dataset directory",
                        placeholder="C:\\directory\\of\\datasets",
                        value=cfg_general.dataset_dir,
                    )
                with gr.Column(scale=1, min_width=60):
                    self.tb_caption_file_ext = gr.Textbox(
                        label="Caption File Ext",
                        placeholder=".txt (on Load and Save)",
                        value=cfg_general.caption_ext,
                    )
                    self.caption_file_ext = cfg_general.caption_ext
                with gr.Column(scale=1, min_width=80):
                    self.btn_load_datasets = gr.Button(value="Load")
                    self.btn_unload_datasets = gr.Button(value="Unload")
            with gr.Accordion(label="Dataset Load Settings"):
                with gr.Row():
                    with gr.Column():
                        self.cb_load_recursive = gr.Checkbox(
                            value=cfg_general.load_recursive,
                            label="Load from subdirectories",
                        )
                        self.cb_load_caption_from_filename = gr.Checkbox(
                            value=cfg_general.load_caption_from_filename,
                            label="Load caption from filename if no text file exists",
                        )
                        self.cb_replace_new_line_with_comma = gr.Checkbox(
                            value=cfg_general.replace_new_line,
                            label="Replace new-line character with comma",
                        )
                    with gr.Column():
                        self.rb_use_interrogator = gr.Radio(
                            choices=[
                                "No",
                                "If Empty",
                                "Overwrite",
                                "Prepend",
                                "Append",
                            ],
                            value=cfg_general.use_interrogator,
                            label="Use Interrogator Caption",
                        )
                        self.dd_intterogator_names = gr.Dropdown(
                            label="Interrogators",
                            choices=dte_instance.INTERROGATOR_NAMES,
                            value=cfg_general.use_interrogator_names,
                            interactive=True,
                            multiselect=True,
                        )
            with gr.Accordion(label="Interrogator Settings", open=False):
                with gr.Row():
                    self.cb_use_custom_threshold_booru = gr.Checkbox(
                        value=cfg_general.use_custom_threshold_booru,
                        label="Use Custom Threshold (Booru)",
                        interactive=True,
                    )
                    self.sl_custom_threshold_booru = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=cfg_general.custom_threshold_booru,
                        step=0.01,
                        interactive=True,
                        label="Booru Score Threshold",
                    )
                with gr.Row():
                    self.sl_custom_threshold_z3d = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=cfg_general.custom_threshold_z3d,
                        step=0.01,
                        interactive=True,
                        label="Z3D-E621 Score Threshold",
                    )
                with gr.Row():
                    self.cb_use_custom_threshold_waifu = gr.Checkbox(
                        value=cfg_general.use_custom_threshold_waifu,
                        label="Use Custom Threshold (WDv1.4 Tagger)",
                        interactive=True,
                    )
                    self.sl_custom_threshold_waifu = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=cfg_general.custom_threshold_waifu,
                        step=0.01,
                        interactive=True,
                        label="WDv1.4 Tagger Score Threshold",
                    )

    def set_callbacks(
        self,
        o_update_filter_and_gallery: List[gr.components.Component],
        toprow: ToprowUI,
        dataset_gallery: DatasetGalleryUI,
        filter_by_tags: FilterByTagsUI,
        filter_by_selection: FilterBySelectionUI,
        batch_edit_captions: BatchEditCaptionsUI,
        update_filter_and_gallery: Callable[[], List],
    ):
        def load_files_from_dir(
            dir: str,
            caption_file_ext: str,
            recursive: bool,
            load_caption_from_filename: bool,
            replace_new_line: bool,
            use_interrogator: str,
            use_interrogator_names,  #: List[str], : to avoid error on gradio v3.23.0
            use_custom_threshold_booru: bool,
            custom_threshold_booru: float,
            use_custom_threshold_waifu: bool,
            custom_threshold_waifu: float,
            custom_threshold_z3d: float,
            use_kohya_metadata: bool,
            kohya_json_path: str,
        ):

            interrogate_method = dte_instance.InterrogateMethod.NONE
            if use_interrogator == "If Empty":
                interrogate_method = dte_instance.InterrogateMethod.PREFILL
            elif use_interrogator == "Overwrite":
                interrogate_method = dte_instance.InterrogateMethod.OVERWRITE
            elif use_interrogator == "Prepend":
                interrogate_method = dte_instance.InterrogateMethod.PREPEND
            elif use_interrogator == "Append":
                interrogate_method = dte_instance.InterrogateMethod.APPEND

            threshold_booru = (
                custom_threshold_booru
                if use_custom_threshold_booru
                else opts.interrogate_deepbooru_score_threshold
            )
            threshold_waifu = (
                custom_threshold_waifu if use_custom_threshold_waifu else -1
            )
            threshold_z3d = custom_threshold_z3d

            dte_instance.load_dataset(
                dir,
                caption_file_ext,
                recursive,
                load_caption_from_filename,
                replace_new_line,
                interrogate_method,
                use_interrogator_names,
                threshold_booru,
                threshold_waifu,
                threshold_z3d,
                opts.dataset_editor_use_temp_files,
                kohya_json_path if use_kohya_metadata else None,
                opts.dataset_editor_max_res,
            )
            imgs = dte_instance.get_filtered_imgs(filters=[])
            img_indices = dte_instance.get_filtered_imgindices(filters=[])
            return (
                [imgs, []]
                + [
                    gr.CheckboxGroup.update(
                        value=[str(i) for i in img_indices],
                        choices=[str(i) for i in img_indices],
                    ),
                    1,
                ]
                + filter_by_tags.clear_filters(update_filter_and_gallery)
                + [batch_edit_captions.tag_select_ui_remove.cbg_tags_update()]
            )

        self.btn_load_datasets.click(
            fn=load_files_from_dir,
            inputs=[
                self.tb_img_directory,
                self.tb_caption_file_ext,
                self.cb_load_recursive,
                self.cb_load_caption_from_filename,
                self.cb_replace_new_line_with_comma,
                self.rb_use_interrogator,
                self.dd_intterogator_names,
                self.cb_use_custom_threshold_booru,
                self.sl_custom_threshold_booru,
                self.cb_use_custom_threshold_waifu,
                self.sl_custom_threshold_waifu,
                self.sl_custom_threshold_z3d,
                toprow.cb_save_kohya_metadata,
                toprow.tb_metadata_output,
            ],
            outputs=[
                dataset_gallery.gl_dataset_images,
                filter_by_selection.gl_filter_images,
            ]
            + [
                dataset_gallery.cbg_hidden_dataset_filter,
                dataset_gallery.nb_hidden_dataset_filter_apply,
            ]
            + o_update_filter_and_gallery,
        )

        def unload_files():
            dte_instance.clear()
            return (
                [[], []]
                + [gr.CheckboxGroup.update(value=[], choices=[]), 1]
                + filter_by_tags.clear_filters(update_filter_and_gallery)
                + [batch_edit_captions.tag_select_ui_remove.cbg_tags_update()]
            )

        self.btn_unload_datasets.click(
            fn=unload_files,
            outputs=[
                dataset_gallery.gl_dataset_images,
                filter_by_selection.gl_filter_images,
            ]
            + [
                dataset_gallery.cbg_hidden_dataset_filter,
                dataset_gallery.nb_hidden_dataset_filter_apply,
            ]
            + o_update_filter_and_gallery,
        )
