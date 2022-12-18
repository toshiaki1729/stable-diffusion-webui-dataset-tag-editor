from typing import List, NamedTuple, Type
from modules import shared, script_callbacks, scripts
from modules.shared import opts
import gradio as gr
import json
import os
from collections import namedtuple

from scripts.dataset_tag_editor.dataset_tag_editor import DatasetTagEditor, InterrogateMethod
from scripts.dataset_tag_editor.filters import TagFilter, PathFilter
from scripts.dataset_tag_editor.ui import TagFilterUI, TagSelectUI

dataset_tag_editor = DatasetTagEditor()

path_filter = PathFilter()
tag_filter_ui:TagFilterUI = None
tag_filter_ui_neg:TagFilterUI = None
tag_select_ui_remove:TagSelectUI = None

def get_filters():
    return [path_filter, tag_filter_ui.get_filter(), tag_filter_ui_neg.get_filter()]

total_image_num = 0
displayed_image_num = 0
tmp_selection_img_path_set = set()
gallery_selected_image_path = ''
selection_selected_image_path = ''
show_only_selected_tags = True


# ================================================================
# General Callbacks
# ================================================================

CONFIG_PATH = os.path.join(scripts.basedir(), 'config.json')


GeneralConfig = namedtuple('GeneralConfig', ['backup', 'dataset_dir', 'load_recursive', 'load_caption_from_filename', 'use_interrogator', 'use_clip_to_prefill', 'use_booru_to_prefill', 'use_waifu_to_prefill'])
FilterConfig = namedtuple('FilterConfig', ['sort_by', 'sort_order', 'logic'])
BatchEditConfig = namedtuple('BatchEditConfig', ['show_only_selected', 'prepend', 'use_regex', 'target', 'sory_by', 'sort_order'])
EditSelectedConfig = namedtuple('EditSelectedConfig', ['auto_copy', 'warn_change_not_saved'])
MoveDeleteConfig = namedtuple('MoveDeleteConfig', ['range', 'target', 'destination'])

CFG_GENERAL_DEFAULT = GeneralConfig(True, '', False, True, 'No', False, False, False)
CFG_FILTER_P_DEFAULT = FilterConfig('Alphabetical Order', 'Ascending', 'AND')
CFG_FILTER_N_DEFAULT = FilterConfig('Alphabetical Order', 'Ascending', 'OR')
CFG_BATCH_EDIT_DEFAULT = BatchEditConfig(True, False, False, 'Only Selected Tags', 'Alphabetical Order', 'Ascending')
CFG_EDIT_SELECTED_DEFAULT = EditSelectedConfig(False, False)
CFG_MOVE_DELETE_DEFAULT = MoveDeleteConfig('Selected One', [], '')

class Config:
    def __init__(self):
        self.config = dict()

    def load(self):
        if not os.path.exists(CONFIG_PATH) or not os.path.isfile(CONFIG_PATH):
            self.config = dict()
            return
        with open(CONFIG_PATH, 'r') as f:
            try:
                j = json.load(f) or dict()
            except:
                j = dict()
            self.config = j

    def save(self):
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.config))
    
    def read(self, name: str):
        return self.config.get(name)

    def write(self, cfg: dict, name: str):
        self.config[name] = cfg

config = Config()

def write_general_config(backup: bool, dataset_dir: str, load_recursive: bool, load_caption_from_filename: bool, use_interrogator: str, use_clip_to_prefill: bool, use_booru_to_prefill: bool, use_waifu_to_prefill: bool):
    cfg = GeneralConfig(backup, dataset_dir, load_recursive, load_caption_from_filename, use_interrogator, use_clip_to_prefill, use_booru_to_prefill, use_waifu_to_prefill)
    config.write(cfg._asdict(), 'general')

def write_filter_config(sort_by_p: str, sort_order_p: str, logic_p: str, sort_by_n: str, sort_order_n: str, logic_n: str):
    cfg_p = FilterConfig(sort_by_p, sort_order_p, logic_p)
    cfg_n = FilterConfig(sort_by_n, sort_order_n, logic_n)
    config.write({'positive':cfg_p._asdict(), 'negative':cfg_n._asdict()}, 'filter')

