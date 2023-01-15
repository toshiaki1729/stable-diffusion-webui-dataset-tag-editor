import os
import re
from typing import List, Set, Optional
from modules import shared
from modules.textual_inversion.dataset import re_numbers_at_start
from PIL import Image
from enum import Enum

from scripts.dynamic_import import dynamic_import
ds = dynamic_import('scripts/dataset_tag_editor/dataset.py')
tagger = dynamic_import('scripts/dataset_tag_editor/tagger.py')
captioning = dynamic_import('scripts/dataset_tag_editor/captioning.py')
filters = dynamic_import('scripts/dataset_tag_editor/filters.py')


re_tags = re.compile(r'^(.+) \[\d+\]$')


class InterrogateMethod(Enum):
    NONE = 0
    PREFILL = 1
    OVERWRITE = 2
    PREPEND = 3
    APPEND = 4


def interrogate_image_blip(path):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        with captioning.BLIP() as cap:
            res = cap.predict(img)
        return ', '.join(res)


def interrogate_image_git(path):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        with captioning.GITLarge() as cap:
            res = cap.predict(img)
        return ', '.join(res)


def interrogate_image_booru(path, threshold):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        with tagger.DeepDanbooru() as tg:
            res = tg.predict(img, threshold=threshold)
        return ', '.join(tagger.get_arranged_tags(res))


def interrogate_image_waifu(path, threshold):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        with tagger.WaifuDiffusion() as tg:
            res = tg.predict(img, threshold=threshold)
        return ', '.join(tagger.get_arranged_tags(res))
            

def get_filepath_set(dir: str, recursive: bool):
    if recursive:
        dirs_to_see = [dir]
        result = set()
        while len(dirs_to_see) > 0:
            current_dir = dirs_to_see.pop()
            basenames = os.listdir(current_dir)
            paths = {os.path.join(current_dir, basename) for basename in basenames}
            for path in paths:
                if os.path.isdir(path):
                    dirs_to_see.append(path)
                elif os.path.isfile(path):
                    result.add(path)
        return result
    else:
        basenames = os.listdir(dir)
        paths = {os.path.join(dir, basename) for basename in basenames}
        return {path for path in paths if os.path.isfile(path)}


