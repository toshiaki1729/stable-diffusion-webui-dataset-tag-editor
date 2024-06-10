from typing import NamedTuple, Type, Dict, Any
from modules import shared, script_callbacks
from modules.shared import opts
import gradio as gr
from scripts.config import *

import scripts.tag_editor_ui as ui

# ================================================================
# General Callbacks
# ================================================================

config = Config()


def write_general_config(*args):
    cfg = GeneralConfig(*args)
    config.write(cfg._asdict(), "general")


def write_filter_config(*args):
    hlen = len(args) // 2
    cfg_p = FilterConfig(*args[:hlen])
    cfg_n = FilterConfig(*args[hlen:])
    config.write({"positive": cfg_p._asdict(), "negative": cfg_n._asdict()}, "filter")


def write_batch_edit_config(*args):
    cfg = BatchEditConfig(*args)
    config.write(cfg._asdict(), "batch_edit")


def write_edit_selected_config(*args):
    cfg = EditSelectedConfig(*args)
    config.write(cfg._asdict(), "edit_selected")


def write_move_delete_config(*args):
    cfg = MoveDeleteConfig(*args)
    config.write(cfg._asdict(), "file_move_delete")


def read_config(name: str, config_type: Type, default: NamedTuple, compat_func=None):
    d = config.read(name)
    cfg = default
    if d:
        if compat_func:
            d = compat_func(d)
        d = cfg._asdict() | d
        d = {k: v for k, v in d.items() if k in cfg._asdict().keys()}
        cfg = config_type(**d)
    return cfg


def read_general_config():
    # for compatibility
    generalcfg_intterogator_names = [
        ("use_blip_to_prefill", "BLIP"),
        ("use_git_to_prefill", "GIT-large-COCO"),
        ("use_booru_to_prefill", "DeepDanbooru"),
        ("use_waifu_to_prefill", "wd-v1-4-vit-tagger"),
    ]
    use_interrogator_names = []

    def compat_func(d: Dict[str, Any]):
        if "use_interrogator_names" in d.keys():
            return d
        for cfg in generalcfg_intterogator_names:
            if d.get(cfg[0]):
                use_interrogator_names.append(cfg[1])
        d["use_interrogator_names"] = use_interrogator_names
        return d

    return read_config("general", GeneralConfig, CFG_GENERAL_DEFAULT, compat_func)


def read_filter_config():
    d = config.read("filter")
    d_p = d.get("positive") if d else None
    d_n = d.get("negative") if d else None
    cfg_p = CFG_FILTER_P_DEFAULT
    cfg_n = CFG_FILTER_N_DEFAULT
    if d_p:
        d_p = cfg_p._asdict() | d_p
        d_p = {k: v for k, v in d_p.items() if k in cfg_p._asdict().keys()}
        cfg_p = FilterConfig(**d_p)
    if d_n:
        d_n = cfg_n._asdict() | d_n
        d_n = {k: v for k, v in d_n.items() if k in cfg_n._asdict().keys()}
        cfg_n = FilterConfig(**d_n)
    return cfg_p, cfg_n


def read_batch_edit_config():
    return read_config("batch_edit", BatchEditConfig, CFG_BATCH_EDIT_DEFAULT)


def read_edit_selected_config():
    return read_config("edit_selected", EditSelectedConfig, CFG_EDIT_SELECTED_DEFAULT)


def read_move_delete_config():
    return read_config("file_move_delete", MoveDeleteConfig, CFG_MOVE_DELETE_DEFAULT)


# ================================================================
# General Callbacks for Updating UIs
# ================================================================


def get_filters():
    filters = [
        ui.filter_by_tags.tag_filter_ui.get_filter(),
        ui.filter_by_tags.tag_filter_ui_neg.get_filter(),
    ] + [ui.filter_by_selection.path_filter]
    return filters


def update_gallery():
    img_indices = ui.dte_instance.get_filtered_imgindices(filters=get_filters())
    total_image_num = len(ui.dte_instance.dataset)
    displayed_image_num = len(img_indices)
    ui.gallery_state.register_value(
        "Displayed Images", f"{displayed_image_num} / {total_image_num} total"
    )
    ui.gallery_state.register_value(
        "Current Tag Filter",
        f"{ui.filter_by_tags.tag_filter_ui.get_filter()} {' AND ' if ui.filter_by_tags.tag_filter_ui.get_filter().tags and ui.filter_by_tags.tag_filter_ui_neg.get_filter().tags else ''} {ui.filter_by_tags.tag_filter_ui_neg.get_filter()}",
    )
    ui.gallery_state.register_value(
        "Current Selection Filter",
        f"{len(ui.filter_by_selection.path_filter.paths)} images",
    )
    return [
        [str(i) for i in img_indices],
        1,
        -1,
        -1,
        -1,
        ui.gallery_state.get_current_gallery_txt(),
    ]