def write_batch_edit_config(show_only_selected: bool, prepend: bool, use_regex: bool, target: str, sort_by: str, sort_order: str):
    cfg = BatchEditConfig(show_only_selected, prepend, use_regex, target, sort_by, sort_order)
    config.write(cfg._asdict(), 'batch_edit')

def write_edit_selected_config(auto_copy: bool, warn_change_not_saved: bool):
    cfg = EditSelectedConfig(auto_copy, warn_change_not_saved)
    config.write(cfg._asdict(), 'edit_selected')

def write_move_delete_config(range: str, target: str, destination: str):
    cfg = MoveDeleteConfig(range, target, destination)
    config.write(cfg._asdict(), 'file_move_delete')

def read_config(name: str, config_type: Type, default: NamedTuple):
    d = config.read(name)
    cfg = default
    if d:
        d = default._asdict() | d
        cfg = config_type(**d)
    return cfg

def read_general_config():
    return read_config('general', GeneralConfig, CFG_GENERAL_DEFAULT)

def read_filter_config():
    d = config.read('filter')
    d_p = d.get('positive') if d else None
    d_n = d.get('negative') if d else None
    cfg_p = CFG_FILTER_P_DEFAULT
    cfg_n = CFG_FILTER_N_DEFAULT
    if d_p:
        d_p = CFG_FILTER_P_DEFAULT._asdict() | d_p
        cfg_p = FilterConfig(**d_p)
    if d_n:
        d_n = CFG_FILTER_N_DEFAULT._asdict() | d_n
        cfg_n = FilterConfig(**d_n)
    return cfg_p, cfg_n

def read_batch_edit_config():
    return read_config('batch_edit', BatchEditConfig, CFG_BATCH_EDIT_DEFAULT)

def read_edit_selected_config():
    return read_config('edit_selected', EditSelectedConfig, CFG_EDIT_SELECTED_DEFAULT)

def read_move_delete_config():
    return read_config('file_move_delete', MoveDeleteConfig, CFG_MOVE_DELETE_DEFAULT)

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

    else:
        return f'Target dataset num: 0'


def load_files_from_dir(dir: str, recursive: bool, load_caption_from_filename: bool, use_interrogator: str, use_clip: bool, use_booru: bool, use_waifu: bool):
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

    dataset_tag_editor.load_dataset(dir, recursive, load_caption_from_filename, interrogate_method, use_booru, use_clip, use_waifu)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=[])
    img_indices = dataset_tag_editor.get_filtered_imgindices(filters=[])
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
    ] +\
    [gr.CheckboxGroup.update(value=[str(i) for i in img_indices], choices=[str(i) for i in img_indices]), True] +\
    clear_tag_filters() +\
    [tag_select_ui_remove.cbg_tags_update()]


def update_gallery():
    global displayed_image_num
    img_indices = dataset_tag_editor.get_filtered_imgindices(filters=get_filters())
    displayed_image_num = len(img_indices)
    return [
        [str(i) for i in img_indices],
        1,
        -1,
        -1,
        -1,
        get_current_gallery_txt()
        ]


def update_filter_and_gallery():
    return \
        [tag_filter_ui.cbg_tags_update(), tag_filter_ui_neg.cbg_tags_update()] +\
        update_gallery() +\
        update_common_tags() +\
        [', '.join(tag_filter_ui.filter.tags)] +\
        [tag_select_ui_remove.cbg_tags_update()]


def clear_tag_filters():
    tag_filter_ui.clear_filter()
    tag_filter_ui_neg.clear_filter()
    return update_filter_and_gallery()


def update_common_tags():
    if show_only_selected_tags:
        tags = ', '.join([t for t in dataset_tag_editor.get_common_tags(filters=get_filters()) if t in tag_filter_ui.filter.tags])
    else:
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
    return update_filter_and_gallery()
    

# ================================================================
# Callbacks for "Edit Caption of Selected Image" tab
# ================================================================

