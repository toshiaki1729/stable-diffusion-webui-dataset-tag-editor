from typing import List, Set
from modules import shared, script_callbacks
from modules.shared import opts, cmd_opts
import gradio as gr
from scripts.dataset_tag_editor.dataset_tag_editor import DatasetTagEditor, interrogate_image_clip, interrogate_image_booru, InterrogateMethod
from scripts.dataset_tag_editor.filters import TagFilter, PathFilter
from scripts.dataset_tag_editor.ui import TagFilterUI

dataset_tag_editor = DatasetTagEditor()

path_filter = PathFilter()
tag_filter_ui = TagFilterUI(dataset_tag_editor)
tag_filter_ui_neg = TagFilterUI(dataset_tag_editor, TagFilter.Mode.EXCLUSIVE)

get_filters = lambda:[path_filter, tag_filter_ui.get_filter(), tag_filter_ui_neg.get_filter()]

total_image_num = 0
displayed_image_num = 0
tmp_selection_img_path_set = set()
gallery_selected_image_path = ''
selection_selected_image_path = ''


# ================================================================
# Callbacks for "Filter and Edit Tags" tab
# ================================================================

def get_current_gallery_txt():
    return f"""
    Displayed Images : {displayed_image_num} / {total_image_num} total<br>
    Current Tag Filter : {tag_filter_ui.get_filter()} {' AND ' if tag_filter_ui.get_filter().tags and tag_filter_ui_neg.get_filter().tags else ''} {tag_filter_ui_neg.get_filter()}<br>
    Current Selection Filter : {len(path_filter.paths)} images<br>
    Selected Image : {gallery_selected_image_path}
    """


def get_current_txt_selection():
    return f"""Selected Image : {selection_selected_image_path}"""


def get_current_move_or_delete_target_num(target_data: str, idx: int):
    if target_data == 'Selected One':
        idx = int(idx)
        return f'Target dataset num: {1 if idx != -1 else 0}'
        
    elif target_data == 'All Displayed Ones':
        img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
        return f'Target dataset num: {len(img_paths)}'


def load_files_from_dir(dir: str, recursive: bool, load_caption_from_filename: bool, use_interrogator: str, use_clip: bool, use_booru: bool):
    global total_image_num, displayed_image_num, tmp_selection_img_path_set, gallery_selected_image_path, selection_selected_image_path, path_filter
    
    interrogate_method = InterrogateMethod.NONE
    if use_interrogator == 'If Empty':
        interrogate_method = InterrogateMethod.PREFILL
    elif use_interrogator == 'Overwrite':
        interrogate_method = InterrogateMethod.OVERWRITE
    elif use_interrogator == 'Prepend':
        interrogate_method = InterrogateMethod.PREPEND
    elif use_interrogator == 'Append':
        interrogate_method = InterrogateMethod.APPEND

    dataset_tag_editor.load_dataset(img_dir=dir, recursive=recursive, load_caption_from_filename=load_caption_from_filename, interrogate_method=interrogate_method, use_clip=use_clip, use_booru=use_booru)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    path_filter = PathFilter()
    total_image_num = displayed_image_num = len(dataset_tag_editor.get_img_path_set())
    tmp_selection_img_path_set = set()
    gallery_selected_image_path = ''
    selection_selected_image_path = ''
    return [
        img_paths,
        [],
        get_current_gallery_txt(),
        get_current_txt_selection()
    ] + clear_tag_filters()


def update_gallery():
    global displayed_image_num
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    displayed_image_num = len(img_paths)
    return [
        img_paths,
        -1,
        get_current_gallery_txt()
        ]


def update_filter_and_gallery():
    return [tag_filter_ui.cbg_tags_update(), tag_filter_ui_neg.cbg_tags_update()] + update_gallery()


def clear_tag_filters():
    tag_filter_ui.clear_filter()
    tag_filter_ui_neg.clear_filter()
    return update_filter_and_gallery() + update_common_tags()


def update_common_tags():
    tags = ', '.join(dataset_tag_editor.get_common_tags(filters=get_filters()))
    return [tags, tags]


def save_all_changes(backup: bool):
    saved, total, dir = dataset_tag_editor.save_dataset(backup=backup)
    return f'Saved text files : {saved}/{total} under {dir}' if total > 0 else ''