def update_filter_and_gallery():
    return (
        [
            ui.filter_by_tags.tag_filter_ui.cbg_tags_update(),
            ui.filter_by_tags.tag_filter_ui_neg.cbg_tags_update(),
        ]
        + update_gallery()
        + ui.batch_edit_captions.get_common_tags(get_filters, ui.filter_by_tags)
        + [", ".join(ui.filter_by_tags.tag_filter_ui.filter.tags)]
        + [ui.batch_edit_captions.tag_select_ui_remove.cbg_tags_update()]
        + ["", ""]
    )


# ================================================================
# Script Callbacks
# ================================================================


def on_ui_tabs():
    config.load()

    cfg_general = read_general_config()
    cfg_filter_p, cfg_filter_n = read_filter_config()
    cfg_batch_edit = read_batch_edit_config()
    cfg_edit_selected = read_edit_selected_config()
    cfg_file_move_delete = read_move_delete_config()

    ui.dte_instance.load_interrogators()

    with gr.Blocks(analytics_enabled=False) as dataset_tag_editor_interface:

        gr.HTML(
            value="""
        This extension works well with text captions in comma-separated style (such as the tags generated by DeepBooru interrogator).
        """
        )

        ui.toprow.create_ui(cfg_general)

        with gr.Accordion(label="Reload/Save Settings (config.json)", open=False):
            with gr.Row():
                btn_reload_config_file = gr.Button(value="Reload settings")
                btn_save_setting_as_default = gr.Button(value="Save current settings")
                btn_restore_default = gr.Button(value="Restore settings to default")

        with gr.Row(equal_height=False):
            with gr.Column():
                ui.load_dataset.create_ui(cfg_general)
                ui.dataset_gallery.create_ui(opts.dataset_editor_image_columns)
                ui.gallery_state.create_ui()

            with gr.Tab(label="Filter by Tags"):
                ui.filter_by_tags.create_ui(cfg_filter_p, cfg_filter_n, get_filters)

            with gr.Tab(label="Filter by Selection"):
                ui.filter_by_selection.create_ui(opts.dataset_editor_image_columns)

            with gr.Tab(label="Batch Edit Captions"):
                ui.batch_edit_captions.create_ui(cfg_batch_edit, get_filters)

            with gr.Tab(label="Edit Caption of Selected Image"):
                ui.edit_caption_of_selected_image.create_ui(cfg_edit_selected)

            with gr.Tab(label="Move or Delete Files"):
                ui.move_or_delete_files.create_ui(cfg_file_move_delete)

        # ----------------------------------------------------------------
        # General

        components_general = [
            ui.toprow.cb_backup,
            ui.load_dataset.tb_img_directory,
            ui.load_dataset.tb_caption_file_ext,
            ui.load_dataset.cb_load_recursive,
            ui.load_dataset.cb_load_caption_from_filename,
            ui.load_dataset.cb_replace_new_line_with_comma,
            ui.load_dataset.rb_use_interrogator,
            ui.load_dataset.dd_intterogator_names,
            ui.load_dataset.cb_use_custom_threshold_booru,
            ui.load_dataset.sl_custom_threshold_booru,
            ui.load_dataset.cb_use_custom_threshold_waifu,
            ui.load_dataset.sl_custom_threshold_waifu,
            ui.load_dataset.sl_custom_threshold_z3d,
            ui.toprow.cb_save_kohya_metadata,
            ui.toprow.tb_metadata_output,
            ui.toprow.tb_metadata_input,
            ui.toprow.cb_metadata_overwrite,
            ui.toprow.cb_metadata_as_caption,
            ui.toprow.cb_metadata_use_fullpath,
        ]
        components_filter = [
            ui.filter_by_tags.tag_filter_ui.cb_prefix,
            ui.filter_by_tags.tag_filter_ui.cb_suffix,
            ui.filter_by_tags.tag_filter_ui.cb_regex,
            ui.filter_by_tags.tag_filter_ui.rb_sort_by,
            ui.filter_by_tags.tag_filter_ui.rb_sort_order,
            ui.filter_by_tags.tag_filter_ui.rb_logic,
        ] + [
            ui.filter_by_tags.tag_filter_ui_neg.cb_prefix,
            ui.filter_by_tags.tag_filter_ui_neg.cb_suffix,
            ui.filter_by_tags.tag_filter_ui_neg.cb_regex,
            ui.filter_by_tags.tag_filter_ui_neg.rb_sort_by,
            ui.filter_by_tags.tag_filter_ui_neg.rb_sort_order,
            ui.filter_by_tags.tag_filter_ui_neg.rb_logic,
        ]
        components_batch_edit = [
            ui.batch_edit_captions.cb_show_only_tags_selected,
            ui.batch_edit_captions.cb_prepend_tags,
            ui.batch_edit_captions.cb_use_regex,
            ui.batch_edit_captions.rb_sr_replace_target,
            ui.batch_edit_captions.tag_select_ui_remove.cb_prefix,
            ui.batch_edit_captions.tag_select_ui_remove.cb_suffix,
            ui.batch_edit_captions.tag_select_ui_remove.cb_regex,
            ui.batch_edit_captions.tag_select_ui_remove.rb_sort_by,
            ui.batch_edit_captions.tag_select_ui_remove.rb_sort_order,
            ui.batch_edit_captions.rb_sort_by,
            ui.batch_edit_captions.rb_sort_order,
            ui.batch_edit_captions.nb_token_count,
        ]
        components_edit_selected = [
            ui.edit_caption_of_selected_image.cb_copy_caption_automatically,
            ui.edit_caption_of_selected_image.cb_sort_caption_on_save,
            ui.edit_caption_of_selected_image.cb_ask_save_when_caption_changed,
            ui.edit_caption_of_selected_image.dd_intterogator_names_si,
            ui.edit_caption_of_selected_image.rb_sort_by,
            ui.edit_caption_of_selected_image.rb_sort_order,
        ]
        components_move_delete = [
            ui.move_or_delete_files.rb_move_or_delete_target_data,
            ui.move_or_delete_files.cbg_move_or_delete_target_file,
            ui.move_or_delete_files.tb_move_or_delete_caption_ext,
            ui.move_or_delete_files.tb_move_or_delete_destination_dir,
        ]

        configurable_components = (
            components_general
            + components_filter
            + components_batch_edit
            + components_edit_selected
            + components_move_delete
        )

        def reload_config_file():
            config.load()
            p, n = read_filter_config()
            logger.write("Reload config.json")
            return (
                read_general_config()
                + p
                + n
                + read_batch_edit_config()
                + read_edit_selected_config()
                + read_move_delete_config()
            )

        btn_reload_config_file.click(
            fn=reload_config_file, outputs=configurable_components
        )

        def save_settings_callback(*a):
            p = 0

            def inc(v):
                nonlocal p
                p += v
                return p

            write_general_config(*a[p : inc(len(components_general))])
            write_filter_config(*a[p : inc(len(components_filter))])
            write_batch_edit_config(*a[p : inc(len(components_batch_edit))])
            write_edit_selected_config(*a[p : inc(len(components_edit_selected))])
            write_move_delete_config(*a[p:])
            config.save()
            logger.write("Current settings have been saved into config.json")

        btn_save_setting_as_default.click(
            fn=save_settings_callback, inputs=configurable_components
        )

        def restore_default_settings():
            write_general_config(*CFG_GENERAL_DEFAULT)
            write_filter_config(*CFG_FILTER_P_DEFAULT, *CFG_FILTER_N_DEFAULT)
            write_batch_edit_config(*CFG_BATCH_EDIT_DEFAULT)
            write_edit_selected_config(*CFG_EDIT_SELECTED_DEFAULT)
            write_move_delete_config(*CFG_MOVE_DELETE_DEFAULT)
            logger.write("Restore default settings")
            return (
                CFG_GENERAL_DEFAULT
                + CFG_FILTER_P_DEFAULT
                + CFG_FILTER_N_DEFAULT
                + CFG_BATCH_EDIT_DEFAULT
                + CFG_EDIT_SELECTED_DEFAULT
                + CFG_MOVE_DELETE_DEFAULT
            )

        btn_restore_default.click(
            fn=restore_default_settings, outputs=configurable_components
        )

        o_update_gallery = [
            ui.dataset_gallery.cbg_hidden_dataset_filter,
            ui.dataset_gallery.nb_hidden_dataset_filter_apply,
            ui.dataset_gallery.nb_hidden_image_index,
            ui.dataset_gallery.nb_hidden_image_index_prev,
            ui.edit_caption_of_selected_image.nb_hidden_image_index_save_or_not,
            ui.gallery_state.txt_gallery,
        ]

        o_update_filter_and_gallery = (
            [
                ui.filter_by_tags.tag_filter_ui.cbg_tags,
                ui.filter_by_tags.tag_filter_ui_neg.cbg_tags,
            ]
            + o_update_gallery
            + [
                ui.batch_edit_captions.tb_common_tags,
                ui.batch_edit_captions.tb_edit_tags,
            ]
            + [ui.batch_edit_captions.tb_sr_selected_tags]
            + [ui.batch_edit_captions.tag_select_ui_remove.cbg_tags]
            + [
                ui.edit_caption_of_selected_image.tb_caption,
                ui.edit_caption_of_selected_image.tb_edit_caption,
            ]
        )

        ui.toprow.set_callbacks(ui.load_dataset)
        ui.load_dataset.set_callbacks(
            o_update_filter_and_gallery,
            ui.toprow,
            ui.dataset_gallery,
            ui.filter_by_tags,
            ui.filter_by_selection,
            ui.batch_edit_captions,
            update_filter_and_gallery,
        )
        ui.dataset_gallery.set_callbacks(ui.load_dataset, ui.gallery_state, get_filters)
        ui.gallery_state.set_callbacks(ui.dataset_gallery)
        ui.filter_by_tags.set_callbacks(
            o_update_gallery,
            o_update_filter_and_gallery,
            ui.batch_edit_captions,
            ui.move_or_delete_files,
            update_gallery,
            update_filter_and_gallery,
            get_filters,
        )
        ui.filter_by_selection.set_callbacks(
            o_update_filter_and_gallery,
            ui.dataset_gallery,
            ui.filter_by_tags,
            get_filters,
            update_filter_and_gallery,
        )
        ui.batch_edit_captions.set_callbacks(
            o_update_filter_and_gallery,
            ui.load_dataset,
            ui.filter_by_tags,
            get_filters,
            update_filter_and_gallery,
        )
        ui.edit_caption_of_selected_image.set_callbacks(
            o_update_filter_and_gallery,
            ui.dataset_gallery,
            ui.load_dataset,
            get_filters,
            update_filter_and_gallery,
        )
        ui.move_or_delete_files.set_callbacks(
            o_update_filter_and_gallery,
            ui.dataset_gallery,
            get_filters,
            update_filter_and_gallery,
        )

    return [
        (
            dataset_tag_editor_interface,
            "Dataset Tag Editor",
            "dataset_tag_editor_interface",
        )
    ]


