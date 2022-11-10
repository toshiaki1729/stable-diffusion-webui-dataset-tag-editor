class DTEModifiedGallery{
    #img_paths = [];
    #path_hidden_map = new Map();
    #elem;

    setElement(elem){
        this.#elem = elem;
    }

    setImgPaths(img_paths){
        this.#img_paths = img_paths
        img_paths.forEach(element => {
            this.#path_hidden_map.set(element, false)
        });
    }

    addKeyHandler(callback_key_handler){
        if (!this.#elem) return;
        let fullImg_preview_group = this.#elem.querySelectorAll('div.absolute.group')
        if (fullImg_preview_group != null) {
            fullImg_preview_group.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('keydown', callback_key_handler, false)
                }
            });
        }
    }

    addClickHandler(callback_clicked){
        if (!this.#elem) return;
        
        let buttons = this.#elem.querySelectorAll(".gallery-item");
        if (buttons != null) {
            buttons.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', callback_clicked, false);
                }
            });
        }

        let fullImg_preview = this.#elem.querySelectorAll('img.w-full.object-contain')
        if (fullImg_preview != null) {
            fullImg_preview.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', callback_clicked, false);
                }
            });
        }

        let imgPreview_close = this.#elem.querySelectorAll('div.modify-upload')
        if (imgPreview_close != null) {
            imgPreview_close.forEach(function (e) {
                if (e && e.parentElement.tagName == 'DIV') {
                    e.addEventListener('click', callback_clicked, false);
                }
            });
        }
        
    }
    
    updateView(){

    }
}