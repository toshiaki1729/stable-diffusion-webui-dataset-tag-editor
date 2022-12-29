from typing import List, Callable

import scripts.settings as settings
if settings.DEVELOP:
    import scripts.dataset_tag_editor.filters as filters
    import scripts.dataset_tag_editor.dataset_tag_editor as dte
    import scripts.dataset_tag_editor.dataset as ds
else:
    from scripts.dynamic_import import dynamic_import
    dte = dynamic_import('scripts/dataset_tag_editor/dataset_tag_editor.py')
    filters = dynamic_import('scripts/dataset_tag_editor/filters.py')
    ds = dynamic_import('scripts/dataset_tag_editor/dataset.py')


class TagFilterUI:
    def __init__(self, dataset_tag_editor: dte.DatasetTagEditor, tag_filter_mode: filters.TagFilter.Mode = filters.TagFilter.Mode.INCLUSIVE):
        self.logic = filters.TagFilter.Logic.AND
        self.filter_word = ''
        self.sort_by = 'Alphabetical Order'
        self.sort_order = 'Ascending'
        self.selected_tags = []
        self.filter_mode = tag_filter_mode
        self.filter = filters.TagFilter({}, self.logic, self.filter_mode)
        self.dataset_tag_editor = dataset_tag_editor
        self.get_filters = lambda:[]
    
    def get_filter(self):
        return self.filter

    def create_ui(self, get_filters: Callable[[], List[ds.Dataset.Filter]], logic = filters.TagFilter.Logic.AND, sort_by = 'Alphabetical Order', sort_order = 'Ascending'):
        self.get_filters = get_filters
        self.logic = logic
        self.filter = filters.TagFilter({}, self.logic, self.filter_mode)

        import gradio as gr
        self.tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
        with gr.Row():
            self.rb_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value=sort_by, interactive=True, label='Sort by')
            self.rb_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value=sort_order, interactive=True, label='Sort Order')
        v = 'AND' if self.logic==filters.TagFilter.Logic.AND else 'OR' if self.logic==filters.TagFilter.Logic.OR else 'NONE'
        self.rb_logic = gr.Radio(choices=['AND', 'OR', 'NONE'], value=v, label='Filter Logic', interactive=True)
        self.cbg_tags = gr.CheckboxGroup(label='Filter Images by Tags', interactive=True)
    

    def set_callbacks(self, on_filter_update: Callable[[List], List] = lambda:[], inputs=[], outputs=[]):
        self.tb_search_tags.change(fn=self.tb_search_tags_changed, inputs=self.tb_search_tags, outputs=self.cbg_tags)
        self.rb_sort_by.change(fn=self.rd_sort_by_changed, inputs=self.rb_sort_by, outputs=self.cbg_tags)
        self.rb_sort_order.change(fn=self.rd_sort_order_changed, inputs=self.rb_sort_order, outputs=self.cbg_tags)
        self.rb_logic.change(fn=lambda a, *b:[self.rd_logic_changed(a)] + on_filter_update(*b), inputs=[self.rb_logic] + inputs, outputs=[self.cbg_tags] + outputs)
        self.cbg_tags.change(fn=lambda a, *b:[self.cbg_tags_changed(a)] + on_filter_update(*b), inputs=[self.cbg_tags] + inputs, outputs=[self.cbg_tags] + outputs)


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
        self.logic = filters.TagFilter.Logic.AND if rd_logic == 'AND' else filters.TagFilter.Logic.OR if rd_logic == 'OR' else filters.TagFilter.Logic.NONE
        self.filter = filters.TagFilter(set(self.selected_tags), self.logic, self.filter_mode)
        return self.cbg_tags_update()


    def cbg_tags_changed(self, cbg_tags: List[str]):
        self.selected_tags = self.dataset_tag_editor.read_tags(cbg_tags)
        self.filter = filters.TagFilter(set(self.selected_tags), self.logic, self.filter_mode)
        return self.cbg_tags_update()


    def cbg_tags_update(self):
        if self.filter_mode == filters.TagFilter.Mode.INCLUSIVE:
            filtered_tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, self.filter.logic == filters.TagFilter.Logic.AND)
        else:
            filtered_tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, self.filter.logic == filters.TagFilter.Logic.OR)
        tags = self.dataset_tag_editor.sort_tags(tags=filtered_tags, sort_by=self.sort_by, sort_order=self.sort_order)
        tags_in_filter = self.dataset_tag_editor.sort_tags(tags=list(self.filter.tags), sort_by=self.sort_by, sort_order=self.sort_order)
        tags = tags_in_filter + [tag for tag in tags if tag not in self.filter.tags]
        tags = self.dataset_tag_editor.write_tags(tags)
        tags_in_filter = self.dataset_tag_editor.write_tags(tags_in_filter)

        import gradio as gr
        return gr.CheckboxGroup.update(value=tags_in_filter, choices=tags)


    def clear_filter(self):
        self.filter = filters.TagFilter({}, self.logic, self.filter_mode)
        self.filter_word = ''
        self.selected_tags = []


