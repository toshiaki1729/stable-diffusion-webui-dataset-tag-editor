// from ui.js
function dataset_tag_editor_selected_gallery_index() {
    var buttons = gradioApp().querySelectorAll('[style="display: block;"].tabitem .gallery-item')
    var button = gradioApp().querySelector('[style="display: block;"].tabitem .gallery-item.\\!ring-2')

    var result = -1
    buttons.forEach(function (v, i) { if (v == button) { result = i } })

    return result
}

var dataset_tag_editor_gallery_image_clicked = function () {
    var set_button = gradioApp().getElementById("dataset_tag_editor_set_index");
    set_button.click()
}

var dataset_tag_editor_key_handler = function (event) {
    dataset_tag_editor_gallery_image_clicked();
}

document.addEventListener("DOMContentLoaded", function () {
    var o = new MutationObserver(function (m) {
        var buttons = gradioApp().getElementById("dataset_tag_editor_images_gallery").querySelectorAll(".gallery-item");

        if (buttons != null) {
            buttons.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }
        var fullImg_preview_group = gradioApp().querySelectorAll('div.absolute.group')
        if (fullImg_preview_group != null) {
            fullImg_preview_group.forEach(function function_name(e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('keydown', dataset_tag_editor_key_handler, false)
                }
            });
        }

        var fullImg_preview = gradioApp().querySelectorAll('img.w-full.object-contain')
        if (fullImg_preview != null) {
            fullImg_preview.forEach(function function_name(e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }
        var imgPreview_close = gradioApp().querySelectorAll('div.modify-upload')
        if (imgPreview_close != null) {
            imgPreview_close.forEach(function function_name(e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', dataset_tag_editor_gallery_image_clicked, false);
                }
            });
        }
    });
    o.observe(gradioApp(), { childList: true, subtree: true });
});