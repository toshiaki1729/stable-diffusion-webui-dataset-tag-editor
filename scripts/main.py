from typing import List
from modules import shared, script_callbacks
from modules.shared import opts, cmd_opts
import gradio as gr
from scripts.dataset_tag_editor.dataset_tag_editor import DatasetTagEditor, interrogate_image_clip, interrogate_image_booru, InterrogateMethod
from scripts.dataset_tag_editor.filters import TagFilter, PathFilter

dataset_tag_editor = DatasetTagEditor()
tag_filter = TagFilter()
tag_filter_neg = TagFilter()
path_filter = PathFilter()

total_image_num = 0
displayed_image_num = 0
current_selection = 0
tmp_selection_img_path_set = set()
gallery_selected_image_path = ''
selection_selected_image_path = ''

# ================================================================
# Callbacks for "Filter and Edit Tags" tab
# ================================================================

def arrange_tag_order(tags: List[str], sort_by: str, sort_order: str) -> List[str]:
    tags = dataset_tag_editor.sort_tags(tags=tags, sort_by=sort_by, sort_order=sort_order)
    tags_in_filter = [tag for tag in tags if tag in tag_filter.tags]
    tags = tags_in_filter + [tag for tag in tags if tag not in tag_filter.tags]
    return tags


def get_current_txt_filter():
    return f"""
    Displayed Images : {displayed_image_num} / {total_image_num} total<br>
    Current Tag Filter : {tag_filter} {'' if not tag_filter_neg.tags else f'AND {tag_filter_neg}'}<br>
    Current Selection Filter : {current_selection} images<br>
    Selected Image : {gallery_selected_image_path}
    """


def get_current_txt_selection():
    return f"""Selected Image : {selection_selected_image_path}"""


def load_files_from_dir(dir: str, sort_by: str, sort_order: str, recursive: bool, load_caption_from_filename: bool, use_interrogator: str, use_clip: bool, use_booru: bool):
    global total_image_num, displayed_image_num, current_selection, tmp_selection_img_path_set, gallery_selected_image_path, selection_selected_image_path, tag_filter, tag_filter_neg, path_filter
    
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
    img_paths, tags = dataset_tag_editor.get_filtered_imgpath_and_tags()
    tag_filter = TagFilter()
    tag_filter_neg = TagFilter()
    path_filter = PathFilter()
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    total_image_num = displayed_image_num = len(dataset_tag_editor.get_img_path_set())
    tmp_selection_img_path_set = set()
    current_selection = 0
    gallery_selected_image_path = ''
    selection_selected_image_path = ''
    return [
        img_paths,
        [],
        gr.CheckboxGroup.update(value=None, choices=dataset_tag_editor.write_tags(tags)),
        '',
        get_current_txt_filter(),
        get_current_txt_selection()
    ]


def search_tags(filter_word: str, sort_by: str, sort_order: str):
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[path_filter, tag_filter, tag_filter_neg], filter_word=filter_word)
    tags = arrange_tag_order(tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def clear_tag_filters(sort_by, sort_order):
    global tag_filter
    tag_filter = TagFilter()
    return filter_gallery(filter_word='', sort_by=sort_by, sort_order=sort_order) + ['']


def rearrange_tag_order(filter_word: str, sort_by: str, sort_order: str):
    _, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[path_filter, tag_filter, tag_filter_neg], filter_word=filter_word)
    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    return gr.CheckboxGroup.update(choices=dataset_tag_editor.write_tags(tags))


def filter_gallery_by_checkbox(filter_tags: List[str], filter_word: str, sort_by: str, sort_order: str):
    global tag_filter
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    tag_filter = TagFilter(set(filter_tags), TagFilter.Logic.AND, TagFilter.Mode.INCLUSIVE)
    return filter_gallery(filter_word=filter_word, sort_by=sort_by, sort_order=sort_order)


