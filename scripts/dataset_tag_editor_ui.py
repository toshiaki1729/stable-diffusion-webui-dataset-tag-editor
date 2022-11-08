from typing import List
from modules import shared
from modules import script_callbacks
from modules.shared import opts
import gradio as gr
from dataset_tag_editor import DatasetTagEditor

dataset_tag_editor = DatasetTagEditor()

total_image_num = 0
displayed_image_num = 0
current_tag_filter = ''
current_selection = 0
tmp_selection_img_path_set = set()
selected_image_path = ''
selection_selected_image_path = ''

# ================================================================
# Callbacks for "Filter and Edit Tags" tab
# ================================================================

def arrange_tag_order(tags: List[str], sort_by: str, sort_order: str) -> List[str]:
    tags = dataset_tag_editor.sort_tags(tags=tags, sort_by=sort_by, sort_order=sort_order)
    return tags


def load_files_from_dir(dir: str, sort_by: str, sort_order: str, recursive: bool):
    global total_image_num, displayed_image_num, current_tag_filter, current_selection, tmp_selection_img_path_set, selected_image_path, selection_selected_image_path
    dataset_tag_editor.load_dataset(img_dir=dir, recursive=recursive)
    img_paths, tags = dataset_tag_editor.get_filtered_imgpath_and_tags()
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    total_image_num = displayed_image_num = len(dataset_tag_editor.get_img_path_set())
    current_tag_filter = ''
    tmp_selection_img_path_set = set()
    current_selection = 0
    selected_image_path = ''
    selection_selected_image_path = ''
    return [
        img_paths,
        [],
        gr.CheckboxGroup.update(value=None, choices=dataset_tag_editor.write_tags(tags)),
        '',
        f"""
        Displayed Images : {displayed_image_num} / {total_image_num} total<br>
        Current Tag Filter : {current_tag_filter}<br>
        Current Selection Filter : {current_selection} images<br>
        Selected Image : {selected_image_path}
        """,
        f"""Selected Image : {selection_selected_image_path}"""
    ]