# ================================================================
# Callbacks for "Filter by Selection" tab
# ================================================================

def arrange_selection_order(paths: List[str]):
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
    return [get_current_txt_selection(), idx]


def add_image_selection(idx: int):
    global tmp_selection_img_path_set
    idx = int(idx)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        tmp_selection_img_path_set.add(img_paths[idx])
    return [arrange_selection_order(tmp_selection_img_path_set), idx]


def add_all_displayed_image_selection():
    global tmp_selection_img_path_set
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    tmp_selection_img_path_set |= set(img_paths)
    return arrange_selection_order(tmp_selection_img_path_set)


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
        get_current_txt_selection(),
        idx
    ]


def clear_image_selection():
    global tmp_selection_img_path_set, selection_selected_image_path, path_filter
    tmp_selection_img_path_set.clear()
    selection_selected_image_path = ''
    path_filter = PathFilter()
    return[
        [],
        get_current_txt_selection(),
        -1
    ]


def apply_image_selection_filter():
    global path_filter
    if len(tmp_selection_img_path_set) > 0:
        path_filter = PathFilter(tmp_selection_img_path_set, PathFilter.Mode.INCLUSIVE)
    else:
        path_filter = PathFilter()
    return update_filter_and_gallery() + update_common_tags()
    

# ================================================================
# Callbacks for "Edit Caption of Selected Image" tab
# ================================================================

def gallery_index_changed(idx: int):
    global gallery_selected_image_path
    idx = int(idx)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    tags_txt = ''
    if 0 <= idx and idx < len(img_paths):
        gallery_selected_image_path = img_paths[idx]
        tags_txt = ', '.join(dataset_tag_editor.get_tags_by_image_path(gallery_selected_image_path))
    else:
        gallery_selected_image_path = ''
        idx = -1
    
    return [
        tags_txt,
        get_current_gallery_txt(),
        idx
        ]


def change_selected_image_caption(tags_text: str, idx: int):
    idx = int(idx)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())

    edited_tags = [t.strip() for t in tags_text.split(',')]
    edited_tags = [t for t in edited_tags if t]

    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        dataset_tag_editor.set_tags_by_image_path(imgpath=img_paths[idx], tags=edited_tags)
    return update_filter_and_gallery() + update_common_tags() + [idx]


def interrogate_selected_image_clip():
    global gallery_selected_image_path
    return interrogate_image_clip(gallery_selected_image_path)


def interrogate_selected_image_booru():
    global gallery_selected_image_path
    return interrogate_image_booru(gallery_selected_image_path)


# ================================================================
# Callbacks for "Batch Edit Captions" tab
# ================================================================

def apply_edit_tags(search_tags: str, replace_tags: str, prepend: bool):
    search_tags = [t.strip() for t in search_tags.split(',')]
    search_tags = [t for t in search_tags if t]
    replace_tags = [t.strip() for t in replace_tags.split(',')]
    replace_tags = [t for t in replace_tags if t]

    dataset_tag_editor.replace_tags(search_tags = search_tags, replace_tags = replace_tags, filters=get_filters(), prepend = prepend)
    tag_filter_ui.get_filter().tags = dataset_tag_editor.get_replaced_tagset(tag_filter_ui.get_filter().tags, search_tags, replace_tags)
    tag_filter_ui_neg.get_filter().tags = dataset_tag_editor.get_replaced_tagset(tag_filter_ui_neg.get_filter().tags, search_tags, replace_tags)

    return update_filter_and_gallery() + update_common_tags()


def search_and_replace(search_text: str, replace_text: str, target_text: str, use_regex: bool):
    if target_text == 'Only Selected Tags':
        selected_tags = set(tag_filter_ui.selected_tags)
        dataset_tag_editor.search_and_replace_selected_tags(search_text = search_text, replace_text=replace_text, selected_tags=selected_tags, filters=get_filters(), use_regex=use_regex)
        tag_filter_ui.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui.filter.tags, selected_tags, use_regex)
        tag_filter_ui_neg.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui_neg.filter.tags, selected_tags, use_regex)

    elif target_text == 'Each Tags':
        dataset_tag_editor.search_and_replace_selected_tags(search_text = search_text, replace_text=replace_text, selected_tags=None, filters=get_filters(), use_regex=use_regex)
        tag_filter_ui.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui.filter.tags, None, use_regex)
        tag_filter_ui_neg.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui_neg.filter.tags, None, use_regex)

    elif target_text == 'Entire Caption':
        dataset_tag_editor.search_and_replace_caption(search_text=search_text, replace_text=replace_text, filters=get_filters(), use_regex=use_regex)
        tag_filter_ui.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui.filter.tags, None, use_regex)
        tag_filter_ui_neg.filter.tags = dataset_tag_editor.search_and_replace_tag_set(search_text, replace_text, tag_filter_ui_neg.filter.tags, None, use_regex)
    
    return update_filter_and_gallery() + update_common_tags()


