class DTEModifiedGallery{
    #elem;
    #items_grid;
    #items_selector;
    #current_filter = null;
    #selected_idx = -1
    #filter_idx = -1

    setElement(elem){
        this.#elem = elem;
        this.#items_grid = this.#elem.querySelectorAll('div.grid-wrap > div.grid-container > button.thumbnail-item')
        this.#items_selector = this.#elem.querySelectorAll('div.preview > div.thumbnails > button.thumbnail-item')
    }

    updateFilter(){
        if (!this.#elem) return;

        if (this.#items_grid){
            for(let i = 0; i < this.#items_grid.length; ++i){
                if(!this.#current_filter || this.#current_filter.includes(i)){
                    this.#items_grid[i].hidden = false
                }
                else{
                    this.#items_grid[i].hidden = true
                }
            }
        }
        if(this.#items_selector){
            for(let i = 0; i < this.#items_selector.length; ++i){
                if(!this.#current_filter || this.#current_filter.includes(i)){
                    this.#items_selector[i].hidden = false
                }
                else{
                    this.#items_selector[i].hidden = true
                }
            }
        }
    }

    filter(indices){
        if (!this.#elem) return;
        this.#current_filter = indices.map((e) => +e).sort((a, b) => a - b)
        this.updateFilter()
    }

    clearFilter(){
        this.#current_filter = null
        this.updateFilter()
    }

    getVisibleSelectedIndex(){
        if (!this.#elem || !this.#items_selector) return -1;

        let button = this.#elem.querySelector('.gradio-gallery .thumbnail-item.selected')
        
        for (let i = 0; i < this.#items_selector.length; ++i){
            if (this.#items_selector[i] == button){
                return i;
            }
        }
        return -1
    }

    getSelectedIndex() {
        if (!this.#elem || !this.#items_selector) return -1;
        if (!this.#current_filter) return this.#selected_idx
        return this.#filter_idx
    }

    keyHandler(e){
        switch(e.key)
        {
            case 'ArrowLeft':
                {
                    let filteridx = this.getSelectedIndex()
                    if (filteridx < 0) break;
                    if (this.#current_filter){
                        let next = (filteridx + this.#current_filter.length - 1) % this.#current_filter.length;
                        this.#filter_idx = next
                        this.#selected_idx = this.#current_filter[next]
                    }
                    else{
                        this.#selected_idx = (filteridx + this.#items_selector.length - 1) % this.#items_selector.length;
                    }
                    let button = this.#items_selector[this.#selected_idx]
                    if(button){
                        button.click()
                    }
                    break;
                }
            case 'ArrowRight':
                {
                    let filteridx = this.getSelectedIndex()
                    if (filteridx < 0) break;
                    if (this.#current_filter){
                        let next = (filteridx + 1) % this.#current_filter.length;
                        this.#filter_idx = next
                        this.#selected_idx = this.#current_filter[next]
                    }
                    else{
                        this.#selected_idx = (filteridx + 1) % this.#items_selector.length;
                    }
                    let button = this.#items_selector[this.#selected_idx]
                    if(button){
                        button.click()
                    }
                    break;
                }
            case 'Escape':
                {
                    let imgPreview_close = this.#elem.querySelector('div.preview > div > button[class^="svelte"]')
                    if (imgPreview_close != null) {
                        imgPreview_close.click()
                    }
                    this.#filter_idx = -1
                    this.#selected_idx = -1
                }
        }
    }

    clickHandler(){
        if(!this.#items_selector) return
        let idx = this.getVisibleSelectedIndex()

        if(!this.#current_filter){
            this.#selected_idx = idx
            return
        }

        for(let i = 0; i<this.#current_filter.length; ++i){
            if (this.#current_filter[i] == idx){
                this.#selected_idx = idx
                this.#filter_idx = i
                return
            }
        }
    }

    clickNextHandler(){
        if(!this.#items_selector || !this.#current_filter) return
        let filteridx = this.getSelectedIndex()
        if (filteridx < 0) return;
        let next = (filteridx + 1) % this.#current_filter.length;
        this.#filter_idx = next
        this.#selected_idx = this.#current_filter[next] 
        let button = this.#items_selector[this.#selected_idx]
        if(button){
            button.click()
        }
    }

    clickCloseHandler(){
        this.#filter_idx = -1
        this.#selected_idx = -1
        this.#items_selector = null
    }
    
    addKeyHandler(callback_key_handler){
        if (!this.#elem) return;
        this.#elem.addEventListener('keydown', callback_key_handler, false)
    }

    addClickHandler(callback_clicked){
        if (!this.#elem) return;
        
        if (this.#items_grid != null) {
            this.#items_grid.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', callback_clicked, false);
                }
            });
        }
        if (this.#items_selector != null) {
            this.#items_selector.forEach(function (btn) {
                if (btn) {
                    btn.addEventListener('click', callback_clicked, false);
                }
            });
        }
        
    }


    addClickNextHandler(callback_clicked){
        if (!this.#elem) return;
        
        let fullImg_preview = this.#elem.querySelectorAll('div.preview > img')
        if (fullImg_preview != null) {
            fullImg_preview.forEach(function (e) {
                if (e) {
                    e.addEventListener('click', callback_clicked, false);
                }
            });
        }

    }

    addClickCloseHandler(callback_clicked){
        if (!this.#elem) return;
        
        let imgPreview_close = this.#elem.querySelectorAll('div.preview > div > button[class^="svelte"]')
        if (imgPreview_close != null) {
            imgPreview_close.forEach(function (e) {
                if (e) {
                    e.addEventListener('click', callback_clicked, false);
                }
            });
        }
        
    }

    clickClose(){
        if (!this.#elem) return;
        
        let imgPreview_close = this.#elem.querySelectorAll('div.preview > div > button[class^="svelte"]')
        if (imgPreview_close != null) {
            imgPreview_close.forEach(function (e) {
                if (e) {
                    e.click()
                }
            });
        }
        
    }

}