def filter_gallery(filter_word: str, sort_by: str, sort_order: str):
    global displayed_image_num, current_selection
    img_paths, tags = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[path_filter, tag_filter, tag_filter_neg], filter_word=filter_word)

    tags = arrange_tag_order(tags=tags, sort_by=sort_by, sort_order=sort_order)
    filter_tags = [tag for tag in tags if tag in tag_filter.tags]
    tags = dataset_tag_editor.write_tags(tags)
    filter_tags = dataset_tag_editor.write_tags(filter_tags)

    displayed_image_num = len(img_paths)
    current_selection = len(tmp_selection_img_path_set)
    tag_txt = ', '.join(tag_filter.tags)
    
    if filter_tags and len(filter_tags) == 0:
        filter_tags = None
    return [
        img_paths,
        gr.CheckboxGroup.update(value=filter_tags, choices=tags),
        tag_txt,
        tag_txt,
        -1,
        get_current_txt_filter()
        ]


def apply_edit_tags(filter_tags: str, edit_tags: str, prepend: bool, filter_word: str, sort_by: str, sort_order: str):
    global tag_filter
    replace_tags = [t.strip() for t in edit_tags.split(',')]
    filter_tags = dataset_tag_editor.read_tags(filter_tags)
    tag_filter = TagFilter(set(filter_tags), TagFilter.Logic.AND, TagFilter.Mode.INCLUSIVE)
    dataset_tag_editor.replace_tags(search_tags = filter_tags, replace_tags = replace_tags, filters = [path_filter, tag_filter, tag_filter_neg], prepend = prepend)
    tag_filter = TagFilter({t for t in replace_tags if t}, TagFilter.Logic.AND, TagFilter.Mode.INCLUSIVE)
    return filter_gallery(filter_word = filter_word, sort_by=sort_by, sort_order=sort_order)


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
    return [get_current_txt_selection(), idx]


def add_image_selection(idx: int):
    global tmp_selection_img_path_set
    idx = int(idx)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[tag_filter, tag_filter_neg])
    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        tmp_selection_img_path_set.add(img_paths[idx])
    return [arrange_selection_order(tmp_selection_img_path_set), idx]


def add_all_displayed_image_selection():
    global tmp_selection_img_path_set
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[tag_filter, tag_filter_neg])
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


def apply_image_selection_filter(filter_word: str, sort_by: str, sort_order: str):
    global path_filter
    if len(tmp_selection_img_path_set) > 0:
        path_filter = PathFilter(tmp_selection_img_path_set, PathFilter.Mode.INCLUSIVE)
    else:
        path_filter = PathFilter()
    return filter_gallery(filter_word=filter_word, sort_by=sort_by, sort_order=sort_order)
    

# ================================================================
# Callbacks for "Edit Caption of Selected Image" tab
# ================================================================

def gallery_index_changed(idx: int):
    global gallery_selected_image_path
    idx = int(idx)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[tag_filter, tag_filter_neg])
    tags_txt = ''
    if 0 <= idx and idx < len(img_paths):
        gallery_selected_image_path = img_paths[idx]
        tags_txt = ', '.join(dataset_tag_editor.get_tags_by_image_path(gallery_selected_image_path))
    else:
        gallery_selected_image_path = ''
        idx = -1
    
    return [
        tags_txt,
        get_current_txt_filter(),
        idx
        ]


def change_tags_selected_image(tags_text: str, filter_word:str, sort_by: str, sort_order: str, idx: int):
    idx = int(idx)
    img_paths, _ = dataset_tag_editor.get_filtered_imgpath_and_tags(filters=[tag_filter, tag_filter_neg])

    edited_tags = [t.strip() for t in tags_text.split(',')]

    if idx < 0 or len(img_paths) <= idx:
        idx = -1
    else:
        dataset_tag_editor.set_tags_by_image_path(imgpath=img_paths[idx], tags=edited_tags)
    return filter_gallery(filter_word=filter_word, sort_by=sort_by, sort_order=sort_order) + [idx]

