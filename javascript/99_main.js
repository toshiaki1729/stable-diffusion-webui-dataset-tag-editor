let dteModifiedGallery_dataset = new DTEModifiedGallery()
let dteModifiedGallery_filter = new DTEModifiedGallery()


// from ui.js
function dataset_tag_editor_gl_dataset_images_selected_index() {
    return dteModifiedGallery_dataset.getSelectedIndex()
}

function dataset_tag_editor_gl_selected_images_selected_index() {
    return dteModifiedGallery_filter.getSelectedIndex()
}

let dataset_tag_editor_gl_dataset_images_clicked = function () {
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_dataset_images_key_handler = function (e) {
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
    dataset_tag_editor_gl_dataset_images_clicked()
}


let dataset_tag_editor_gl_selected_images_clicked = function () {
    let set_button = gradioApp().getElementById("dataset_tag_editor_btn_hidden_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gl_selected_images_key_handler = function (e) {
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
    dataset_tag_editor_gl_selected_images_clicked()
}

document.addEventListener("DOMContentLoaded", function () {
    let o = new MutationObserver(function (m) {
        let elem_gl_dataset = gradioApp().getElementById("dataset_tag_editor_dataset_gallery")
        let elem_gl_selected = gradioApp().getElementById("dataset_tag_editor_selection_gallery")
        if(elem_gl_dataset){
            dteModifiedGallery_dataset.setElement(elem_gl_dataset)
            dteModifiedGallery_dataset.addKeyHandler(dataset_tag_editor_gl_dataset_images_key_handler)
            dteModifiedGallery_dataset.addClickHandler(dataset_tag_editor_gl_dataset_images_clicked)
        }
        if(elem_gl_selected){
            dteModifiedGallery_filter.setElement(elem_gl_selected)
            dteModifiedGallery_filter.addKeyHandler(dataset_tag_editor_gl_selected_images_key_handler)
            dteModifiedGallery_filter.addClickHandler(dataset_tag_editor_gl_selected_images_clicked)
        }
    });
    
    o.observe(gradioApp(), { childList: true, subtree: true })
});