def on_ui_settings():
    section = ("dataset-tag-editor", "Dataset Tag Editor")
    shared.opts.add_option(
        "dataset_editor_image_columns",
        shared.OptionInfo(6, "Number of columns on image gallery", section=section),
    )
    shared.opts.add_option(
        "dataset_editor_max_res",
        shared.OptionInfo(0, "Max resolution of temporary files", section=section),
    )
    shared.opts.add_option(
        "dataset_editor_use_temp_files",
        shared.OptionInfo(
            False, "Force image gallery to use temporary files", section=section
        ),
    )
    shared.opts.add_option(
        "dataset_editor_use_raw_clip_token",
        shared.OptionInfo(
            True,
            "Use raw CLIP token to calculate token count (without emphasis or embeddings)",
            section=section,
        ),
    )
    shared.opts.add_option(
        "dataset_editor_use_rating",
        shared.OptionInfo(
            False,
            "Use rating tags",
            section=section,
        ),
    )

    shared.opts.add_option(
        "dataset_editor_num_cpu_workers",
        shared.OptionInfo(
            -1,
            "Number of CPU workers when preprocessing images (set -1 to auto)",
            section=section,
        ),
    )

    shared.opts.add_option(
        "dataset_editor_batch_size_vit",
        shared.OptionInfo(
            4,
            "Inference batch size for ViT taggers",
            section=section,
        ),
    )

    shared.opts.add_option(
        "dataset_editor_batch_size_convnext",
        shared.OptionInfo(
            4,
            "Inference batch size for ConvNeXt taggers",
            section=section,
        ),
    )

    shared.opts.add_option(
        "dataset_editor_batch_size_swinv2",
        shared.OptionInfo(
            4,
            "Inference batch size for SwinTransformerV2 taggers",
            section=section,
        ),
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
