let dteModifiedGallery_dataset = new DTEModifiedGallery()
let dteModifiedGallery_filter = new DTEModifiedGallery()


function dataset_tag_editor_gl_dataset_images_selected_index() {
    return dteModifiedGallery_dataset.getSelectedIndex()
}

function dataset_tag_editor_gl_filter_images_selected_index() {
    return dteModifiedGallery_filter.getSelectedIndex()
}

function dataset_tag_editor_gl_dataset_images_filter(indices) {
    dteModifiedGallery_dataset.filter(indices)
    return indices
}

function dataset_tag_editor_gl_dataset_images_clear_filter() {
    dteModifiedGallery_dataset.clearFilter()
    return []
}

function dataset_tag_editor_gl_dataset_images_close() {
    dteModifiedGallery_dataset.clickClose()
}

function dataset_tag_editor_gl_filter_images_close() {
    dteModifiedGallery_filter.clickClose()
}

let dataset_tag_editor_gl_dataset_images_clicked = function () {
    dteModifiedGallery_dataset.updateFilter()
    dteModifiedGallery_dataset.clickHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_dataset_images_next_clicked = function () {
    dteModifiedGallery_dataset.updateFilter()
    dteModifiedGallery_dataset.clickNextHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_dataset_images_close_clicked = function () {
    dteModifiedGallery_dataset.updateFilter()
    dteModifiedGallery_dataset.clickCloseHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_dataset_images_key_handler = function (e) {
    dteModifiedGallery_dataset.keyHandler(e)
    switch(e.key)
    {
        case 'Enter':
            let button = gradioApp().getElementById('dataset_tag_editor_btn_add_image_selection');
            if (button) {
                button.click();
            }
            e.preventDefault();
            break;
    }
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_index");
    if(set_button){
        set_button.click()
    }
}


let dataset_tag_editor_gl_filter_images_clicked = function () {
    dteModifiedGallery_filter.updateFilter()
    dteModifiedGallery_filter.clickHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_filter_images_next_clicked = function () {
    dteModifiedGallery_filter.updateFilter()
    dteModifiedGallery_filter.clickNextHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_filter_images_close_clicked = function () {
    dteModifiedGallery_filter.updateFilter()
    dteModifiedGallery_filter.clickCloseHandler()
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_filter_images_key_handler = function (e) {
    dteModifiedGallery_filter.keyHandler(e)
    switch(e.key)
    {
        case 'Delete':
            let button = gradioApp().getElementById('dataset_tag_editor_btn_remove_image_selection');
            if (button) {
                button.click();
            }
            e.preventDefault();
            break;
    }
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

document.addEventListener("DOMContentLoaded", function () {
    let o = new MutationObserver(function (m) {
        let elem_gl_dataset = gradioApp().getElementById("dataset_tag_editor_dataset_gallery")
        let elem_gl_filter = gradioApp().getElementById("dataset_tag_editor_filter_gallery")
        if(elem_gl_dataset){
            dteModifiedGallery_dataset.setElement(elem_gl_dataset)
            dteModifiedGallery_dataset.addKeyHandler(dataset_tag_editor_gl_dataset_images_key_handler)
            dteModifiedGallery_dataset.addClickHandler(dataset_tag_editor_gl_dataset_images_clicked)
            dteModifiedGallery_dataset.addClickNextHandler(dataset_tag_editor_gl_dataset_images_next_clicked)
            dteModifiedGallery_dataset.addClickCloseHandler(dataset_tag_editor_gl_dataset_images_close_clicked)
        }
        if(elem_gl_filter){
            dteModifiedGallery_filter.setElement(elem_gl_filter)
            dteModifiedGallery_filter.addKeyHandler(dataset_tag_editor_gl_filter_images_key_handler)
            dteModifiedGallery_filter.addClickHandler(dataset_tag_editor_gl_filter_images_clicked)
            dteModifiedGallery_filter.addClickNextHandler(dataset_tag_editor_gl_filter_images_next_clicked)
            dteModifiedGallery_filter.addClickCloseHandler(dataset_tag_editor_gl_filter_images_close_clicked)
        }
        
        if(gradioApp().getElementById('settings_json') == null) return
        function changeTokenCounterPos(id, id_counter){
            var prompt = gradioApp().getElementById(id)
            var counter = gradioApp().getElementById(id_counter)
    
            if(counter.parentElement == prompt.parentElement){
                return
            }
    
            prompt.parentElement.insertBefore(counter, prompt)
            prompt.parentElement.style.position = "relative"
            counter.style.width = "auto"
        }
        changeTokenCounterPos('dte_caption', 'dte_caption_counter')
        changeTokenCounterPos('dte_edit_caption', 'dte_edit_caption_counter')
        changeTokenCounterPos('dte_interrogate', 'dte_interrogate_counter')
    });
    
    o.observe(gradioApp(), { childList: true, subtree: true })
});