def interrogate_selected_image_clip():
    global gallery_selected_image_path
    return interrogate_image_clip(gallery_selected_image_path)

def interrogate_selected_image_booru():
    global gallery_selected_image_path
    return interrogate_image_booru(gallery_selected_image_path)


# ================================================================
# Script Callbacks
# ================================================================

def on_ui_tabs():
    global displayed_image_num, total_image_num, current_selection, gallery_selected_image_path, selection_selected_image_path
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
                txt_filter = gr.HTML(value=get_current_txt_filter())

            with gr.Tab(label='Filter and Edit Tags'):
                with gr.Column():
                    with gr.Row():
                        btn_clear_tag_filters = gr.Button(value='Clear tag filters')
                        btn_clear_all_filters = gr.Button(value='Clear ALL filters')
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Edit tags in filtered images (=displayed images)')
                        tb_selected_tags = gr.Textbox(label='Selected Tags', interactive=False)
                        tb_edit_tags = gr.Textbox(label='Edit Tags', interactive=True)
                        cb_prepend_tags = gr.Checkbox(value=False, label='Prepend additional tags')
                        btn_apply_edit_tags = gr.Button(value='Apply changes to filtered images', variant='primary')
                        with gr.Accordion(label='Show description of how to edit tags', open=False):
                            gr.HTML(value="""
                            1. The selected tags are displayed in comma separated style.<br>
                            2. When changes are applied, all tags in each displayed images are replaced.<br>
                            3. If you change some tags into blank, they will be erased.<br>
                            4. If you add some tags to the end, they will be added to the end/beginning of the text file.<br>
                            5. Changes are not applied to the text files until the "Save all changes" button is pressed.<br>
                            <b>ex A.</b><br>
                            &emsp;Original Text = "A, A, B, C"&emsp;Selected Tags = "B, A"&emsp;Edit Tags = "X, Y"<br>
                            &emsp;Result = "Y, Y, X, C"&emsp;(B->X, A->Y)<br>
                            <b>ex B.</b><br>
                            &emsp;Original Text = "A, B, C"&emsp;Selected Tags = "(nothing)"&emsp;Edit Tags = "X, Y"<br>
                            &emsp;Result = "A, B, C, X, Y"&emsp;(add X and Y to the end (default))<br>
                            &emsp;Result = "X, Y, A, B, C"&emsp;(add X and Y to the beginning ("Prepend additional tags" checked))<br>
                            <b>ex C.</b><br>
                            &emsp;Original Text = "A, B, C, D, E"&emsp;Selected Tags = "A, B, D"&emsp;Edit Tags = ", X, "<br>
                            &emsp;Result = "X, C, E"&emsp;(A->"", B->X, D->"")<br>
                            """)
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags')
                        tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
                        with gr.Row():
                            rd_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value='Alphabetical Order', interactive=True, label='Sort by')
                            rd_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value='Ascending', interactive=True, label='Sort Order')
                        cbg_tags = gr.CheckboxGroup(label='Filter Images by Tags', interactive=True)
            
            with gr.Tab(label='Filter by Selection'):
                with gr.Row(visible=False):
                    btn_hidden_set_selection_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_selection_index")
                    nb_hidden_selection_image_index = gr.Number(value=-1)
                gr.HTML("""Select images from the left gallery.""")
                
                with gr.Column(variant='panel'):
                    with gr.Row():
                        btn_add_image_selection = gr.Button(value='Add selection [Enter]', elem_id='dataset_tag_editor_btn_add_image_selection')    
                        btn_add_all_displayed_image_selection = gr.Button(value='Add ALL')    

                    gl_selected_images = gr.Gallery(label='Filter Images', elem_id="dataset_tag_editor_selection_gallery").style(grid=opts.dataset_editor_image_columns)
                    txt_selection = gr.HTML(value=get_current_txt_selection())

                    with gr.Row():
                        btn_remove_image_selection = gr.Button(value='Remove selection [Delete]', elem_id='dataset_tag_editor_btn_remove_image_selection')
                        btn_invert_image_selection = gr.Button(value='Invert selection')
                        btn_clear_image_selection = gr.Button(value='Clear selection')

                btn_apply_image_selection_filter = gr.Button(value='Apply selection filter', variant='primary')
                    
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
        
        #----------------------------------------------------------------
        # Filter and Edit Tags tab
        btn_save_all_changes.click(
            fn=save_all_changes,
            inputs=[cb_backup],
            outputs=[txt_result]
        )

        btn_load_datasets.click(
            fn=load_files_from_dir,
            inputs=[tb_img_directory, rd_sort_by, rd_sort_order, cb_load_recursive, cb_load_caption_from_filename, rb_use_interrogator, cb_use_clip_to_prefill, cb_use_booru_to_prefill],
            outputs=[gl_dataset_images, gl_selected_images, cbg_tags, tb_search_tags, txt_filter, txt_selection]
        )
        btn_load_datasets.click(
            fn=lambda:['', '', '',  -1],
            inputs=None,
            outputs=[tb_selected_tags, tb_edit_tags, tb_caption_selected_image, nb_hidden_image_index]
        )

        cbg_tags.change(
            fn=filter_gallery_by_checkbox,
            inputs=[cbg_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter]
        )

        rd_sort_by.change(
            fn=rearrange_tag_order,
            inputs=[tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        rd_sort_order.change(
            fn=rearrange_tag_order,
            inputs=[tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        tb_search_tags.change(
            fn=search_tags,
            inputs=[tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=cbg_tags
        )

        btn_apply_edit_tags.click(
            fn=apply_edit_tags,
            inputs=[cbg_tags, tb_edit_tags, cb_prepend_tags, tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter]
        )

        btn_clear_tag_filters.click(
            fn=clear_tag_filters,
            inputs=[rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter, tb_search_tags]
        )

        btn_clear_all_filters.click(
            fn=clear_image_selection,
            inputs=None,
            outputs=[gl_selected_images, txt_selection, nb_hidden_selection_image_index]
        )

        btn_clear_all_filters.click(
            fn=clear_tag_filters,
            inputs=[rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter, tb_search_tags]
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
            inputs=None,
            outputs=gl_selected_images
        )

        btn_invert_image_selection.click(
            fn=invert_image_selection,
            inputs=None,
            outputs=gl_selected_images
        )

        btn_remove_image_selection.click(
            fn=remove_image_selection,
            inputs=[nb_hidden_selection_image_index],
            outputs=[gl_selected_images,txt_selection,nb_hidden_selection_image_index]
        )

        btn_clear_image_selection.click(
            fn=clear_image_selection,
            inputs=None,
            outputs=[gl_selected_images,txt_selection,nb_hidden_selection_image_index]
        )

        btn_apply_image_selection_filter.click(
            fn=apply_image_selection_filter,
            inputs=[tb_search_tags, rd_sort_by, rd_sort_order],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter]
        )

        #----------------------------------------------------------------
        # Edit Caption of Selected Image tab

        btn_hidden_set_index.click(
            fn=gallery_index_changed,
            _js="(x) => [dataset_tag_editor_gl_dataset_images_selected_index()]",
            inputs=[nb_hidden_image_index],
            outputs=[tb_caption_selected_image, txt_filter, nb_hidden_image_index]
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
            inputs=None,
            outputs=[tb_interrogate_selected_image]
        )

        btn_interrogate_booru.click(
            fn=interrogate_selected_image_booru,
            inputs=None,
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
            fn=change_tags_selected_image,
            inputs=[tb_edit_caption_selected_image, tb_search_tags, rd_sort_by, rd_sort_order, nb_hidden_image_index],
            outputs=[gl_dataset_images, cbg_tags, tb_selected_tags, tb_edit_tags, nb_hidden_image_index, txt_filter, nb_hidden_image_index]
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
