from pathlib import Path
import re
from typing import List, Set, Optional
from enum import Enum
from PIL import Image

from modules import shared
from modules.textual_inversion.dataset import re_numbers_at_start

from scripts.singleton import Singleton

from . import tagger, captioning, filters, dataset as ds, kohya_finetune_metadata as kohya_metadata
from scripts.tokenizer import clip_tokenizer

WD_TAGGER_NAMES = ["wd-v1-4-vit-tagger", "wd-v1-4-convnext-tagger", "wd-v1-4-vit-tagger-v2", "wd-v1-4-convnext-tagger-v2", "wd-v1-4-swinv2-tagger-v2"]
WD_TAGGER_THRESHOLDS = [0.35, 0.35, 0.3537, 0.3685, 0.3771] # v1: idk if it's okay  v2: P=R thresholds on each repo https://huggingface.co/SmilingWolf

INTERROGATORS = [captioning.BLIP(), tagger.DeepDanbooru()] + [tagger.WaifuDiffusion(name, WD_TAGGER_THRESHOLDS[i]) for i, name in enumerate(WD_TAGGER_NAMES)]
INTERROGATOR_NAMES = [it.name() for it in INTERROGATORS]

re_tags = re.compile(r'^([\s\S]+?)( \[\d+\])?$')
re_newlines = re.compile(r'[\r\n]+')


def interrogate_image(path:str, interrogator_name:str, threshold_booru, threshold_wd):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        for it in INTERROGATORS:
            if it.name() == interrogator_name:
                if isinstance(it, tagger.DeepDanbooru):
                    with it as tg:
                        res = tg.predict(img, threshold_booru)
                elif isinstance(it, tagger.WaifuDiffusion):
                    with it as tg:
                        res = tg.predict(img, threshold_wd)
                else:
                    with it as cap:
                        res = cap.predict(img)
        return ', '.join(res)


