// from ui.js
function dataset_tag_editor_selected_gallery_index() {
    let gallery = gradioApp().getElementById("dataset_tag_editor_images_gallery")
    let buttons = gallery.querySelectorAll('[style="display: block;"].tabitem .gallery-item')
    let button = gallery.querySelector('[style="display: block;"].tabitem .gallery-item.\\!ring-2')

    let result = -1
    buttons.forEach(function (v, i) { if (v == button) { result = i } })

    return result
}

function dataset_tag_editor_selected_selection_index() {
    let selection = gradioApp().getElementById("dataset_tag_editor_selection_images_gallery")
    let buttons = selection.querySelectorAll('[style="display: block;"].tabitem .gallery-item')
    let button = selection.querySelector('[style="display: block;"].tabitem .gallery-item.\\!ring-2')

    let result = -1
    buttons.forEach(function (v, i) { if (v == button) { result = i } })

    return result
}

let dataset_tag_editor_gallery_image_clicked = function () {
    let set_button = gradioApp().getElementById("dataset_tag_editor_set_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_gallery_key_handler = function (e) {
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
    dataset_tag_editor_gallery_image_clicked();
}


let dataset_tag_editor_selection_image_clicked = function () {
    let set_button = gradioApp().getElementById("dataset_tag_editor_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

let dataset_tag_editor_selection_key_handler = function (e) {
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
    dataset_tag_editor_selection_image_clicked();
}

let dteModifiedGallery_dataset = new DTEModifiedGallery()
let dteModifiedGallery_filter = new DTEModifiedGallery()

document.addEventListener("DOMContentLoaded", function () {
    let o = new MutationObserver(function (m) {
        dteModifiedGallery_dataset.setElement(gradioApp().getElementById("dataset_tag_editor_images_gallery"))
        dteModifiedGallery_dataset.addKeyHandler(dataset_tag_editor_gallery_key_handler)
        dteModifiedGallery_dataset.addClickHandler(dataset_tag_editor_gallery_image_clicked)
        
        dteModifiedGallery_filter.setElement(gradioApp().getElementById("dataset_tag_editor_selection_images_gallery"))
        dteModifiedGallery_filter.addKeyHandler(dataset_tag_editor_selection_key_handler)
        dteModifiedGallery_filter.addClickHandler(dataset_tag_editor_selection_image_clicked)
    });
    o.observe(gradioApp(), { childList: true, subtree: true });
});