# ================================================================
# Callbacks for "Move or Delete Files" tab
# ================================================================

def move_files(target_data: str, target_file: List[str], dest_dir: str, idx: int = -1):
    move_img = 'Image File' in target_file
    move_txt = 'Caption Text File' in target_file
    move_bak = 'Caption Backup File' in target_file
    if target_data == 'Selected One':
        idx = int(idx)
        img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
        if  0 <= idx and idx < len(img_paths):
            dataset_tag_editor.move_dataset_file(img_paths[idx], dest_dir, move_img, move_txt, move_bak)
            dataset_tag_editor.construct_tag_counts()
        
    elif target_data == 'All Displayed Ones':
        dataset_tag_editor.move_dataset(dest_dir, get_filters(), move_img, move_txt, move_bak)

    return update_filter_and_gallery() + update_common_tags()


def delete_files(target_data: str, target_file: List[str], idx: int = -1):
    delete_img = 'Image File' in target_file
    delete_txt = 'Caption Text File' in target_file
    delete_bak = 'Caption Backup File' in target_file
    if target_data == 'Selected One':
        idx = int(idx)
        img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
        if  0 <= idx and idx < len(img_paths):
            dataset_tag_editor.delete_dataset_file(delete_img, delete_txt, delete_bak)
            dataset_tag_editor.construct_tag_counts()
    
    elif target_data == 'All Displayed Ones':
        dataset_tag_editor.delete_dataset(get_filters(), delete_img, delete_txt, delete_bak)

    return update_filter_and_gallery() + update_common_tags()