class TagSelectUI:
    def __init__(self, dataset_tag_editor: dte.DatasetTagEditor):
        self.filter_word = ''
        self.sort_by = 'Alphabetical Order'
        self.sort_order = 'Ascending'
        self.selected_tags = set()
        self.tags = set()
        self.dataset_tag_editor = dataset_tag_editor
        self.get_filters = lambda:[]


    def create_ui(self, get_filters: Callable[[], List[ds.Dataset.Filter]], sort_by = 'Alphabetical Order', sort_order = 'Ascending'):
        self.get_filters = get_filters

        import gradio as gr
        self.tb_search_tags = gr.Textbox(label='Search Tags', interactive=True)
        with gr.Row():
            self.rb_sort_by = gr.Radio(choices=['Alphabetical Order', 'Frequency'], value=sort_by, interactive=True, label='Sort by')
            self.rb_sort_order = gr.Radio(choices=['Ascending', 'Descending'], value=sort_order, interactive=True, label='Sort Order')
        with gr.Row():
            self.btn_select_visibles = gr.Button(value='Select visible tags')
            self.btn_deselect_visibles = gr.Button(value='Deselect visible tags')
        self.cbg_tags = gr.CheckboxGroup(label='Select Tags', interactive=True)


    def set_callbacks(self):
        self.tb_search_tags.change(fn=self.tb_search_tags_changed, inputs=self.tb_search_tags, outputs=self.cbg_tags)
        self.rb_sort_by.change(fn=self.rd_sort_by_changed, inputs=self.rb_sort_by, outputs=self.cbg_tags)
        self.rb_sort_order.change(fn=self.rd_sort_order_changed, inputs=self.rb_sort_order, outputs=self.cbg_tags)
        self.btn_select_visibles.click(fn=self.btn_select_visibles_clicked, outputs=self.cbg_tags)
        self.btn_deselect_visibles.click(fn=self.btn_deselect_visibles_clicked, inputs=self.cbg_tags, outputs=self.cbg_tags)
        self.cbg_tags.change(fn=self.cbg_tags_changed, inputs=self.cbg_tags, outputs=self.cbg_tags)


    def tb_search_tags_changed(self, tb_search_tags: str):
        self.filter_word = tb_search_tags
        return self.cbg_tags_update()


    def rd_sort_by_changed(self, rb_sort_by: str):
        self.sort_by = rb_sort_by
        return self.cbg_tags_update()


    def rd_sort_order_changed(self, rd_sort_order: str):
        self.sort_order = rd_sort_order
        return self.cbg_tags_update()


    def cbg_tags_changed(self, cbg_tags: List[str]):
        self.selected_tags = set(self.dataset_tag_editor.read_tags(cbg_tags))
        return self.cbg_tags_update()


    def btn_deselect_visibles_clicked(self, cbg_tags: List[str]):
        tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, True)
        selected_tags = set(self.dataset_tag_editor.read_tags(cbg_tags)) & tags
        self.selected_tags -= selected_tags
        return self.cbg_tags_update()


    def btn_select_visibles_clicked(self):
        tags = set(self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, True))
        self.selected_tags |= tags
        return self.cbg_tags_update()


    def cbg_tags_update(self):
        tags = self.dataset_tag_editor.get_filtered_tags(self.get_filters(), self.filter_word, True)
        self.tags = set(self.dataset_tag_editor.get_filtered_tags(self.get_filters(), filter_tags=True))
        self.selected_tags &= self.tags
        tags = self.dataset_tag_editor.sort_tags(tags=tags, sort_by=self.sort_by, sort_order=self.sort_order)
        tags = self.dataset_tag_editor.write_tags(tags)
        selected_tags = self.dataset_tag_editor.write_tags(list(self.selected_tags))
        import gradio as gr
        return gr.CheckboxGroup.update(value=selected_tags, choices=tags)