class DatasetTagEditor(Singleton):
    class SortBy(Enum):
        ALPHA = 'Alphabetical Order'
        FREQ = 'Frequency'
        LEN = 'Length'
        TOKEN = 'Token Length'

    class SortOrder(Enum):
        ASC = 'Ascending'
        DESC = 'Descending'

    class InterrogateMethod(Enum):
        NONE = 0
        PREFILL = 1
        OVERWRITE = 2
        PREPEND = 3
        APPEND = 4
    
    def __init__(self):
        # from modules.textual_inversion.dataset
        self.re_word = re.compile(shared.opts.dataset_filename_word_regex) if len(shared.opts.dataset_filename_word_regex) > 0 else None
        self.dataset = ds.Dataset()
        self.img_idx = dict()
        self.tag_counts = {}
        self.dataset_dir = ''
        self.images = {}
        self.tag_tokens = {}
        self.raw_clip_token_used = None

    def get_tag_list(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_infos()
        return [key for key in self.tag_counts.keys()]


    def get_tag_set(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_infos()
        return {key for key in self.tag_counts.keys()}


    def get_tags_by_image_path(self, imgpath:str):
        return self.dataset.get_data_tags(imgpath)

    
    def set_tags_by_image_path(self, imgpath:str, tags:List[str]):
        self.dataset.append_data(ds.Data(imgpath, ','.join(tags)))
        self.construct_tag_infos()
    

    def write_tags(self, tags:List[str], sort_by:SortBy=SortBy.FREQ):
        sort_by = self.SortBy(sort_by)
        if tags:
            if sort_by == self.SortBy.FREQ:
                return [f'{tag} [{self.tag_counts.get(tag) or 0}]' for tag in tags if tag]
            elif sort_by == self.SortBy.LEN:
                return [f'{tag} [{len(tag)}]' for tag in tags if tag]
            elif sort_by == self.SortBy.TOKEN:
                return [f'{tag} [{self.tag_tokens.get(tag, (0, 0))[1]}]' for tag in tags if tag]
            else:
                return [f'{tag}' for tag in tags if tag]
        else:
            return []


    def read_tags(self, tags:List[str]):
        if tags:
            tags = [re_tags.match(tag).group(1) for tag in tags if tag]
            return [t for t in tags if t]
        else:
            return []


    def sort_tags(self, tags:List[str], sort_by:SortBy=SortBy.ALPHA, sort_order:SortOrder=SortOrder.ASC):
        sort_by = self.SortBy(sort_by)
        sort_order = self.SortOrder(sort_order)
        if sort_by == self.SortBy.ALPHA:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, reverse=True)
        elif sort_by == self.SortBy.FREQ:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, key=lambda t:(self.tag_counts.get(t, 0), t), reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, key=lambda t:(-self.tag_counts.get(t, 0), t), reverse=False)
        elif sort_by == self.SortBy.LEN:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, key=lambda t:(len(t), t), reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, key=lambda t:(-len(t), t), reverse=False)
        elif sort_by == self.SortBy.TOKEN:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, key=lambda t:(self.tag_tokens.get(t, (0, 0))[1], t), reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, key=lambda t:(-self.tag_tokens.get(t, (0, 0))[1], t), reverse=False)
        return list(tags)


    def get_filtered_imgpaths(self, filters:List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        img_paths = sorted(filtered_set.datas.keys())
        
        return img_paths
    

    def get_filtered_imgs(self, filters:List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        img_paths = sorted(filtered_set.datas.keys())
        
        return [self.images.get(path) for path in img_paths]


    def get_filtered_imgindices(self, filters:List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        img_paths = sorted(filtered_set.datas.keys())
        
        return [self.img_idx.get(p) for p in img_paths]


    def get_filtered_tags(self, filters:List[filters.Filter] = [], filter_word:str = '', filter_tags = True, prefix=False, suffix=False, regex=False):
        if filter_tags:
            filtered_set = self.dataset.copy()
            for filter in filters:
                filtered_set.filter(filter)
            tags:Set[str] = filtered_set.get_tagset()
        else:
            tags:Set[str] = self.dataset.get_tagset()
        
        result = set()
        try:
            for tag in tags:
                if prefix:
                    if regex:
                        if re.search("^" + filter_word, tag) is not None:
                            result.add(tag)
                            continue
                    else:
                        if tag.startswith(filter_word):
                            result.add(tag)
                            continue
                if suffix:
                    if regex:
                        if re.search(filter_word + "$", tag) is not None:
                            result.add(tag)
                            continue
                    else:
                        if tag.endswith(filter_word):
                            result.add(tag)
                            continue
                if not prefix and not suffix:
                    if regex:
                        if re.search(filter_word, tag) is not None:
                            result.add(tag)
                            continue
                    else:
                        if filter_word in tag:
                            result.add(tag)
                            continue
        except:
            return tags
        else:
            return result


    def cleanup_tags(self, tags:List[str]):
        current_dataset_tags = self.dataset.get_tagset()
        return [t for t in tags if t in current_dataset_tags]
    
    def cleanup_tagset(self, tags:Set[str]):
        current_dataset_tagset = self.dataset.get_tagset()
        return tags & current_dataset_tagset
        

    def get_common_tags(self, filters:List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        result = filtered_set.get_tagset()
        for d in filtered_set.datas.values():
            result &= d.tagset

        return sorted(result)
    

    def replace_tags(self, search_tags:List[str], replace_tags:List[str], filters:List[filters.Filter] = [], prepend:bool = False):
        img_paths = self.get_filtered_imgpaths(filters=filters)
        tags_to_append = replace_tags[len(search_tags):]
        tags_to_remove = search_tags[len(replace_tags):]
        tags_to_replace = {}
        for i in range(min(len(search_tags), len(replace_tags))):
            if replace_tags[i] is None or replace_tags[i] == '':
                tags_to_remove.append(search_tags[i])
            else:
                tags_to_replace[search_tags[i]] = replace_tags[i]
        for img_path in img_paths:
            tags_removed = [t for t in self.dataset.get_data_tags(img_path) if t not in tags_to_remove]
            tags_replaced = [tags_to_replace.get(t) if t in tags_to_replace.keys() else t for t in tags_removed]
            self.set_tags_by_image_path(img_path, tags_to_append + tags_replaced if prepend else tags_replaced + tags_to_append)
        
        self.construct_tag_infos()

    def get_replaced_tagset(self, tags:Set[str], search_tags:List[str], replace_tags:List[str]):
        tags_to_remove = search_tags[len(replace_tags):]
        tags_to_replace = {}
        for i in range(min(len(search_tags), len(replace_tags))):
            if replace_tags[i] is None or replace_tags[i] == '':
                tags_to_remove.append(search_tags[i])
            else:
                tags_to_replace[search_tags[i]] = replace_tags[i]
        tags_removed = {t for t in tags if t not in tags_to_remove}
        tags_replaced = {tags_to_replace.get(t) if t in tags_to_replace.keys() else t for t in tags_removed}
        return {t for t in tags_replaced if t}


    def search_and_replace_caption(self, search_text:str, replace_text:str, filters:List[filters.Filter] = [], use_regex:bool = False):
        img_paths = self.get_filtered_imgpaths(filters=filters)
        
        for img_path in img_paths:
            caption = ', '.join(self.dataset.get_data_tags(img_path))
            if use_regex:
                caption = [t.strip() for t in re.sub(search_text, replace_text, caption).split(',')]
            else:
                caption = [t.strip() for t in caption.replace(search_text, replace_text).split(',')]
            caption = [t for t in caption if t]
            self.set_tags_by_image_path(img_path, caption)
        
        self.construct_tag_infos()


    def search_and_replace_selected_tags(self, search_text:str, replace_text:str, selected_tags:Optional[Set[str]], filters:List[filters.Filter] = [], use_regex:bool = False):
        img_paths = self.get_filtered_imgpaths(filters=filters)

        for img_path in img_paths:
            tags = self.dataset.get_data_tags(img_path)
            tags = self.search_and_replace_tag_list(search_text, replace_text, tags, selected_tags, use_regex)
            self.set_tags_by_image_path(img_path, tags)
        
        self.construct_tag_infos()

    
    def search_and_replace_tag_list(self, search_text:str, replace_text:str, tags:List[str], selected_tags:Optional[Set[str]] = None, use_regex:bool = False):
        if use_regex:
            if selected_tags is None:
                tags = [re.sub(search_text, replace_text, t) for t in tags]
            else:
                tags = [re.sub(search_text, replace_text, t) if t in selected_tags else t for t in tags]
        else:
            if selected_tags is None:
                tags = [t.replace(search_text, replace_text) for t in tags]
            else:
                tags = [t.replace(search_text, replace_text) if t in selected_tags else t for t in tags]
        tags = [t2 for t1 in tags for t2 in t1.split(',') if t2]
        return [t for t in tags if t]


    def search_and_replace_tag_set(self, search_text:str, replace_text:str, tags:Set[str], selected_tags:Optional[Set[str]] = None, use_regex:bool = False):
        if use_regex:
            if selected_tags is None:
                tags = {re.sub(search_text, replace_text, t) for t in tags}
            else:
                tags = {re.sub(search_text, replace_text, t) if t in selected_tags else t for t in tags}
        else:
            if selected_tags is None:
                tags = {t.replace(search_text, replace_text) for t in tags}
            else:
                tags = {t.replace(search_text, replace_text) if t in selected_tags else t for t in tags}
        tags = {t2 for t1 in tags for t2 in t1.split(',') if t2}
        return {t for t in tags if t}
    

    def remove_duplicated_tags(self, filters:List[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = []
            for t in tags:
                if t not in res:
                    res.append(t)
            self.set_tags_by_image_path(path, res)
    

    def remove_tags(self, tags:Set[str], filters:List[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            res = self.dataset.get_data_tags(path)
            res = [t for t in res if t not in tags]
            self.set_tags_by_image_path(path, res)


    def sort_filtered_tags(self, filters:List[filters.Filter] = [], **sort_args):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = self.sort_tags(tags, **sort_args)
            self.set_tags_by_image_path(path, res)
        print(f'[tag-editor] Tags are sorted by {sort_args.get("sort_by").value} ({sort_args.get("sort_order").value})')


    def truncate_filtered_tags_by_token_count(self, filters:List[filters.Filter] = [], max_token_count:int = 75):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = []
            for tag in tags:
                _, token_count = clip_tokenizer.tokenize(', '.join(res + [tag]), shared.opts.dataset_editor_use_raw_clip_token)
                if token_count <= max_token_count:
                    res.append(tag)
                else:
                    break
            self.set_tags_by_image_path(path, res)

        self.construct_tag_infos()
        print(f'[tag-editor] Tags are truncated into token count <= {max_token_count}')


    def get_img_path_list(self):
        return [k for k in self.dataset.datas.keys() if k]


    def get_img_path_set(self):
        return {k for k in self.dataset.datas.keys() if k}


    def delete_dataset(self, caption_ext:str, filters:List[filters.Filter], delete_image:bool = False, delete_caption:bool = False, delete_backup:bool = False):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.delete_dataset_file(path, caption_ext, delete_image, delete_caption, delete_backup)
        
        if delete_image:
            self.dataset.remove(filtered_set)
            self.construct_tag_infos()


    def move_dataset(self, dest_dir:str, caption_ext:str, filters:List[filters.Filter], move_image:bool = False, move_caption:bool = False, move_backup:bool = False):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.move_dataset_file(path, caption_ext, dest_dir, move_image, move_caption, move_backup)
        
        if move_image:
            self.construct_tag_infos()

    
    def delete_dataset_file(self, img_path:str, caption_ext:str, delete_image:bool = False, delete_caption:bool = False, delete_backup:bool = False):
        if img_path not in self.dataset.datas.keys():
            return
        
        img_path_obj = Path(img_path)
        
        if delete_image:
            try:
                if img_path_obj.is_file():
                    if img_path in self.images:
                        self.images[img_path].close()
                        del self.images[img_path]
                    img_path_obj.unlink()
                    self.dataset.remove_by_path(img_path)
                    print(f'[tag-editor] Deleted {img_path_obj.absolute()}')
            except Exception as e:
                print(e)
        
        if delete_caption:
            try:
                txt_path_obj = img_path_obj.with_suffix(caption_ext)
                if txt_path_obj.is_file():
                    txt_path_obj.unlink()
                    print(f'[tag-editor] Deleted {txt_path_obj.absolute()}')
            except Exception as e:
                print(e)
        
        if delete_backup:
            try:
                for extnum in range(1000):
                    bak_path_obj = img_path_obj.with_suffix(f'.{extnum:0>3d}')
                    if bak_path_obj.is_file():
                        bak_path_obj.unlink()
                        print(f'[tag-editor] Deleted {bak_path_obj.absolute()}')
            except Exception as e:
                print(e)
    

    def move_dataset_file(self, img_path:str, caption_ext:str, dest_dir:str, move_image:bool = False, move_caption:bool = False, move_backup:bool = False):
        if img_path not in self.dataset.datas.keys():
            return
        
        img_path_obj = Path(img_path)
        dest_dir_obj = Path(dest_dir)

        if (move_image or move_caption or move_backup) and not dest_dir_obj.exists():
            dest_dir_obj.mkdir()

        if move_image:
            try:
                dst_path_obj = dest_dir_obj / img_path_obj.name
                if img_path_obj.is_file():
                    if img_path in self.images:
                        self.images[img_path].close()
                        del self.images[img_path]
                    img_path_obj.replace(dst_path_obj)
                    self.dataset.remove_by_path(img_path)
                    print(f'[tag-editor] Moved {img_path_obj.absolute()} -> {dst_path_obj.absolute()}')
            except Exception as e:
                print(e)
        
        if move_caption:
            try:
                txt_path_obj = img_path_obj.with_suffix(caption_ext)
                dst_path_obj = dest_dir_obj / txt_path_obj.name
                if txt_path_obj.is_file():
                    txt_path_obj.replace(dst_path_obj)
                    print(f'[tag-editor] Moved {txt_path_obj.absolute()} -> {dst_path_obj.absolute()}')
            except Exception as e:
                print(e)
        
        if move_backup:
            try:
                for extnum in range(1000):
                    bak_path_obj = img_path_obj.with_suffix(f'.{extnum:0>3d}')
                    dst_path_obj = dest_dir_obj / bak_path_obj.name
                    if bak_path_obj.is_file():
                        bak_path_obj.replace(dst_path_obj)
                        print(f'[tag-editor] Moved {bak_path_obj.absolute()} -> {dst_path_obj.absolute()}')
            except Exception as e:
                print(e)


    def load_dataset(self, img_dir:str, caption_ext:str, recursive:bool, load_caption_from_filename:bool, replace_new_line:bool, interrogate_method:InterrogateMethod, interrogator_names:List[str], threshold_booru:float, threshold_waifu:float, use_temp_dir:bool, kohya_json_path:Optional[str], max_res:float):
        self.clear()

        img_dir_obj = Path(img_dir)

        print(f'[tag-editor] Loading dataset from {img_dir_obj.absolute()}')
        if recursive:
            print(f'[tag-editor] Also loading from subdirectories.')
        
        try:
            filepaths = img_dir_obj.glob('**/*') if recursive else img_dir_obj.glob('*')
            filepaths = [p for p in filepaths if p.is_file()]
        except Exception as e:
            print(e)
            print('[tag-editor] Loading Aborted.')
            return

        self.dataset_dir = img_dir

        print(f'[tag-editor] Total {len(filepaths)} files under the directory including not image files.')

        def load_images(filepaths:List[Path]):
            imgpaths = []
            images = {}
            for img_path in filepaths:
                if img_path.suffix == caption_ext:
                    continue
                try:
                    img = Image.open(img_path)
                    if (max_res > 0):
                        img_res = int(max_res), int(max_res)
                        img.thumbnail(img_res)
                except:
                    continue
                else:
                    abs_path = str(img_path.absolute())
                    if not use_temp_dir and max_res <= 0:
                        img.already_saved_as = abs_path
                    images[abs_path] = img
                
                imgpaths.append(abs_path)
            return imgpaths, images
        
        def load_captions(imgpaths:List[str]):
            taglists = []
            for abs_path in imgpaths:
                img_path = Path(abs_path)
                text_path = img_path.with_suffix(caption_ext)
                caption_text = ''
                if interrogate_method != self.InterrogateMethod.OVERWRITE:
                    # from modules/textual_inversion/dataset.py, modified
                    if text_path.is_file():
                        caption_text = text_path.read_text('utf8')
                    elif load_caption_from_filename:
                        caption_text = img_path.stem
                        caption_text = re.sub(re_numbers_at_start, '', caption_text)
                        if self.re_word:
                            tokens = self.re_word.findall(caption_text)
                            caption_text = (shared.opts.dataset_filename_join_string or "").join(tokens)
                
                if replace_new_line:
                    caption_text = re_newlines.sub(',', caption_text)
                
                caption_tags =  [t.strip() for t in caption_text.split(',')]
                caption_tags = [t for t in caption_tags if t]
                taglists.append(caption_tags)

            return taglists
        
        try:
            captionings = []
            taggers = []
            if interrogate_method != self.InterrogateMethod.NONE:
                for it in INTERROGATORS:
                    if it.name() in interrogator_names:
                        it.start()
                        if isinstance(it, tagger.Tagger):
                            if isinstance(it, tagger.DeepDanbooru):
                                taggers.append((it, threshold_booru))
                            if isinstance(it, tagger.WaifuDiffusion):
                                taggers.append((it, threshold_waifu))
                        elif isinstance(it, captioning.Captioning):
                            captionings.append(it)

            if kohya_json_path:
                imgpaths, self.images, taglists = kohya_metadata.read(img_dir, kohya_json_path, use_temp_dir)
            else:
                imgpaths, self.images = load_images(filepaths)
                taglists = load_captions(imgpaths)
            
            for img_path, tags in zip(imgpaths, taglists):
                interrogate_tags = []
                img = self.images.get(img_path)
                if interrogate_method != self.InterrogateMethod.NONE and ((interrogate_method != self.InterrogateMethod.PREFILL) or (interrogate_method == self.InterrogateMethod.PREFILL and not tags)):
                    if img is None:
                        print(f'Failed to load image {img_path}. Interrogating is aborted.')
                    else:
                        img = img.convert('RGB')
                        for cap in captionings:
                            interrogate_tags += cap.predict(img)
                            
                        for tg, threshold in taggers:
                            interrogate_tags += [t for t in tg.predict(img, threshold).keys()]
                
                if interrogate_method == self.InterrogateMethod.OVERWRITE:
                    tags = interrogate_tags
                elif interrogate_method == self.InterrogateMethod.PREPEND:
                    tags = interrogate_tags + tags
                else:
                    tags = tags + interrogate_tags
                
                self.set_tags_by_image_path(img_path, tags)
            
        finally:
            if interrogate_method != self.InterrogateMethod.NONE:
                for cap in captionings:
                    cap.stop()
                for tg, _ in taggers:
                    tg.stop()
        
        for i, p in enumerate(sorted(self.dataset.datas.keys())):
            self.img_idx[p] = i

        self.construct_tag_infos()
        print(f'[tag-editor] Loading Completed: {len(self.dataset)} images found')
 

    def save_dataset(self, backup:bool, caption_ext:str, write_kohya_metadata:bool, meta_out_path:str, meta_in_path:Optional[str], meta_overwrite:bool, meta_as_caption:bool, meta_full_path:bool):
        if len(self.dataset) == 0:
            return (0, 0, '')

        saved_num = 0
        backup_num = 0
        for data in self.dataset.datas.values():
            img_path, tags = Path(data.imgpath), data.tags
            txt_path = img_path.with_suffix(caption_ext)
            # make backup
            if backup and txt_path.is_file():
                for extnum in range(1000):
                    bak_path = img_path.with_suffix(f'.{extnum:0>3d}')
                    if not bak_path.is_file():
                        break
                    else:
                        bak_path = None
                if bak_path is None:
                    print(f"[tag-editor] There are too many backup files with same filename. A backup file of {txt_path} cannot be created.")
                else:
                    try:
                        txt_path.rename(bak_path)
                    except Exception as e:
                        print(e)
                        print(f"[tag-editor] A backup file of {txt_path} cannot be created.")
                    else:
                        backup_num += 1
            # save
            try:
                txt_path.write_text(', '.join(tags), 'utf8')
            except Exception as e:
                print(e)
                print(f"[tag-editor] Warning: {txt_path} cannot be saved.")
            else:
                saved_num += 1
        print(f'[tag-editor] Backup text files: {backup_num}/{len(self.dataset)} under {self.dataset_dir}')
        print(f'[tag-editor] Saved text files: {saved_num}/{len(self.dataset)} under {self.dataset_dir}')
        
        if(write_kohya_metadata):
            kohya_metadata.write(dataset=self.dataset, dataset_dir=self.dataset_dir, out_path=meta_out_path, in_path=meta_in_path, overwrite=meta_overwrite, save_as_caption=meta_as_caption, use_full_path=meta_full_path)
            print(f'[tag-editor] Saved json metadata file in {meta_out_path}')
        return (saved_num, len(self.dataset), self.dataset_dir)


    def clear(self):
        self.dataset.clear()
        self.tag_counts.clear()
        self.tag_tokens.clear()
        self.img_idx.clear()
        self.dataset_dir = ''
        for img in self.images:
            if isinstance(img, Image.Image):
                img.close()
        self.images.clear()


    def construct_tag_infos(self):
        self.tag_counts = {}
        update_token_count = self.raw_clip_token_used is None or self.raw_clip_token_used != shared.opts.dataset_editor_use_raw_clip_token

        if update_token_count:
            self.tag_tokens.clear()

        for data in self.dataset.datas.values():
            for tag in data.tags:
                if tag in self.tag_counts.keys():
                    self.tag_counts[tag] += 1
                else:
                    self.tag_counts[tag] = 1
                if tag not in self.tag_tokens:
                    self.tag_tokens[tag] = clip_tokenizer.tokenize(tag, shared.opts.dataset_editor_use_raw_clip_token)
        self.raw_clip_token_used = shared.opts.dataset_editor_use_raw_clip_token