def gallery_index_changed(prev_idx: int, next_idx: int, edit_caption: str, copy_automatically: bool, warn_change_not_saved: bool):
    global gallery_selected_image_path
    prev_idx = int(prev_idx)
    next_idx = int(next_idx)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())
    prev_tags_txt = ''
    if 0 <= prev_idx and prev_idx < len(img_paths):
        prev_tags_txt = ', '.join(dataset_tag_editor.get_tags_by_image_path(gallery_selected_image_path))
    else:
        prev_idx = -1
    
    next_tags_txt = ''
    if 0 <= next_idx and next_idx < len(img_paths):
        gallery_selected_image_path = img_paths[next_idx]
        next_tags_txt = ', '.join(dataset_tag_editor.get_tags_by_image_path(gallery_selected_image_path))
    else:
        gallery_selected_image_path = ''
        
    return\
        [prev_idx if warn_change_not_saved and edit_caption != prev_tags_txt else -1] +\
        [next_tags_txt, next_tags_txt if copy_automatically else edit_caption] +\
        [edit_caption] +\
        [get_current_gallery_txt()]


def dialog_selected_save_caption_change(prev_idx: int, edit_caption: str):
    global gallery_selected_image_path
    prev_idx = int(prev_idx)
    return change_selected_image_caption(edit_caption, prev_idx)


def change_selected_image_caption(tags_text: str, idx: int):
    idx = int(idx)
    img_paths = dataset_tag_editor.get_filtered_imgpaths(filters=get_filters())

    edited_tags = [t.strip() for t in tags_text.split(',')]
    edited_tags = [t for t in edited_tags if t]

    if 0 <= idx and idx < len(img_paths):
        dataset_tag_editor.set_tags_by_image_path(imgpath=img_paths[idx], tags=edited_tags)
    return update_filter_and_gallery()


def interrogate_selected_image_clip():
    global gallery_selected_image_path
    from scripts.dataset_tag_editor.dataset_tag_editor import interrogate_image_clip
    return interrogate_image_clip(gallery_selected_image_path)


def interrogate_selected_image_booru():
    global gallery_selected_image_path
    from scripts.dataset_tag_editor.dataset_tag_editor import interrogate_image_booru
    return interrogate_image_booru(gallery_selected_image_path)


def interrogate_selected_image_waifu():
    global gallery_selected_image_path
    from scripts.dataset_tag_editor.dataset_tag_editor import interrogate_image_waifu
    return interrogate_image_waifu(gallery_selected_image_path)


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

    return update_filter_and_gallery()


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
    
    return update_filter_and_gallery()


def cb_show_only_tags_selected_changed(value: bool):
    global show_only_selected_tags
    show_only_selected_tags = value
    return update_common_tags()


def remove_duplicated_tags():
    dataset_tag_editor.remove_duplicated_tags(get_filters())
    return update_filter_and_gallery()


def remove_selected_tags():
    dataset_tag_editor.remove_tags(tag_select_ui_remove.selected_tags, get_filters())
    return update_filter_and_gallery()


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

    return update_filter_and_gallery()


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

    return update_filter_and_gallery()


# ================================================================
# Script Callbacks
# ================================================================