def search_tags(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    tags = arrange_tag_order(tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def clear_tag_filters(sort_by, sort_order):
    return filter_gallery(filter_tags=[], filter_word='', sort_by=sort_by, sort_order=sort_order) + ['']


def rearrange_tag_order(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def filter_gallery_by_checkbox(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    return filter_gallery(filter_tags=filter_tags, filter_word=filter_word, sort_by=sort_by, sort_order=sort_order)


def filter_gallery(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    global displayed_image_num, total_image_num, current_tag_filter, current_selection, selected_image_path
    img_paths, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags, filter_word=filter_word)
    current_tag_filter = ', '.join(filter_tags) if filter_tags else ''
    displayed_image_num = len(img_paths)
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    filter_tags = dataset_tag_editor.write_tags(filter_tags)
    tags = dataset_tag_editor.write_tags(tags)
    current_selection = len(tmp_selection_img_path_set)
    if filter_tags and len(filter_tags) == 0:
        filter_tags = None
    return [
        img_paths,
        gr.CheckboxGroup.update(value=filter_tags, choices=tags),
        current_tag_filter,
        current_tag_filter,
        -1,
        f"""
        Displayed Images : {displayed_image_num} / {total_image_num} total<br>
        Current Tag Filter : {current_tag_filter}<br>
        Current Selection Filter : {current_selection} images<br>
        Selected Image : {selected_image_path}
        """
        ]


def apply_edit_tags(edit_tags: str, filter_tags: List[str], append_to_begin: bool, filter_word: str, sort_by: str, sort_order: str):
    replace_tags = [t.strip() for t in edit_tags.split(',')]
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    dataset_tag_editor.replace_tags(search_tags = filter_tags, replace_tags = replace_tags, filter_tags = filter_tags, append_to_begin = append_to_begin)
    replace_tags = [t for t in replace_tags if t]
    return filter_gallery(filter_tags = replace_tags, filter_word = filter_word, sort_by=sort_by, sort_order=sort_order)


def save_all_changes(backup: bool) -> str:
    saved, total, dir = dataset_tag_editor.save_dataset(backup=backup)
    return f'Saved text files : {saved}/{total} under {dir}' if total > 0 else ''


# ================================================================
# Callbacks for "Filter by Selection" tab
# ================================================================

def arrange_selection_order(paths: List[str]) -> List[str]:
    return sorted(paths)


def selection_index_changed(idx: int):
    global tmp_selection_img_path_set, selection_selected_image_path
    idx = int(idx)
    img_paths = arrange_selection_order(tmp_selection_img_path_set)
    if idx < 0 or len(img_paths) <= idx:
        selection_selected_image_path = ''
        idx = -1
    else:
        selection_selected_image_path = img_paths[idx]
    return [f"""Selected Image : {selection_selected_image_path}""", idx]


def add_image_selection(filter_tags: List[str], idx: int):
    global tmp_selection_img_path_set
    idx = int(idx)
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags)
    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        tmp_selection_img_path_set.add(img_paths[idx])
    return [arrange_selection_order(tmp_selection_img_path_set), idx]


def invert_image_selection():
    global tmp_selection_img_path_set
    img_paths = dataset_tag_editor.get_img_path_set()
    tmp_selection_img_path_set = img_paths - tmp_selection_img_path_set
    return arrange_selection_order(tmp_selection_img_path_set)


def remove_image_selection(idx: int):
    global tmp_selection_img_path_set, selection_selected_image_path
    idx = int(idx)
    img_paths = arrange_selection_order(tmp_selection_img_path_set)
    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        tmp_selection_img_path_set.remove(img_paths[idx])
        selection_selected_image_path = ''

    return [
        arrange_selection_order(tmp_selection_img_path_set),
        f"""Selected Image : {selection_selected_image_path}""",
        idx
    ]


def clear_image_selection():
    global tmp_selection_img_path_set, selection_selected_image_path
    tmp_selection_img_path_set.clear()
    selection_selected_image_path = ''
    dataset_tag_editor.set_img_filter_img_path()
    return[
        [],
        f"""Selected Image : {selection_selected_image_path}""",
        -1
    ]


def apply_image_selection_filter(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    global tmp_selection_img_path_set
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    dataset_tag_editor.set_img_filter_img_path(tmp_selection_img_path_set)
    return filter_gallery(filter_tags=filter_tags, filter_word=filter_word, sort_by=sort_by, sort_order=sort_order)
    

# ================================================================
# Callbacks for "Edit Caption of Selected Image" tab
# ================================================================

def gallery_index_changed(filter_tags: List[str], idx: int):
    global displayed_image_num, total_image_num, current_tag_filter, current_selection, selected_image_path
    idx = int(idx)
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filter_tags=filter_tags)
    tags_txt = ''
    if 0 <= idx and idx < len(img_paths):
        selected_image_path = img_paths[idx]
        tags_txt = ', '.join(dataset_tag_editor.get_tags_by_image_path(selected_image_path))
    else:
        selected_image_path = ''
        idx = -1
    
    return [
        tags_txt,
        f"""
        Displayed Images : {displayed_image_num} / {total_image_num} total<br>
        Current Tag Filter : {current_tag_filter}<br>
        Current Selection Filter : {current_selection} images<br>
        Selected Image : {selected_image_path}
        """,
        idx
        ]


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
    global displayed_image_num, total_image_num, current_tag_filter, current_selection, selected_image_path, selection_selected_image_path
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
                    with gr.Column(scale=3):
                        tb_img_directory = gr.Textbox(label='Dataset directory', placeholder='C:\\directory\\of\\datasets')
                    with gr.Column(scale=1, min_width=80):
                        btn_load_datasets = gr.Button(value='Load')
                        cb_load_recursive = gr.Checkbox(value=False, label='Load from subdirectories')
                gl_dataset_images = gr.Gallery(label='Dataset Images', elem_id="dataset_tag_editor_images_gallery").style(grid=opts.dataset_editor_image_columns)
                txt_filter = gr.HTML(value=f"""
                Displayed Images : {displayed_image_num} / {total_image_num} total<br>
                Current Tag Filter : {current_tag_filter}<br>
                Current Selection Filter : {current_selection} images<br>
                Selected Image : {selected_image_path}
                """)

            with gr.Tab(label='Filter and Edit Tags'):
                with gr.Column():
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags')
                        tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
                        with gr.Row():
                            btn_clear_tag_filters = gr.Button(value='Clear tag filters')
                            btn_clear_all_filters = gr.Button(value='Clear ALL filters')
                        with gr.Row():
                            rd_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value='Alphabetical Order', interactive=True, label='Sort by')
                            rd_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value='Ascending', interactive=True, label='Sort Order')
                        cbg_tags = gr.CheckboxGroup(label='Filter Images by Tags', interactive=True)
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Edit tags in filtered images')
                        tb_selected_tags = gr.Textbox(label='Selected Tags', interactive=False)
                        tb_edit_tags = gr.Textbox(label='Edit Tags', interactive=True)
                        btn_apply_edit_tags = gr.Button(value='Apply changes to filtered images', variant='primary')
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
            
            with gr.Tab(label='Filter by Selection'):
                with gr.Row(visible=False):
                    btn_hidden_set_selection_index = gr.Button(elem_id="dataset_tag_editor_set_selection_index")
                    lbl_hidden_selection_image_index = gr.Label(value=-1)
                gr.HTML("""Select images from the left gallery.""")
                
                with gr.Column(variant='panel'):
                    with gr.Row():
                        btn_add_image_selection = gr.Button(value='Add selection [Enter]', elem_id='dataset_tag_editor_btn_add_image_selection')    

                    gl_selected_images = gr.Gallery(label='Filter Images', elem_id="dataset_tag_editor_selection_images_gallery").style(grid=opts.dataset_editor_image_columns)
                    txt_selection = gr.HTML(value=f"""Selected Image : {selection_selected_image_path}""")

                    with gr.Row():
                        btn_remove_image_selection = gr.Button(value='Remove selection [Delete]', elem_id='dataset_tag_editor_btn_remove_image_selection')
                        btn_invert_image_selection = gr.Button(value='Invert selection')
                        btn_clear_image_selection = gr.Button(value='Clear selection')

                btn_apply_image_selection_filter = gr.Button(value='Apply selection filter', variant='primary')
                    

            with gr.Tab(label='Edit Caption of Selected Image'):
                with gr.Column():
                    tb_caption_selected_image = gr.Textbox(label='Caption of Selected Image', interactive=False, lines=6)
                    btn_copy_caption_selected_image = gr.Button(value='Copy caption')
                    tb_edit_caption_selected_image = gr.Textbox(label='Edit Caption', interactive=True, lines=6)
                    btn_apply_changes_selected_image = gr.Button(value='Apply changes to selected image', variant='primary')

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
            inputs=[tb_img_directory, rd_sort_by, rd_sort_order, cb_load_recursive],
            outputs=[gl_dataset_images, gl_selected_images, cbg_tags, tb_search_tags, txt_filter, txt_selection]
        )
        btn_load_datasets.click(
            fn=lambda:['', -1],
            inputs=[],
            outputs=[tb_caption_selected_image, lbl_hidden_image_index]
        )

        cbg_tags.change(
            fn=filter_gallery_by_checkbox,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index, txt_filter]
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
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index, txt_filter]
        )

        btn_clear_tag_filters.click(
            fn=clear_tag_filters,
            inputs=[rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index, txt_filter, tb_search_tags]
        )

        btn_clear_all_filters.click(
            fn=clear_image_selection,
            inputs=None,
            outputs=[gl_selected_images, txt_selection, lbl_hidden_selection_image_index]
        )

        btn_clear_all_filters.click(
            fn=clear_tag_filters,
            inputs=[rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index, txt_filter, tb_search_tags]
        )

        #----------------------------------------------------------------
        # Filter by Selection tab

        btn_hidden_set_selection_index.click(
            fn=selection_index_changed,
            _js="(x) => [dataset_tag_editor_selected_selection_index()]",
            inputs=[lbl_hidden_selection_image_index],
            outputs=[txt_selection, lbl_hidden_selection_image_index]
        )

        btn_add_image_selection.click(
            fn=add_image_selection,
            _js="(x, y) => [x, dataset_tag_editor_selected_gallery_index()]",
            inputs=[cbg_tags, lbl_hidden_image_index],
            outputs=[gl_selected_images, lbl_hidden_image_index]
        )

        btn_invert_image_selection.click(
            fn=invert_image_selection,
            inputs=None,
            outputs=gl_selected_images
        )

        btn_remove_image_selection.click(
            fn=remove_image_selection,
            _js="(x) => [dataset_tag_editor_selected_selection_index()]",
            inputs=[lbl_hidden_selection_image_index],
            outputs=[gl_selected_images,txt_selection,lbl_hidden_selection_image_index]
        )

        btn_clear_image_selection.click(
            fn=clear_image_selection,
            inputs=None,
            outputs=[gl_selected_images,txt_selection,lbl_hidden_selection_image_index]
        )

        btn_apply_image_selection_filter.click(
            fn=apply_image_selection_filter,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, lbl_hidden_image_index, txt_filter]
        )

        #----------------------------------------------------------------
        # Edit Caption of Selected Image tab

        btn_hidden_set_index.click(
            fn=gallery_index_changed,
            _js="(x, y) => [x, dataset_tag_editor_selected_gallery_index()]",
            inputs=[cbg_tags, lbl_hidden_image_index],
            outputs=[tb_caption_selected_image, txt_filter, lbl_hidden_image_index]
        )

        btn_copy_caption_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_apply_changes_selected_image.click(
            fn=change_tags_selected_image,
            _js="(a, b, c, d, e) => [a, b, c, d, dataset_tag_editor_selected_gallery_index()]",
            inputs=[tb_edit_caption_selected_image, cbg_tags, rd_sort_by, rd_sort_order, lbl_hidden_image_index],
            outputs=[cbg_tags, lbl_hidden_image_index]
        )
        btn_apply_changes_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_edit_caption_selected_image],
            outputs=[tb_caption_selected_image]
        )

    return [(dataset_tag_editor_interface, "Dataset Tag Editor", "dataset_tag_editor_interface")]


def on_ui_settings():
    section = ('dataset-tag-editor', "Dataset Tag Editor")
    shared.opts.add_option("dataset_editor_image_columns", shared.OptionInfo(6, "Number of columns on image gallery", section=section))


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