# ================================================================
# Script Callbacks
# ================================================================

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as dataset_tag_editor_interface:
        with gr.Row(visible=False):
            btn_hidden_set_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_index")
            nb_hidden_image_index = gr.Number(value=-1)

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
            with gr.Column():
                with gr.Column(variant='panel'):
                    with gr.Row():
                        with gr.Column(scale=3):
                            tb_img_directory = gr.Textbox(label='Dataset directory', placeholder='C:\\directory\\of\\datasets')
                        with gr.Column(scale=1, min_width=80):
                            btn_load_datasets = gr.Button(value='Load')
                    with gr.Row():
                        with gr.Column():
                            cb_load_recursive = gr.Checkbox(value=False, label='Load from subdirectories')
                            cb_load_caption_from_filename = gr.Checkbox(value=True, label='Load caption from filename if no text file exists')
                        with gr.Column():
                            rb_use_interrogator = gr.Radio(choices=['No', 'If Empty', 'Overwrite', 'Prepend', 'Append'], value='No', label='Use Interrogator Caption')
                            with gr.Row():
                                cb_use_clip_to_prefill = gr.Checkbox(value=False, label='Use BLIP')
                                cb_use_booru_to_prefill = gr.Checkbox(value=False, label='Use DeepDanbooru')
                
                gl_dataset_images = gr.Gallery(label='Dataset Images', elem_id="dataset_tag_editor_dataset_gallery").style(grid=opts.dataset_editor_image_columns)
                txt_gallery = gr.HTML(value=get_current_gallery_txt())

            with gr.Tab(label='Filter by Tags'):
                with gr.Row():
                        btn_clear_tag_filters = gr.Button(value='Clear tag filters')
                        btn_clear_all_filters = gr.Button(value='Clear ALL filters')

                with gr.Tab(label='Positive Filter'):
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags')
                        tag_filter_ui.create_ui(get_filters)

                with gr.Tab(label='Negative Filter'):
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags')
                        tag_filter_ui_neg.create_ui(get_filters)
            
            with gr.Tab(label='Filter by Selection'):
                with gr.Row(visible=False):
                    btn_hidden_set_selection_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_selection_index")
                    nb_hidden_selection_image_index = gr.Number(value=-1)
                gr.HTML("""Select images from the left gallery.""")
                
                with gr.Column(variant='panel'):
                    with gr.Row():
                        btn_add_image_selection = gr.Button(value='Add selection [Enter]', elem_id='dataset_tag_editor_btn_add_image_selection')    
                        btn_add_all_displayed_image_selection = gr.Button(value='Add ALL Displayed')    

                    gl_selected_images = gr.Gallery(label='Filter Images', elem_id="dataset_tag_editor_selection_gallery").style(grid=opts.dataset_editor_image_columns)
                    txt_selection = gr.HTML(value=get_current_txt_selection())

                    with gr.Row():
                        btn_remove_image_selection = gr.Button(value='Remove selection [Delete]', elem_id='dataset_tag_editor_btn_remove_image_selection')
                        btn_invert_image_selection = gr.Button(value='Invert selection')
                        btn_clear_image_selection = gr.Button(value='Clear selection')

                btn_apply_image_selection_filter = gr.Button(value='Apply selection filter', variant='primary')

            with gr.Tab(label='Batch Edit Captions'):
                with gr.Column(variant='panel'):
                    gr.HTML('Edit common tags.')
                    tb_common_tags = gr.Textbox(label='Common Tags', interactive=False)
                    tb_edit_tags = gr.Textbox(label='Edit Tags', interactive=True)
                    cb_prepend_tags = gr.Checkbox(value=False, label='Prepend additional tags')
                    btn_apply_edit_tags = gr.Button(value='Apply changes to filtered images', variant='primary')
                    with gr.Accordion(label='Show description of how to edit tags', open=False):
                        gr.HTML(value="""
                        1. The tags common to all displayed images are shown in comma separated style.<br>
                        2. When changes are applied, all tags in each displayed images are replaced.<br>
                        3. If you change some tags into blank, they will be erased.<br>
                        4. If you add some tags to the end, they will be added to the end/beginning of the text file.<br>
                        5. Changes are not applied to the text files until the "Save all changes" button is pressed.<br>
                        <b>ex A.</b><br>
                        &emsp;Original Text = "A, A, B, C"&emsp;Common Tags = "B, A"&emsp;Edit Tags = "X, Y"<br>
                        &emsp;Result = "Y, Y, X, C"&emsp;(B->X, A->Y)<br>
                        <b>ex B.</b><br>
                        &emsp;Original Text = "A, B, C"&emsp;Common Tags = "(nothing)"&emsp;Edit Tags = "X, Y"<br>
                        &emsp;Result = "A, B, C, X, Y"&emsp;(add X and Y to the end (default))<br>
                        &emsp;Result = "X, Y, A, B, C"&emsp;(add X and Y to the beginning ("Prepend additional tags" checked))<br>
                        <b>ex C.</b><br>
                        &emsp;Original Text = "A, B, C, D, E"&emsp;Common Tags = "A, B, D"&emsp;Edit Tags = ", X, "<br>
                        &emsp;Result = "X, C, E"&emsp;(A->"", B->X, D->"")<br>
                        """)
                with gr.Column(variant='panel'):
                    gr.HTML('Search and Replace for all images displayed.')
                    tb_sr_search_tags = gr.Textbox(label='Search Text', interactive=True)
                    tb_sr_replace_tags = gr.Textbox(label='Replace Text', interactive=True)
                    cb_use_regex = gr.Checkbox(label='Use regex')
                    rb_sr_replace_target = gr.Radio(['Only Selected Tags', 'Each Tags', 'Entire Caption'], value='Only Selected Tags', label='Search and Replace in', interactive=True)
                    tb_sr_selected_tags = gr.Textbox(label='Selected Tags', interactive=False, lines=2)
                    btn_apply_sr_tags = gr.Button(value='Search and Replace', variant='primary')
                    
            with gr.Tab(label='Edit Caption of Selected Image'):
                with gr.Tab(label='Read Caption from Selected Image'):
                    tb_caption_selected_image = gr.Textbox(label='Caption of Selected Image', interactive=True, lines=6)
                    with gr.Row():
                        btn_copy_caption = gr.Button(value='Copy and Overwrite')
                        btn_prepend_caption = gr.Button(value='Prepend')
                        btn_append_caption = gr.Button(value='Append')
                    
                with gr.Tab(label='Interrogate Selected Image'):
                    with gr.Row():
                        btn_interrogate_clip = gr.Button(value='Interrogate with BLIP')
                        btn_interrogate_booru = gr.Button(value='Interrogate with DeepDanbooru')
                    tb_interrogate_selected_image = gr.Textbox(label='Interrogate Result', interactive=True, lines=6)
                    with gr.Row():
                        btn_copy_interrogate = gr.Button(value='Copy and Overwrite')
                        btn_prepend_interrogate = gr.Button(value='Prepend')
                        btn_append_interrogate = gr.Button(value='Append')

                tb_edit_caption_selected_image = gr.Textbox(label='Edit Caption', interactive=True, lines=6)
                btn_apply_changes_selected_image = gr.Button(value='Apply changes to selected image', variant='primary')

                gr.HTML("""Changes are not applied to the text files until the "Save all changes" button is pressed.""")

            with gr.Tab(label='Move or Delete Files'):
                gr.HTML(value='<b>Note: </b>Moved or deleted images will be unloaded.')
                rb_move_or_delete_target_data = gr.Radio(choices=['Selected One', 'All Displayed Ones'], label='Move or Delete')
                cbg_move_or_delete_target_file = gr.CheckboxGroup(choices=['Image File', 'Caption Text File', 'Caption Backup File'], label='Target')
                ta_move_or_delete_target_dataset_num = gr.HTML(value='Target dataset num: 0')
                tb_move_or_delete_destination_dir = gr.Textbox(label='Destination Directory')
                btn_move_or_delete_move_files = gr.Button(value='Move File(s)', variant='primary')
                btn_move_or_delete_delete_files = gr.Button(value='DELETE File(s)', variant='primary')
        
        #----------------------------------------------------------------
        # Filter and Edit Tags tab
        btn_save_all_changes.click(
            fn=save_all_changes,
            inputs=[cb_backup],
            outputs=[txt_result]
        )

        tag_filter_ui.set_callbacks(
            on_filter_update=lambda:
            update_gallery() +
            update_common_tags() +
            [', '.join(tag_filter_ui.filter.tags)] +
            [get_current_move_or_delete_target_num(rb_move_or_delete_target_data, nb_hidden_image_index)],
            outputs=[gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags] + [tb_sr_selected_tags] + [ta_move_or_delete_target_dataset_num]
        )

        tag_filter_ui_neg.set_callbacks(
            on_filter_update=lambda:
            update_gallery() +
            update_common_tags() +
            [', '.join(tag_filter_ui_neg.filter.tags)] +
            [get_current_move_or_delete_target_num(rb_move_or_delete_target_data, nb_hidden_image_index)],
            outputs=[gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags] + [tb_sr_selected_tags] + [ta_move_or_delete_target_dataset_num]
        )

        btn_load_datasets.click(
            fn=load_files_from_dir,
            inputs=[tb_img_directory, cb_load_recursive, cb_load_caption_from_filename, rb_use_interrogator, cb_use_clip_to_prefill, cb_use_booru_to_prefill],
            outputs=[gl_dataset_images, gl_selected_images, txt_gallery, txt_selection] + [tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )
        btn_load_datasets.click(
            fn=lambda:['', '', '', -1],
            outputs=[tb_common_tags, tb_edit_tags, tb_caption_selected_image, nb_hidden_image_index]
        )

        btn_clear_tag_filters.click(
            fn=clear_tag_filters,
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        btn_clear_all_filters.click(
            fn=clear_image_selection,
            outputs=[gl_selected_images, txt_selection, nb_hidden_selection_image_index]
        )
        btn_clear_all_filters.click(
            fn=clear_tag_filters,
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        #----------------------------------------------------------------
        # Filter by Selection tab

        btn_hidden_set_selection_index.click(
            fn=selection_index_changed,
            _js="(x) => [dataset_tag_editor_gl_selected_images_selected_index()]",
            inputs=[nb_hidden_selection_image_index],
            outputs=[txt_selection, nb_hidden_selection_image_index]
        )

        btn_add_image_selection.click(
            fn=add_image_selection,
            inputs=[nb_hidden_image_index],
            outputs=[gl_selected_images, nb_hidden_image_index]
        )

        btn_add_all_displayed_image_selection.click(
            fn=add_all_displayed_image_selection,
            outputs=gl_selected_images
        )

        btn_invert_image_selection.click(
            fn=invert_image_selection,
            outputs=gl_selected_images
        )

        btn_remove_image_selection.click(
            fn=remove_image_selection,
            inputs=[nb_hidden_selection_image_index],
            outputs=[gl_selected_images, txt_selection, nb_hidden_selection_image_index]
        )

        btn_clear_image_selection.click(
            fn=clear_image_selection,
            outputs=[gl_selected_images, txt_selection, nb_hidden_selection_image_index]
        )

        btn_apply_image_selection_filter.click(
            fn=apply_image_selection_filter,
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        #----------------------------------------------------------------
        # Batch Edit Captions tab

        btn_apply_edit_tags.click(
            fn=apply_edit_tags,
            inputs=[tb_common_tags, tb_edit_tags, cb_prepend_tags],
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        btn_apply_sr_tags.click(
            fn=search_and_replace,
            inputs=[tb_sr_search_tags, tb_sr_replace_tags, rb_sr_replace_target, cb_use_regex],
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        #----------------------------------------------------------------
        # Edit Caption of Selected Image tab

        btn_hidden_set_index.click(
            fn=gallery_index_changed,
            _js="(x) => [dataset_tag_editor_gl_dataset_images_selected_index()]",
            inputs=[nb_hidden_image_index],
            outputs=[tb_caption_selected_image, txt_gallery, nb_hidden_image_index]
        )
        btn_hidden_set_index.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        btn_copy_caption.click(
            fn=lambda a:a,
            inputs=[tb_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_append_caption.click(
            fn=lambda a, b : b + (', ' if a and b else '') + a,
            inputs=[tb_caption_selected_image, tb_edit_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_prepend_caption.click(
            fn=lambda a, b : a + (', ' if a and b else '') + b,
            inputs=[tb_caption_selected_image, tb_edit_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_interrogate_clip.click(
            fn=interrogate_selected_image_clip,
            outputs=[tb_interrogate_selected_image]
        )

        btn_interrogate_booru.click(
            fn=interrogate_selected_image_booru,
            outputs=[tb_interrogate_selected_image]
        )

        btn_copy_interrogate.click(
            fn=lambda a:a,
            inputs=[tb_interrogate_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_append_interrogate.click(
            fn=lambda a, b : b + (', ' if a and b else '') + a,
            inputs=[tb_interrogate_selected_image, tb_edit_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )
        
        btn_prepend_interrogate.click(
            fn=lambda a, b : a + (', ' if a and b else '') + b,
            inputs=[tb_interrogate_selected_image, tb_edit_caption_selected_image],
            outputs=[tb_edit_caption_selected_image]
        )

        btn_apply_changes_selected_image.click(
            fn=change_selected_image_caption,
            inputs=[tb_edit_caption_selected_image, nb_hidden_image_index],
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags] + [nb_hidden_image_index]
        )
        
        btn_apply_changes_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_edit_caption_selected_image],
            outputs=[tb_caption_selected_image]
        )

        #----------------------------------------------------------------
        # Move or Delete Files

        rb_move_or_delete_target_data.change(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        btn_move_or_delete_move_files.click(
            fn=move_files,
            inputs=[rb_move_or_delete_target_data, cbg_move_or_delete_target_file, tb_move_or_delete_destination_dir, nb_hidden_image_index],
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

        btn_move_or_delete_delete_files.click(
            fn=delete_files,
            inputs=[rb_move_or_delete_target_data, cbg_move_or_delete_target_file, nb_hidden_image_index],
            outputs=[tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, gl_dataset_images, nb_hidden_image_index, txt_gallery] + [tb_common_tags, tb_edit_tags]
        )

    return [(dataset_tag_editor_interface, "Dataset Tag Editor", "dataset_tag_editor_interface")]


def on_ui_settings():
    section = ('dataset-tag-editor', "Dataset Tag Editor")
    shared.opts.add_option("dataset_editor_image_columns", shared.OptionInfo(6, "Number of columns on image gallery", section=section))


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
