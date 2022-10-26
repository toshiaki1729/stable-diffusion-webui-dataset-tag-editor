from modules import shared
from modules import script_callbacks
from modules.shared import opts
from typing import List
import gradio as gr
from dataset_tag_editor import DatasetTagEditor

dataset_tag_editor = DatasetTagEditor()


# ================================================================
# Callbacks for "Filter and Edit Tags" tab
# ================================================================

def arrange_tag_order(tags: List[str], sort_by: str, sort_order: str) -> List[str]:
    tags = dataset_tag_editor.sort_tags(tags=tags, sort_by=sort_by, sort_order=sort_order)
    return tags


def load_files_from_dir(dir: str, sort_by: str, sort_order: str):
    dataset_tag_editor.load_dataset(dir)
    tags = arrange_tag_order(tags=dataset_tag_editor.get_tags(), sort_by=sort_by, sort_order=sort_order)
    return [
        dataset_tag_editor.get_img_path_list(),
        gr.CheckboxGroup.update(value=None, choices=dataset_tag_editor.write_tags(tags)),
        ''
    ]


def search_tags(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    tags = arrange_tag_order(tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def rearrange_tag_order(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def filter_gallery_by_checkbox(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    return filter_gallery(filter_tags=filter_tags, filter_word=filter_word, sort_by=sort_by, sort_order=sort_order)

def filter_gallery(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    img_paths, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    filter_tag_text = ', '.join(filter_tags) if filter_tags else ''
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    filter_tags = dataset_tag_editor.write_tags(filter_tags)
    tags = dataset_tag_editor.write_tags(tags)
    if filter_tags and len(filter_tags) == 0:
        filter_tags = None
    return [
        img_paths,
        gr.CheckboxGroup.update(value=filter_tags, choices=tags),
        filter_tag_text,
        filter_tag_text,
        -1
    ]


def apply_edit_tags(edit_tags: str, filter_tags: List[str], append_to_begin: bool, filter_word: str, sort_by: str, sort_order: str):
    replace_tags = [t.strip() for t in edit_tags.split(',')]
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    dataset_tag_editor.replace_tags(search_tags = filter_tags, replace_tags = replace_tags, filter_tags = filter_tags, append_to_begin = append_to_begin)
    replace_tags = [t for t in replace_tags if t]
    return filter_gallery(filter_tags = replace_tags, filter_word = filter_word, sort_by=sort_by, sort_order=sort_order)


def save_all_changes(backup: bool):
    saved, total, dir = dataset_tag_editor.save_dataset(backup=backup)
    return f'Saved text files : {saved}/{total} in {dir}'


# ================================================================
# Callbacks for "Edit Tags of Selected Image" tab
# ================================================================

def gallery_index_changed(filter_tags: List[str], idx: int):
    idx = int(idx)
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags)
    if idx < 0 or len(img_paths) <= idx:
        return ['', -1]
    else:
        return [', '.join(dataset_tag_editor.get_tags_by_image_path(img_paths[idx])), idx]


def change_tags_selected_image(tags_text: str, filter_tags: List[str], sort_by: str, sort_order: str, idx: int):
    idx = int(idx)
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags)

    edited_tags = [t.strip() for t in tags_text.split(',')]

    if idx < 0 or len(img_paths) <= idx:
        return [gr.CheckboxGroup.update(), -1]
    else:
        dataset_tag_editor.set_tags_by_image_path(imgpath=img_paths[idx], tags=edited_tags)
        _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags)
        tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
        return [gr.CheckboxGroup.update(value=dataset_tag_editor.write_tags(filter_tags), choices=dataset_tag_editor.write_tags(tags)), idx]

# ================================================================
# Script Callbacks
# ================================================================

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as dataset_tag_editor_interface:
        with gr.Row(visible=False):
            btn_hidden_set_index = gr.Button(elem_id="dataset_tag_editor_set_index")
            lbl_hidden_image_index = gr.Label(value=-1)

        gr.HTML(value="""
        This extension works well with text captions in comma-separated style (such as the tags generated by DeepBooru interrogator).
        """)
        with gr.Column(variant='panel'):
            with gr.Row():
                with gr.Column(scale=1):
                    btn_save_all_changes = gr.Button(value='Save all changes', variant='primary')
                with gr.Column(scale=2):
                    cb_backup = gr.Checkbox(value=True, label='Backup original text file (original file will be renamed like filename.000, .001, .002, ...)', interactive=True)
            gr.HTML(value='<b>Note:</b> New text file will be created if you are using filename as captions.')
            txt_result = gr.Textbox(label='Results', interactive=False)

        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):
                with gr.Row():
                    with gr.Column(scale=4):
                        tb_img_directory = gr.Textbox(label='Dataset directory', placeholder='C:\\directory\\of\\datasets')
                    with gr.Column(scale=1, min_width=80):
                        btn_load_datasets = gr.Button(value='Load')
                gl_dataset_images = gr.Gallery(label='Dataset Images', elem_id="dataset_tag_editor_images_gallery").style(grid=opts.dataset_editor_image_columns)
            with gr.Tab(label='Filter and Edit Tags'):
                with gr.Column():
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags')
                        tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
                        btn_clear_tag_filters = gr.Button(value='Clear all filters')
                        with gr.Row():
                            rd_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value='Alphabetical Order', interactive=True, label='Sort by')
                            rd_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value='Ascending', interactive=True, label='Sort Order')
                        cbg_tags = gr.CheckboxGroup(label='Filter Images by Tags', interactive=True)
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Edit tags in filtered images')
                        tb_selected_tags = gr.Textbox(label='Selected Tags', interactive=False)
                        tb_edit_tags = gr.Textbox(label='Edit Tags', interactive=True)
                        btn_apply_edit_tags = gr.Button(value='Apply changes to filtered images')
                        cb_append_tags_to_begin = gr.Checkbox(value=False, label='Append additional tags to the beginning')

                        gr.HTML(value="""
                        1. The selected tags are displayed in comma separated style.<br>
                        2. When changes are applied, all tags in each displayed images are replaced.<br>
                        3. If you change some tags into blank, they will be erased.<br>
                        4. If you add some tags to the end, they will be appended to the end/beginning of the text file.<br>
                        5. Changes are not applied to the text files until the "Save all changes" button is pressed.<br>
                        <b>ex A.</b><br>
                        &emsp;Original Text = "A, A, B, C"&emsp;Selected Tags = "B, A"&emsp;Edit Tags = "X, Y"<br>
                        &emsp;Result = "Y, Y, X, C"&emsp;(B->X, A->Y)<br>
                        <b>ex B.</b><br>
                        &emsp;Original Text = "A, B, C"&emsp;Selected Tags = "(nothing)"&emsp;Edit Tags = "X, Y"<br>
                        &emsp;Result = "A, B, C, X, Y"&emsp;(add X and Y to the end (default))<br>
                        &emsp;Result = "X, Y, A, B, C"&emsp;(add X and Y to the beginning ("Append additional tags to the beginning" checked))<br>
                        <b>ex C.</b><br>
                        &emsp;Original Text = "A, B, C, D, E"&emsp;Selected Tags = "A, B, D"&emsp;Edit Tags = ", X, "<br>
                        &emsp;Result = "X, C, E"&emsp;(A->"", B->X, D->"")<br>
                        """)

            with gr.Tab(label='Edit Tags of Selected Image'):
                with gr.Column():
                    tb_tags_selected_image = gr.Textbox(label='Tags of Selected Image', interactive=False, lines=6)
                    btn_copy_tags_selected_image = gr.Button(value='Copy tags')
                    tb_edit_tags_selected_image = gr.Textbox(label='Edit Tags', interactive=True, lines=6)
                    btn_apply_changes_selected_image = gr.Button(value='Apply changes to selected image')

                    gr.HTML("""Changes are not applied to the text files until the "Save all changes" button is pressed.""")
        
        #----------------------------------------------------------------
        # Filter and Edit Tags tab
        btn_save_all_changes.click(
            fn=save_all_changes,
            inputs=[cb_backup],
            outputs=[txt_result]
        )

        btn_load_datasets.click(
            fn=load_files_from_dir,
            inputs=[tb_img_directory, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_search_tags]
        )
        btn_load_datasets.click(
            fn=lambda:['', -1],
            inputs=[],
            outputs=[tb_tags_selected_image, lbl_hidden_image_index]
        )

        cbg_tags.change(
            fn=filter_gallery_by_checkbox,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index]
        )

        rd_sort_by.change(
            fn=rearrange_tag_order,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        rd_sort_order.change(
            fn=rearrange_tag_order,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        tb_search_tags.change(
            fn=search_tags,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        btn_apply_edit_tags.click(
            fn=apply_edit_tags,
            inputs=[tb_edit_tags, cbg_tags, cb_append_tags_to_begin, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index]
        )

        btn_clear_tag_filters.click(
            fn=lambda: [
                dataset_tag_editor.get_img_path_list(),
                gr.CheckboxGroup.update(value=None, choices=dataset_tag_editor.write_tags(dataset_tag_editor.get_tags())),
                '', '', '', '', -1],
            inputs=None,
            outputs=[gl_dataset_images, cbg_tags, tb_search_tags, tb_selected_tags, tb_edit_tags, tb_tags_selected_image, lbl_hidden_image_index]
        )

        #----------------------------------------------------------------
        # Edit Tags of Selected Image tab

        btn_hidden_set_index.click(
            fn=gallery_index_changed,
            _js="(x, y, z) => [x, dataset_tag_editor_selected_gallery_index()]",
            inputs=[cbg_tags, lbl_hidden_image_index],
            outputs=[tb_tags_selected_image, lbl_hidden_image_index]
        )

        btn_copy_tags_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_tags_selected_image],
            outputs=[tb_edit_tags_selected_image]
        )

        btn_apply_changes_selected_image.click(
            fn=change_tags_selected_image,
            _js="(a, b, c, d, e) => [a, b, c, d, dataset_tag_editor_selected_gallery_index()]",
            inputs=[tb_edit_tags_selected_image, cbg_tags, rd_sort_by, rd_sort_order, lbl_hidden_image_index],
            outputs=[cbg_tags, lbl_hidden_image_index]
        )
        btn_apply_changes_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_edit_tags_selected_image],
            outputs=[tb_tags_selected_image]
        )

    return [(dataset_tag_editor_interface, "Dataset Tag Editor", "dataset_tag_editor_interface")]


def on_ui_settings():
    section = ('dataset-tag-editor', "Dataset Tag Editor")
    shared.opts.add_option("dataset_editor_image_columns", shared.OptionInfo(6, "Number of columns on image gallery", section=section))


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
