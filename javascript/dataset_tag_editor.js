// from ui.js
function dataset_tag_editor_selected_gallery_index() {
    var gallery = gradioApp().getElementById("dataset_tag_editor_images_gallery")
    var buttons = gallery.querySelectorAll('[style="display: block;"].tabitem .gallery-item')
    var button = gallery.querySelector('[style="display: block;"].tabitem .gallery-item.\\!ring-2')

    var result = -1
    buttons.forEach(function (v, i) { if (v == button) { result = i } })

    return result
}

function dataset_tag_editor_selected_selection_index() {
    var selection = gradioApp().getElementById("dataset_tag_editor_selection_images_gallery")
    var buttons = selection.querySelectorAll('[style="display: block;"].tabitem .gallery-item')
    var button = selection.querySelector('[style="display: block;"].tabitem .gallery-item.\\!ring-2')

    var result = -1
    buttons.forEach(function (v, i) { if (v == button) { result = i } })

    return result
}

var dataset_tag_editor_gallery_image_clicked = function () {
    var set_button = gradioApp().getElementById("dataset_tag_editor_set_index");
    if(set_button){
        set_button.click()
    }
}

var dataset_tag_editor_gallery_key_handler = function (e) {
    switch(e.key)
    {
        case 'Enter':
            var button = gradioApp().getElementById('dataset_tag_editor_btn_add_image_selection');
            if (button) {
                button.click();
            }
            e.preventDefault();
            break;
    }
    dataset_tag_editor_gallery_image_clicked();
}


var dataset_tag_editor_selection_image_clicked = function () {
    var set_button = gradioApp().getElementById("dataset_tag_editor_set_selection_index");
    if(set_button){
        set_button.click()
    }
}

var dataset_tag_editor_selection_key_handler = function (e) {
    switch(e.key)
    {
        case 'Delete':
            var button = gradioApp().getElementById('dataset_tag_editor_btn_remove_image_selection');
            if (button) {
                button.click();
            }
            e.preventDefault();
            break;
    }
    dataset_tag_editor_selection_image_clicked();
}

document.addEventListener("DOMContentLoaded", function () {
    var o = new MutationObserver(function (m) {
        var gallery_dataset = gradioApp().getElementById("dataset_tag_editor_images_gallery")

        var fullImg_preview_group = gallery_dataset.querySelectorAll('div.absolute.group')
        if (fullImg_preview_group != null) {
            fullImg_preview_group.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('keydown', dataset_tag_editor_gallery_key_handler, false)
                }
            });
        }
        
        var buttons = gallery_dataset.querySelectorAll(".gallery-item");
        if (buttons != null) {
            buttons.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }

        var fullImg_preview = gallery_dataset.querySelectorAll('img.w-full.object-contain')
        if (fullImg_preview != null) {
            fullImg_preview.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }

        var imgPreview_close = gallery_dataset.querySelectorAll('div.modify-upload')
        if (imgPreview_close != null) {
            imgPreview_close.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }


        var selection = gradioApp().getElementById("dataset_tag_editor_selection_images_gallery")

        var fullImg_preview_group_selection = selection.querySelectorAll('div.absolute.group')
        if (fullImg_preview_group_selection != null) {
            fullImg_preview_group_selection.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('keydown', dataset_tag_editor_selection_key_handler, false)
                }
            });
        }
        
        var buttons_selection = selection.querySelectorAll(".gallery-item");
        if (buttons_selection != null) {
            buttons_selection.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', dataset_tag_editor_selection_image_clicked, false);
                }
            });
        }

        var fullImg_preview_selection = selection.querySelectorAll('img.w-full.object-contain')
        if (fullImg_preview_selection != null) {
            fullImg_preview_selection.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_selection_image_clicked, false);
                }
            });
        }
        
        var imgPreview_close_selection = selection.querySelectorAll('div.modify-upload')
        if (imgPreview_close_selection != null) {
            imgPreview_close_selection.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_selection_image_clicked, false);
                }
            });
        }
    });
    o.observe(gradioApp(), { childList: true, subtree: true });
});