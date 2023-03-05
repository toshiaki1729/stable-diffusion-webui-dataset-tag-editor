from .ui_classes import *

__all__ = [
    'toprow', 'load_dataset', 'dataset_gallery', 'gallery_state', 'filter_by_tags', 'filter_by_selection', 'batch_edit_captions', 'edit_caption_of_selected_image', 'move_or_delete_files'
]

toprow = ToprowUI.get_instance()
load_dataset = LoadDatasetUI.get_instance()
dataset_gallery = DatasetGalleryUI.get_instance()
gallery_state = GalleryStateUI.get_instance()
filter_by_tags = FilterByTagsUI.get_instance()
filter_by_selection = FilterBySelectionUI.get_instance()
batch_edit_captions = BatchEditCaptionsUI.get_instance()
edit_caption_of_selected_image = EditCaptionOfSelectedImageUI.get_instance()
move_or_delete_files = MoveOrDeleteFilesUI.get_instance()
