from scripts.dataset_tag_editor.filters import TagFilter
from scripts.dataset_tag_editor.dataset_tag_editor import DatasetTagEditor
from scripts.dataset_tag_editor.dataset import Dataset
from typing import List, Callable

class TagFilterUI:
    def __init__(self, dataset_tag_editor: DatasetTagEditor, tag_filter_logic: TagFilter.Mode = TagFilter.Logic.AND, tag_filter_mode: TagFilter.Mode = TagFilter.Mode.INCLUSIVE):
        self.logic = tag_filter_logic
        self.filter_word = ''
        self.sort_by = 'Alphabetical Order'
        self.sort_order = 'Ascending'
        self.selected_tags = []
        self.filter_mode = tag_filter_mode
        self.filter = TagFilter({}, self.logic, self.filter_mode)
        self.dataset_tag_editor = dataset_tag_editor
        self.get_filters = lambda:[]
    
    def get_filter(self):
        return self.filter

    def create_ui(self, get_filters: Callable[[], List[Dataset.Filter]]):
        self.get_filters = get_filters

        import gradio as gr
        self.tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
        with gr.Row():
            self.rd_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value='Alphabetical Order', interactive=True, label='Sort by')
            self.rd_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value='Ascending', interactive=True, label='Sort Order')
        self.rd_logic = gr.Radio(choices=['AND', 'OR', 'NONE'], value='AND', label='Filter Logic', interactive=True)
        self.cbg_tags = gr.CheckboxGroup(label='Filter Images by Tags', interactive=True)
    

    def set_callbacks(self, on_filter_update: Callable[[], List] = lambda:[], outputs=None):
        self.tb_search_tags.change(fn=self.tb_search_tags_changed, inputs=self.tb_search_tags, outputs=self.cbg_tags)
        self.rd_sort_by.change(fn=self.rd_sort_by_changed, inputs=self.rd_sort_by, outputs=self.cbg_tags)
        self.rd_sort_order.change(fn=self.rd_sort_order_changed, inputs=self.rd_sort_order, outputs=self.cbg_tags)
        self.rd_logic.change(fn=lambda a:[self.rd_logic_changed(a)] + on_filter_update(), inputs=self.rd_logic, outputs=[self.cbg_tags] + outputs)
        self.cbg_tags.change(fn=lambda a:[self.cbg_tags_changed(a)] + on_filter_update(), inputs=self.cbg_tags, outputs=[self.cbg_tags] + outputs)


    def tb_search_tags_changed(self, tb_search_tags: str):
        self.filter_word = tb_search_tags
        return self.cbg_tags_update()


    def rd_sort_by_changed(self, rb_sort_by: str):
        self.sort_by = rb_sort_by
        return self.cbg_tags_update()


    def rd_sort_order_changed(self, rd_sort_order: str):
        self.sort_order = rd_sort_order
        return self.cbg_tags_update()


    def rd_logic_changed(self, rd_logic: str):
        self.logic = TagFilter.Logic.AND if rd_logic == 'AND' else TagFilter.Logic.OR if rd_logic == 'OR' else TagFilter.Logic.NONE
        self.filter = TagFilter(set(self.selected_tags), self.logic, self.filter_mode)
        return self.cbg_tags_update()


    def cbg_tags_changed(self, cbg_tags: List[str]):
        self.selected_tags = self.dataset_tag_editor.read_tags(cbg_tags)
        self.filter = TagFilter(set(self.selected_tags), self.logic, self.filter_mode)
        return self.cbg_tags_update()


    def cbg_tags_update(self):
        if self.filter_mode == TagFilter.Mode.INCLUSIVE:
            filtered_tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, self.filter.logic == TagFilter.Logic.AND)
        else:
            filtered_tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, self.filter.logic == TagFilter.Logic.OR)
        tags = self.dataset_tag_editor.sort_tags(tags=filtered_tags, sort_by=self.sort_by, sort_order=self.sort_order)
        tags_in_filter = self.dataset_tag_editor.sort_tags(tags=list(self.filter.tags), sort_by=self.sort_by, sort_order=self.sort_order)
        tags = tags_in_filter + [tag for tag in tags if tag not in self.filter.tags]
        tags = self.dataset_tag_editor.write_tags(tags)
        tags_in_filter = self.dataset_tag_editor.write_tags(tags_in_filter)

        import gradio as gr
        return gr.CheckboxGroup.update(value=tags_in_filter, choices=tags)


    def clear_filter(self):
        self.filter = TagFilter({}, self.logic, self.filter_mode)
        self.filter_word = ''
        self.selected_tags = []