class DatasetTagEditor:
    def __init__(self):
        # from modules.textual_inversion.dataset
        self.re_word = re.compile(shared.opts.dataset_filename_word_regex) if len(shared.opts.dataset_filename_word_regex) > 0 else None
        self.dataset = ds.Dataset()
        self.img_idx = dict()
        self.tag_counts = {}
        self.dataset_dir = ''
        self.caption_ext = '.txt'

    def get_tag_list(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_counts()
        return [key for key in self.tag_counts.keys()]


    def get_tag_set(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_counts()
        return {key for key in self.tag_counts.keys()}


    def get_tags_by_image_path(self, imgpath: str):
        return self.dataset.get_data_tags(imgpath)

    
    def set_tags_by_image_path(self, imgpath: str, tags: List[str]):
        self.dataset.append_data(ds.Data(imgpath, ','.join(tags)))
        self.construct_tag_counts()
    

    def write_tags(self, tags: List[str]):
        if tags:
            return [f'{tag} [{self.tag_counts.get(tag) or 0}]' for tag in tags if tag]
        else:
            return []


    def read_tags(self, tags:List[str]):
        if tags:
            tags = [re_tags.match(tag).group(1) for tag in tags if tag]
            return [t for t in tags if t]
        else:
            return []


    def sort_tags(self, tags: List[str], sort_by: str, sort_order: str):
        if sort_by == 'Alphabetical Order':
            if sort_order == 'Ascending':
                return sorted(tags, reverse=False)
            elif sort_order == 'Descending':
                return sorted(tags, reverse=True)
        elif sort_by == 'Frequency':
            if sort_order == 'Ascending':
                return sorted(tags, key=lambda t:(self.tag_counts.get(t), t), reverse=False)
            elif sort_order == 'Descending':
                return sorted(tags, key=lambda t:(-self.tag_counts.get(t), t), reverse=False)
        return []


    def get_filtered_imgpaths(self, filters: List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        img_paths = sorted(filtered_set.datas.keys())
        
        return img_paths


    def get_filtered_imgindices(self, filters: List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        img_paths = sorted(filtered_set.datas.keys())
        
        return [self.img_idx.get(p) for p in img_paths]


    def get_filtered_tags(self, filters: List[filters.Filter] = [], filter_word: str = '', filter_tags = True):
        if filter_tags:
            filtered_set = self.dataset.copy()
            for filter in filters:
                filtered_set.filter(filter)
            tags = filtered_set.get_tagset()
        else:
            tags = self.dataset.get_tagset()
        
        return {tag for tag in tags if filter_word in tag}
        

    def get_common_tags(self, filters: List[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        
        result = filtered_set.get_tagset()
        for d in filtered_set.datas.values():
            result &= d.tagset

        return sorted(result)
    

    def replace_tags(self, search_tags: List[str], replace_tags: List[str], filters: List[filters.Filter] = [], prepend: bool = False):
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
        
        self.construct_tag_counts()

    def get_replaced_tagset(self, tags: Set[str], search_tags: List[str], replace_tags: List[str]):
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


    def search_and_replace_caption(self, search_text: str, replace_text: str, filters: List[filters.Filter] = [], use_regex: bool = False):
        img_paths = self.get_filtered_imgpaths(filters=filters)
        
        for img_path in img_paths:
            caption = ', '.join(self.dataset.get_data_tags(img_path))
            if use_regex:
                caption = [t.strip() for t in re.sub(search_text, replace_text, caption).split(',')]
            else:
                caption = [t.strip() for t in caption.replace(search_text, replace_text).split(',')]
            caption = [t for t in caption if t]
            self.set_tags_by_image_path(img_path, caption)
        
        self.construct_tag_counts()


    def search_and_replace_selected_tags(self, search_text: str, replace_text: str, selected_tags: Optional[Set[str]], filters: List[filters.Filter] = [], use_regex: bool = False):
        img_paths = self.get_filtered_imgpaths(filters=filters)

        for img_path in img_paths:
            tags = self.dataset.get_data_tags(img_path)
            tags = self.search_and_replace_tag_list(search_text, replace_text, tags, selected_tags, use_regex)
            self.set_tags_by_image_path(img_path, tags)
        
        self.construct_tag_counts()

    
    def search_and_replace_tag_list(self, search_text: str, replace_text: str, tags: List[str], selected_tags: Optional[Set[str]] = None, use_regex: bool = False):
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
        return [t for t in tags if t]        


    def search_and_replace_tag_set(self, search_text: str, replace_text: str, tags: Set[str], selected_tags: Optional[Set[str]] = None, use_regex: bool = False):
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
        return {t for t in tags if t}
    

    def remove_duplicated_tags(self, filters: List[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = []
            for t in tags:
                if t not in res:
                    res.append(t)
            self.set_tags_by_image_path(path, res)
    

    def remove_tags(self, tags: Set[str], filters: List[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            res = self.dataset.get_data_tags(path)
            res = [t for t in res if t not in tags]
            self.set_tags_by_image_path(path, res)


    def get_img_path_list(self):
        return [k for k in self.dataset.datas.keys() if k]


    def get_img_path_set(self):
        return {k for k in self.dataset.datas.keys() if k}


    def delete_dataset(self, caption_ext: str, filters: List[filters.Filter], delete_image: bool = False, delete_caption: bool = False, delete_backup: bool = False):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.delete_dataset_file(path, caption_ext, delete_image, delete_caption, delete_backup)
        
        if delete_image:
            self.dataset.remove(filtered_set)
            print(list(self.dataset.datas.values()))
            self.construct_tag_counts()


    def move_dataset(self, dest_dir: str, caption_ext:str, filters: List[filters.Filter], move_image: bool = False, move_caption: bool = False, move_backup: bool = False):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.move_dataset_file(path, caption_ext, dest_dir, move_image, move_caption, move_backup)
        
        if move_image:
            self.construct_tag_counts()

    
    def delete_dataset_file(self, img_path: str, caption_ext:str, delete_image: bool = False, delete_caption: bool = False, delete_backup: bool = False):
        if img_path not in self.dataset.datas.keys():
            return
        
        if delete_image:
            try:
                if os.path.exists(img_path) and os.path.isfile(img_path):
                    os.remove(img_path)
                    self.dataset.remove_by_path(img_path)
                    print(f'Deleted {img_path}')
            except Exception as e:
                print(e)
        
        if delete_caption:
            try:
                filepath_noext, _ = os.path.splitext(img_path)
                txt_path = filepath_noext + caption_ext
                if os.path.exists(txt_path) and os.path.isfile(txt_path):
                    os.remove(txt_path)
                    print(f'Deleted {txt_path}')
            except Exception as e:
                print(e)
        
        if delete_backup:
            try:
                filepath_noext, _ = os.path.splitext(img_path)
                for extnum in range(1000):
                    bak_path = filepath_noext + f'.{extnum:0>3d}'
                    if os.path.exists(bak_path) and os.path.isfile(bak_path):
                        os.remove(bak_path)
                        print(f'Deleted {bak_path}')
            except Exception as e:
                print(e)
    

    def move_dataset_file(self, img_path: str, caption_ext: str, dest_dir: str, move_image: bool = False, move_caption: bool = False, move_backup: bool = False):
        if img_path not in self.dataset.datas.keys():
            return
        
        if (move_image or move_caption or move_backup) and not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        if move_image:
            try:
                dst_path = os.path.join(dest_dir, os.path.basename(img_path))
                if os.path.exists(img_path) and os.path.isfile(img_path):
                    os.replace(img_path, dst_path)
                    self.dataset.remove_by_path(img_path)
                    print(f'Moved {img_path} -> {dst_path}')
            except Exception as e:
                print(e)
        
        if move_caption:
            try:
                filepath_noext, _ = os.path.splitext(img_path)
                txt_path = filepath_noext + caption_ext
                dst_path = os.path.join(dest_dir, os.path.basename(txt_path))
                if os.path.exists(txt_path) and os.path.isfile(txt_path):
                    os.replace(txt_path, dst_path)
                    print(f'Moved {txt_path} -> {dst_path}')
            except Exception as e:
                print(e)
        
        if move_backup:
            try:
                filepath_noext, _ = os.path.splitext(img_path)
                for extnum in range(1000):
                    bak_path = filepath_noext + f'.{extnum:0>3d}'
                    dst_path = os.path.join(dest_dir, os.path.basename(bak_path))
                    if os.path.exists(bak_path) and os.path.isfile(bak_path):
                        os.replace(bak_path, dst_path)
                        print(f'Moved {bak_path} -> {dst_path}')
            except Exception as e:
                print(e)


    def load_dataset(self, img_dir: str, caption_ext:str,  recursive: bool, load_caption_from_filename: bool, interrogate_method: InterrogateMethod, use_booru: bool, use_blip: bool, use_git:bool, use_waifu: bool, threshold_booru: float, threshold_waifu: float):
        self.clear()
        print(f'Loading dataset from {img_dir}')
        if recursive:
            print(f'Also loading from subdirectories.')

        self.caption_ext = caption_ext
        
        try:
            filepath_set = get_filepath_set(dir=img_dir, recursive=recursive)
        except Exception as e:
            print(e)
            print('Loading Aborted.')
            return

        self.dataset_dir = img_dir

        print(f'Total {len(filepath_set)} files under the directory including not image files.')

        def load_images(filepath_set: Set[str], captionings: List[captioning.Captioning], taggers: List[tagger.Tagger]):
            for img_path in filepath_set:
                img_dir = os.path.dirname(img_path)
                img_filename, img_ext = os.path.splitext(os.path.basename(img_path))
                if img_ext == self.caption_ext:
                    continue

                try:
                    img = Image.open(img_path)
                except:
                    continue
                else:
                    img.close()
                
                text_filename = os.path.join(img_dir, img_filename+self.caption_ext)
                caption_text = ''
                if interrogate_method != InterrogateMethod.OVERWRITE:
                    # from modules/textual_inversion/dataset.py, modified
                    if os.path.exists(text_filename) and os.path.isfile(text_filename):
                        with open(text_filename, "r", encoding="utf8") as ftxt:
                            caption_text = ftxt.read()
                    elif load_caption_from_filename:
                        caption_text = img_filename
                        caption_text = re.sub(re_numbers_at_start, '', caption_text)
                        if self.re_word:
                            tokens = self.re_word.findall(caption_text)
                            caption_text = (shared.opts.dataset_filename_join_string or "").join(tokens)
                
                interrogate_tags = []
                caption_tags =  [t.strip() for t in caption_text.split(',')]
                caption_tags = [t for t in caption_tags if t]
                if interrogate_method != InterrogateMethod.NONE and ((interrogate_method != InterrogateMethod.PREFILL) or (interrogate_method == InterrogateMethod.PREFILL and not caption_tags)):
                    try:
                        img = Image.open(img_path).convert('RGB')
                    except Exception as e:
                        print(e)
                        print(f'Cannot interrogate file: {img_path}')
                    else:
                        for cap in captionings:
                            interrogate_tags += cap.predict(img)
                            
                        for tg, threshold in taggers:
                            probs = tg.predict(img)
                            interrogate_tags += [t for t, p in probs.items() if p > threshold]

                        img.close()
                
                if interrogate_method == InterrogateMethod.OVERWRITE:
                    tags = interrogate_tags
                elif interrogate_method == InterrogateMethod.PREPEND:
                    tags = interrogate_tags + caption_tags
                else:
                    tags = caption_tags + interrogate_tags
                self.set_tags_by_image_path(img_path, tags)
        
        try:
            captionings = []
            taggers = []
            if interrogate_method != InterrogateMethod.NONE:
                if use_blip:
                    cap = captioning.BLIP()
                    cap.start()
                    captionings.append(cap)
                if use_git:
                    cap = captioning.GITLarge()
                    cap.start()
                    captionings.append(cap)
                if use_booru:
                    tg = tagger.DeepDanbooru()
                    tg.start()
                    taggers.append((tg, threshold_booru))
                if use_waifu:
                    tg = tagger.WaifuDiffusion()
                    tg.start()
                    taggers.append((tg, threshold_waifu))

            load_images(filepath_set=filepath_set, captionings=captionings, taggers=taggers)
            
        finally:
            if interrogate_method != InterrogateMethod.NONE:
                for cap in captionings:
                    cap.stop()
                for tg, _ in taggers:
                    tg.stop()
        
        for i, p in enumerate(sorted(self.dataset.datas.keys())):
            self.img_idx[p] = i

        self.construct_tag_counts()
        print(f'Loading Completed: {len(self.dataset)} images found')
 

    def save_dataset(self, backup: bool):
        if len(self.dataset) == 0:
            return (0, 0, '')

        saved_num = 0
        backup_num = 0
        img_dir = ''
        for data in self.dataset.datas.values():
            img_path, tags = data.imgpath, data.tags
            img_dir = os.path.dirname(img_path)
            img_path_noext, _ = os.path.splitext(os.path.basename(img_path))
            txt_path = os.path.join(img_dir, img_path_noext + self.caption_ext)
            # make backup
            if backup and os.path.exists(txt_path) and os.path.isfile(txt_path):
                for extnum in range(1000):
                    bak_path = os.path.join(img_dir, f'{img_path_noext}.{extnum:0>3d}')
                    if not os.path.exists(bak_path) or not os.path.isfile(bak_path):
                        break
                    else:
                        bak_path = None
                if bak_path is None:
                    print(f"There are too many backup files with same filename. A backup file of {txt_path} cannot be created.")
                else:
                    try:
                        os.rename(txt_path, bak_path)
                    except Exception as e:
                        print(e)
                        print(f"A backup file of {txt_path} cannot be created.")
                    else:
                        backup_num += 1
            # save
            try:
                with open(txt_path, "w", encoding="utf8") as file:
                    file.write(', '.join(tags))
            except Exception as e:
                print(e)
                print(f"Warning: {txt_path} cannot be saved.")
            else:
                saved_num += 1
        
        print(f'Backup text files: {backup_num}/{len(self.dataset)} under {self.dataset_dir}')
        print(f'Saved text files: {saved_num}/{len(self.dataset)} under {self.dataset_dir}')
        return (saved_num, len(self.dataset), self.dataset_dir)


    def clear(self):
        self.dataset.clear()
        self.tag_counts.clear()
        self.img_idx.clear()
        self.dataset_dir = ''


    def construct_tag_counts(self):
        self.tag_counts = {}
        for data in self.dataset.datas.values():
            for tag in data.tags:
                if tag in self.tag_counts.keys():
                    self.tag_counts[tag] += 1
                else:
                    self.tag_counts[tag] = 1