def on_ui_tabs():
    global tag_filter_ui, tag_filter_ui_neg, tag_select_ui_remove
    config.load()

    cfg_general = read_general_config()
    cfg_filter_p, cfg_filter_n = read_filter_config()
    cfg_batch_edit = read_batch_edit_config()
    cfg_edit_selected = read_edit_selected_config()
    cfg_file_move_delete = read_move_delete_config()

    tag_filter_ui = TagFilterUI(dataset_tag_editor, tag_filter_mode=TagFilter.Mode.INCLUSIVE)
    tag_filter_ui_neg = TagFilterUI(dataset_tag_editor, tag_filter_mode=TagFilter.Mode.EXCLUSIVE)
    tag_select_ui_remove = TagSelectUI(dataset_tag_editor)

    with gr.Blocks(analytics_enabled=False) as dataset_tag_editor_interface:
        with gr.Row(visible=False):
            btn_hidden_set_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_index")
            nb_hidden_image_index = gr.Number(value=-1, label='hidden_idx_next')
            nb_hidden_image_index_prev = gr.Number(value=-1, label='hidden_idx_prev')
            nb_hidden_image_index_save_or_not = gr.Number(value=-1, label='hidden_s_or_n')
            btn_hidden_save_caption = gr.Button(elem_id="dataset_tag_editor_btn_hidden_save_caption")
            tb_hidden_edit_caption = gr.Textbox()
            cbg_hidden_dataset_filter = gr.CheckboxGroup(label='Dataset Filter')
            nb_hidden_dataset_filter_apply = gr.Number(label='Filter Apply', value=-1)

        gr.HTML(value="""
        This extension works well with text captions in comma-separated style (such as the tags generated by DeepBooru interrogator).
        """)
        with gr.Column(variant='panel'):
            with gr.Row():
                with gr.Column(scale=1):
                    btn_save_all_changes = gr.Button(value='Save all changes', variant='primary')
                with gr.Column(scale=2):
                    cb_backup = gr.Checkbox(value=cfg_general.backup, label='Backup original text file (original file will be renamed like filename.000, .001, .002, ...)', interactive=True)
            gr.HTML(value='<b>Note:</b> New text file will be created if you are using filename as captions.')
            with gr.Row(visible=False):
                txt_result = gr.Textbox(label='Results', interactive=False)
        
        with gr.Accordion(label='Reload/Save Settings (config.json)', open=False):
            with gr.Row():
                btn_reload_config_file = gr.Button(value='Reload settings')
                btn_save_setting_as_default = gr.Button(value='Save current settings')
                btn_restore_default = gr.Button(value='Restore settings to default')

        with gr.Row().style(equal_height=False):
            with gr.Column():
                with gr.Column(variant='panel'):
                    with gr.Row():
                        with gr.Column(scale=3):
                            tb_img_directory = gr.Textbox(label='Dataset directory', placeholder='C:\\directory\\of\\datasets', value=cfg_general.dataset_dir)
                        with gr.Column(scale=1, min_width=80):
                            btn_load_datasets = gr.Button(value='Load')
                    with gr.Accordion(label='Dataset Load Settings'):
                        with gr.Row():
                            with gr.Column():
                                cb_load_recursive = gr.Checkbox(value=cfg_general.load_recursive, label='Load from subdirectories')
                                cb_load_caption_from_filename = gr.Checkbox(value=cfg_general.load_caption_from_filename, label='Load caption from filename if no text file exists')
                            with gr.Column():
                                rb_use_interrogator = gr.Radio(choices=['No', 'If Empty', 'Overwrite', 'Prepend', 'Append'], value=cfg_general.use_interrogator, label='Use Interrogator Caption')
                                with gr.Row():
                                    cb_use_clip_to_prefill = gr.Checkbox(value=cfg_general.use_clip_to_prefill, label='Use BLIP')
                                    cb_use_booru_to_prefill = gr.Checkbox(value=cfg_general.use_booru_to_prefill, label='Use DeepDanbooru')
                                    cb_use_waifu_to_prefill = gr.Checkbox(value=cfg_general.use_waifu_to_prefill, label='Use WDv1.4 Tagger')
                
                gl_dataset_images = gr.Gallery(label='Dataset Images', elem_id="dataset_tag_editor_dataset_gallery").style(grid=opts.dataset_editor_image_columns)
                txt_gallery = gr.HTML(value=get_current_gallery_txt())

            with gr.Tab(label='Filter by Tags'):
                with gr.Row():
                        btn_clear_tag_filters = gr.Button(value='Clear tag filters')
                        btn_clear_all_filters = gr.Button(value='Clear ALL filters')

                with gr.Tab(label='Positive Filter'):
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags <b>(INCLUSIVE)</b>')
                        logic_p = TagFilter.Logic.OR if cfg_filter_p.logic=='OR' else TagFilter.Logic.NONE if cfg_filter_p.logic=='NONE' else TagFilter.Logic.AND
                        tag_filter_ui.create_ui(get_filters, logic_p, cfg_filter_p.sort_by, cfg_filter_p.sort_order)

                with gr.Tab(label='Negative Filter'):
                    with gr.Column(variant='panel'):
                        gr.HTML(value='Search tags / Filter images by tags <b>(EXCLUSIVE)</b>')
                        logic_n = TagFilter.Logic.AND if cfg_filter_n.logic=='AND' else TagFilter.Logic.NONE if cfg_filter_n.logic=='NONE' else TagFilter.Logic.OR
                        tag_filter_ui_neg.create_ui(get_filters, logic_n, cfg_filter_n.sort_by, cfg_filter_n.sort_order)
            
            with gr.Tab(label='Filter by Selection'):
                with gr.Row(visible=False):
                    btn_hidden_set_selection_index = gr.Button(elem_id="dataset_tag_editor_btn_hidden_set_selection_index")
                    nb_hidden_selection_image_index = gr.Number(value=-1)
                gr.HTML("""Select images from the left gallery.""")
                
                with gr.Column(variant='panel'):
                    with gr.Row():
                        btn_add_image_selection = gr.Button(value='Add selection [Enter]', elem_id='dataset_tag_editor_btn_add_image_selection')    
                        btn_add_all_displayed_image_selection = gr.Button(value='Add ALL Displayed')    

                    gl_filter_images = gr.Gallery(label='Filter Images', elem_id="dataset_tag_editor_filter_gallery").style(grid=opts.dataset_editor_image_columns)
                    txt_selection = gr.HTML(value=get_current_txt_selection())

                    with gr.Row():
                        btn_remove_image_selection = gr.Button(value='Remove selection [Delete]', elem_id='dataset_tag_editor_btn_remove_image_selection')
                        btn_invert_image_selection = gr.Button(value='Invert selection')
                        btn_clear_image_selection = gr.Button(value='Clear selection')

                btn_apply_image_selection_filter = gr.Button(value='Apply selection filter', variant='primary')

            with gr.Tab(label='Batch Edit Captions'):
                with gr.Tab(label='Search and Replace'):
                    with gr.Column(variant='panel'):
                        gr.HTML('Edit common tags.')
                        cb_show_only_tags_selected = gr.Checkbox(value=cfg_batch_edit.show_only_selected, label='Show only the tags selected in the Positive Filter')
                        tb_common_tags = gr.Textbox(label='Common Tags', interactive=False)
                        tb_edit_tags = gr.Textbox(label='Edit Tags', interactive=True)
                        cb_prepend_tags = gr.Checkbox(value=cfg_batch_edit.prepend, label='Prepend additional tags')
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
                        cb_use_regex = gr.Checkbox(label='Use regex', value=cfg_batch_edit.use_regex)
                        rb_sr_replace_target = gr.Radio(['Only Selected Tags', 'Each Tags', 'Entire Caption'], value=cfg_batch_edit.target, label='Search and Replace in', interactive=True)
                        tb_sr_selected_tags = gr.Textbox(label='Selected Tags', interactive=False, lines=2)
                        btn_apply_sr_tags = gr.Button(value='Search and Replace', variant='primary')
                with gr.Tab(label='Remove'):
                    with gr.Column(variant='panel'):
                        gr.HTML('Remove <b>duplicate</b> tags from the images displayed.')
                        btn_remove_duplicate = gr.Button(value='Remove duplicate tags', variant='primary')
                    with gr.Column(variant='panel'):
                        gr.HTML('Remove <b>selected</b> tags from the images displayed.')
                        btn_remove_selected = gr.Button(value='Remove selected tags', variant='primary')
                        tag_select_ui_remove.create_ui(get_filters, cfg_batch_edit.sory_by, cfg_batch_edit.sort_order)
                    
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
                        btn_interrogate_waifu = gr.Button(value='Interrogate with WDv1.4 tagger')
                    tb_interrogate_selected_image = gr.Textbox(label='Interrogate Result', interactive=True, lines=6)
                    with gr.Row():
                        btn_copy_interrogate = gr.Button(value='Copy and Overwrite')
                        btn_prepend_interrogate = gr.Button(value='Prepend')
                        btn_append_interrogate = gr.Button(value='Append')
                cb_copy_caption_automatically = gr.Checkbox(value=cfg_edit_selected.auto_copy, label='Copy caption from selected images automatically')
                cb_ask_save_when_caption_changed = gr.Checkbox(value=cfg_edit_selected.warn_change_not_saved, label='Warn if changes in caption is not saved')
                tb_edit_caption_selected_image = gr.Textbox(label='Edit Caption', interactive=True, lines=6)
                btn_apply_changes_selected_image = gr.Button(value='Apply changes to selected image', variant='primary')

                gr.HTML("""Changes are not applied to the text files until the "Save all changes" button is pressed.""")

            with gr.Tab(label='Move or Delete Files'):
                gr.HTML(value='<b>Note: </b>Moved or deleted images will be unloaded.')
                rb_move_or_delete_target_data = gr.Radio(choices=['Selected One', 'All Displayed Ones'], value=cfg_file_move_delete.range, label='Move or Delete')
                cbg_move_or_delete_target_file = gr.CheckboxGroup(choices=['Image File', 'Caption Text File', 'Caption Backup File'], label='Target', value=cfg_file_move_delete.target)
                ta_move_or_delete_target_dataset_num = gr.HTML(value='Target dataset num: 0')
                tb_move_or_delete_destination_dir = gr.Textbox(label='Destination Directory', value=cfg_file_move_delete.destination)
                btn_move_or_delete_move_files = gr.Button(value='Move File(s)', variant='primary')
                gr.HTML(value='<b>Note: </b>DELETE cannot be undone. The files will be deleted completely.')
                btn_move_or_delete_delete_files = gr.Button(value='DELETE File(s)', variant='primary')
        
        o_filter_and_gallery = \
            [tag_filter_ui.cbg_tags, tag_filter_ui_neg.cbg_tags, cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply, nb_hidden_image_index, nb_hidden_image_index_prev, nb_hidden_image_index_save_or_not, txt_gallery] +\
            [tb_common_tags, tb_edit_tags] +\
            [tb_sr_selected_tags] +\
            [tag_select_ui_remove.cbg_tags]

        #----------------------------------------------------------------
        # General

        configurable_components = \
            [cb_backup, tb_img_directory, cb_load_recursive, cb_load_caption_from_filename, rb_use_interrogator, cb_use_clip_to_prefill, cb_use_booru_to_prefill, cb_use_waifu_to_prefill] +\
            [tag_filter_ui.rb_sort_by, tag_filter_ui.rb_sort_order, tag_filter_ui.rb_logic, tag_filter_ui_neg.rb_sort_by, tag_filter_ui_neg.rb_sort_order, tag_filter_ui_neg.rb_logic] +\
            [cb_show_only_tags_selected, cb_prepend_tags, cb_use_regex, rb_sr_replace_target, tag_select_ui_remove.rb_sort_by, tag_select_ui_remove.rb_sort_order] +\
            [cb_copy_caption_automatically, cb_ask_save_when_caption_changed] +\
            [rb_move_or_delete_target_data, cbg_move_or_delete_target_file, tb_move_or_delete_destination_dir]
        
        def reload_config_file():
            config.load()
            p, n = read_filter_config()
            return read_general_config() + p + n + read_batch_edit_config() + read_edit_selected_config() + read_move_delete_config()

        btn_reload_config_file.click(
            fn=reload_config_file,
            outputs=configurable_components
        )

        def save_settings_callback(*a):
            write_general_config(*a[:8])
            write_filter_config(*a[8:14])
            write_batch_edit_config(*a[14:20])
            write_edit_selected_config(*a[20:22])
            write_move_delete_config(*a[22:])
            config.save()

        btn_save_setting_as_default.click(
            fn=save_settings_callback,
            inputs=configurable_components
        )

        def restore_default_settings():
            write_general_config(*CFG_GENERAL_DEFAULT)
            write_filter_config(*CFG_FILTER_P_DEFAULT, *CFG_FILTER_N_DEFAULT)
            write_batch_edit_config(*CFG_BATCH_EDIT_DEFAULT)
            write_edit_selected_config(*CFG_EDIT_SELECTED_DEFAULT)
            write_move_delete_config(*CFG_MOVE_DELETE_DEFAULT)
            return CFG_GENERAL_DEFAULT + CFG_FILTER_P_DEFAULT + CFG_FILTER_N_DEFAULT + CFG_BATCH_EDIT_DEFAULT + CFG_EDIT_SELECTED_DEFAULT + CFG_MOVE_DELETE_DEFAULT
            

        btn_restore_default.click(
            fn=restore_default_settings,
            outputs=configurable_components
        )


        #----------------------------------------------------------------
        # Filter and Edit Tags tab

        btn_save_all_changes.click(
            fn=save_all_changes,
            inputs=[cb_backup],
            outputs=[txt_result]
        )

        tag_filter_ui.set_callbacks(
            on_filter_update=lambda a, b:
            update_gallery() +
            update_common_tags() +
            [', '.join(tag_filter_ui.filter.tags)] +
            [get_current_move_or_delete_target_num(a, b)] +
            [tag_select_ui_remove.cbg_tags_update()],
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=
            [cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply, nb_hidden_image_index, nb_hidden_image_index_prev, nb_hidden_image_index_save_or_not, txt_gallery] +
            [tb_common_tags, tb_edit_tags] +
            [tb_sr_selected_tags] +
            [ta_move_or_delete_target_dataset_num]+
            [tag_select_ui_remove.cbg_tags]
        )

        tag_filter_ui_neg.set_callbacks(
            on_filter_update=lambda a, b:
            update_gallery() +
            update_common_tags() +
            [get_current_move_or_delete_target_num(a, b)] +
            [tag_select_ui_remove.cbg_tags_update()],
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=
            [cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply, nb_hidden_image_index, nb_hidden_image_index_prev, nb_hidden_image_index_save_or_not, txt_gallery] +
            [tb_common_tags, tb_edit_tags] +
            [ta_move_or_delete_target_dataset_num] +
            [tag_select_ui_remove.cbg_tags]
        )

        btn_load_datasets.click(
            fn=load_files_from_dir,
            inputs=[tb_img_directory, cb_load_recursive, cb_load_caption_from_filename, rb_use_interrogator, cb_use_clip_to_prefill, cb_use_booru_to_prefill, cb_use_waifu_to_prefill],
            outputs=
            [gl_dataset_images, gl_filter_images, txt_gallery, txt_selection] +
            [cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply] +
            o_filter_and_gallery
        )
        btn_load_datasets.click(
            fn=lambda:['', '', '', -1, -1, -1],
            outputs=[tb_common_tags, tb_edit_tags, tb_caption_selected_image, nb_hidden_image_index, nb_hidden_image_index_prev, nb_hidden_image_index_save_or_not]
        )

        nb_hidden_dataset_filter_apply.change(
            fn=lambda a, b: [a, b],
            _js='(x, y) => [y>=0 ? dataset_tag_editor_gl_dataset_images_filter(x) : x, -1]',
            inputs=[cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply],
            outputs=[cbg_hidden_dataset_filter, nb_hidden_dataset_filter_apply]
        )

        btn_clear_tag_filters.click(
            fn=clear_tag_filters,
            outputs=o_filter_and_gallery
        )
        btn_clear_tag_filters.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        btn_clear_all_filters.click(
            fn=clear_image_selection,
            outputs=[gl_filter_images, txt_selection, nb_hidden_selection_image_index]
        )
        btn_clear_all_filters.click(
            fn=clear_tag_filters,
            outputs=o_filter_and_gallery
        )
        btn_clear_all_filters.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        #----------------------------------------------------------------
        # Filter by Selection tab

        btn_hidden_set_selection_index.click(
            fn=selection_index_changed,
            _js="(x) => [dataset_tag_editor_gl_filter_images_selected_index()]",
            inputs=[nb_hidden_selection_image_index],
            outputs=[txt_selection, nb_hidden_selection_image_index]
        )

        btn_add_image_selection.click(
            fn=add_image_selection,
            inputs=[nb_hidden_image_index],
            outputs=[gl_filter_images, nb_hidden_image_index]
        )

        btn_add_all_displayed_image_selection.click(
            fn=add_all_displayed_image_selection,
            outputs=gl_filter_images
        )

        btn_invert_image_selection.click(
            fn=invert_image_selection,
            outputs=gl_filter_images
        )

        btn_remove_image_selection.click(
            fn=remove_image_selection,
            inputs=[nb_hidden_selection_image_index],
            outputs=[gl_filter_images, txt_selection, nb_hidden_selection_image_index]
        )

        btn_clear_image_selection.click(
            fn=clear_image_selection,
            outputs=[gl_filter_images, txt_selection, nb_hidden_selection_image_index]
        )

        btn_apply_image_selection_filter.click(
            fn=apply_image_selection_filter,
            outputs=o_filter_and_gallery
        )
        btn_apply_image_selection_filter.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        #----------------------------------------------------------------
        # Batch Edit Captions tab

        btn_apply_edit_tags.click(
            fn=apply_edit_tags,
            inputs=[tb_common_tags, tb_edit_tags, cb_prepend_tags],
            outputs=o_filter_and_gallery
        )
        btn_apply_edit_tags.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        btn_apply_sr_tags.click(
            fn=search_and_replace,
            inputs=[tb_sr_search_tags, tb_sr_replace_tags, rb_sr_replace_target, cb_use_regex],
            outputs=o_filter_and_gallery
        )
        btn_apply_sr_tags.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        cb_show_only_tags_selected.change(
            fn=cb_show_only_tags_selected_changed,
            inputs=cb_show_only_tags_selected,
            outputs=[tb_common_tags, tb_edit_tags]
        )

        btn_remove_duplicate.click(
            fn=remove_duplicated_tags,
            outputs=o_filter_and_gallery
        )

        tag_select_ui_remove.set_callbacks()

        btn_remove_selected.click(
            fn=remove_selected_tags,
            outputs=o_filter_and_gallery
        )

        #----------------------------------------------------------------
        # Edit Caption of Selected Image tab

        btn_hidden_set_index.click(
            fn=lambda x, y:[x, y],
            _js="(x, y) => [dataset_tag_editor_gl_dataset_images_selected_index(), x]",
            inputs=[nb_hidden_image_index, nb_hidden_image_index_prev],
            outputs=[nb_hidden_image_index, nb_hidden_image_index_prev]
        )
        
        nb_hidden_image_index.change(
            fn=gallery_index_changed,
            inputs=[nb_hidden_image_index_prev, nb_hidden_image_index, tb_edit_caption_selected_image, cb_copy_caption_automatically, cb_ask_save_when_caption_changed],
            outputs=[nb_hidden_image_index_save_or_not] + [tb_caption_selected_image, tb_edit_caption_selected_image] + [tb_hidden_edit_caption] + [txt_gallery]
        )

        nb_hidden_image_index_save_or_not.change(
            fn=lambda a:None,
            _js='(a) => dataset_tag_editor_ask_save_change_or_not(a)',
            inputs=nb_hidden_image_index_save_or_not
        )

        btn_hidden_save_caption.click(
            fn=lambda iprev, e, t, inext: dialog_selected_save_caption_change(iprev, e) + [get_current_move_or_delete_target_num(t, inext)],
            inputs=[nb_hidden_image_index_prev, tb_hidden_edit_caption] + [rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=o_filter_and_gallery + [ta_move_or_delete_target_dataset_num]
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

        btn_interrogate_waifu.click(
            fn=interrogate_selected_image_waifu,
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
            outputs=o_filter_and_gallery
        )
        btn_apply_changes_selected_image.click(
            fn=lambda a:a,
            inputs=[tb_edit_caption_selected_image],
            outputs=[tb_caption_selected_image]
        )
        btn_apply_changes_selected_image.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
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
            outputs=o_filter_and_gallery
        )
        btn_move_or_delete_move_files.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

        btn_move_or_delete_delete_files.click(
            fn=delete_files,
            inputs=[rb_move_or_delete_target_data, cbg_move_or_delete_target_file, nb_hidden_image_index],
            outputs=o_filter_and_gallery
        )
        btn_move_or_delete_delete_files.click(
            fn=get_current_move_or_delete_target_num,
            inputs=[rb_move_or_delete_target_data, nb_hidden_image_index],
            outputs=[ta_move_or_delete_target_dataset_num]
        )

    return [(dataset_tag_editor_interface, "Dataset Tag Editor", "dataset_tag_editor_interface")]


def on_ui_settings():
    section = ('dataset-tag-editor', "Dataset Tag Editor")
    shared.opts.add_option("dataset_editor_image_columns", shared.OptionInfo(6, "Number of columns on image gallery", section=section))


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
