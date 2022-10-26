import os
import re
from typing import Optional, List, Tuple
from modules import shared
from modules.textual_inversion.dataset import re_numbers_at_start

re_tags = re.compile(r'^(.+) \[\d+\]$')

class DatasetTagEditor:
    def __init__(self):
        # from modules.textual_inversion.dataset
        self.re_word = re.compile(shared.opts.dataset_filename_word_regex) if len(shared.opts.dataset_filename_word_regex) > 0 else None
        self.img_tag_dict = dict()
        self.tag_counts = dict()


    def get_tags(self):
        if len(self.tag_counts) == 0 and len(self.img_tag_dict) == 0:
            self.construct_tag_counts()
        return [key for key in self.tag_counts.keys()]


    def get_tags_by_image_path(self, imgpath: str) -> Optional[List[str]]:
        return self.img_tag_dict.get(imgpath)

    
    def set_tags_by_image_path(self, imgpath: str, tags: List[str]):
        self.img_tag_dict[imgpath] = tags
        self.construct_tag_counts()
    

    def write_tags(self, tags: List[str]) -> List[str]:
        if tags:
            return [f'{tag} [{self.tag_counts.get(tag)}]' for tag in tags if tag]
        else:
            return []


    def read_tags(self, tags:List[str]) -> List[str]:
        if tags:
            tags = [re_tags.match(tag).group(1) for tag in tags if tag]
            return [t for t in tags if t]
        else:
            return []


    def sort_tags(self, tags: List[str], sort_by: str, sort_order: str) -> List[str]:
        if sort_by == 'Alphabetical Order':
            if sort_order == 'Ascending':
                tags.sort(reverse=False)
                return tags
            elif sort_order == 'Descending':
                tags.sort(reverse=True)
                return tags
        elif sort_by == 'Frequency':
            if sort_order == 'Ascending':
                tags.sort(key=lambda t:(self.tag_counts.get(t), t), reverse=False)
                return tags
            elif sort_order == 'Descending':
                tags.sort(reverse=False)
                tags.sort(key=lambda t:(-self.tag_counts.get(t), t), reverse=False)
                return tags
        return []


    def get_filtered_imgpath_and_tags(self, filter_tags: Optional[List[str]] = None, filter_word: Optional[str] = None) -> Tuple[List[str], List[str]]:
        img_paths = []

        if filter_tags and len(filter_tags) > 0:
            for path, tags in self.img_tag_dict.items():
                flag = True
                for v in filter_tags:
                    if v not in tags:
                        flag = False
                        break
                if flag:
                    img_paths.append(path)
            tag_list = self.construct_tag_list_from(img_paths)
        else:
            tag_list = self.get_tags()
            img_paths = self.get_img_path_list()

        if filter_word:
            # all tags with filter_word
            result = [tag for tag in tag_list if filter_word in tag]
            return (img_paths, result)
        else:
            return (img_paths, tag_list)


    def replace_tags(self, search_tags: List[str], replace_tags: List[str], filter_tags: Optional[List[str]] = None, append_to_begin: bool = False):
        img_paths, _ = self.get_filtered_imgpath_and_tags(filter_tags=filter_tags)
        tags_to_append = replace_tags[len(search_tags):]
        tags_to_remove = search_tags[len(replace_tags):]
        tags_to_replace = {}
        for i in range(min(len(search_tags), len(replace_tags))):
            if replace_tags[i] is None or replace_tags[i] == '':
                tags_to_remove.append(search_tags[i])
            else:
                tags_to_replace[search_tags[i]] = replace_tags[i]
        for img_path in img_paths:
            tags_removed = [t for t in self.img_tag_dict.get(img_path) if t not in tags_to_remove]
            tags_replaced = [tags_to_replace.get(t) if t in tags_to_replace.keys() else t for t in tags_removed]
            self.img_tag_dict[img_path] = tags_to_append + tags_replaced if append_to_begin else tags_replaced + tags_to_append
        
        self.construct_tag_counts()


    def get_img_path_list(self) -> List[str]:
        keys = []
        for key in self.img_tag_dict.keys():
            keys.append(key)
        return keys


    def load_dataset(self, img_dir: str):
        self.clear()
        try:
            f_list = os.listdir(img_dir)
        except:
            return
        for img_filebasename in f_list:
            img_path = os.path.join(img_dir, img_filebasename)
            img_dir = os.path.dirname(img_path)
            img_filename, img_ext = os.path.splitext(img_filebasename)
            if os.path.isfile(img_path) and (img_ext == '.png'):
                text_filename = os.path.join(img_dir, img_filename+'.txt')
                # from modules/textual_inversion/dataset.py
                if os.path.exists(text_filename) and os.path.isfile(text_filename):
                    with open(text_filename, "r", encoding="utf8") as ftxt:
                        filename_text = ftxt.read()
                else:
                    filename_text = img_filename
                    filename_text = re.sub(re_numbers_at_start, '', filename_text)
                    if self.re_word:
                        tokens = self.re_word.findall(filename_text)
                        filename_text = (shared.opts.dataset_filename_join_string or "").join(tokens)

                self.img_tag_dict[img_path] = [t.strip() for t in filename_text.split(',')]

        self.construct_tag_counts()

 
    def save_dataset(self, backup: bool) -> Tuple[int, int, str]:
        saved_num = 0
        backup_num = 0
        for img_path, tags in self.img_tag_dict.items():
            img_dir = os.path.dirname(img_path)
            img_path_noext, _ = os.path.splitext(os.path.basename(img_path))
            txt_path = os.path.join(img_dir, img_path_noext + '.txt')
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
        
        print(f'Backup text files: {backup_num}/{len(self.img_tag_dict)} in {img_dir}')
        print(f'Saved text files: {saved_num}/{len(self.img_tag_dict)} in {img_dir}')
        return (saved_num, len(self.img_tag_dict), img_dir)


    def clear(self):
        self.img_tag_dict.clear()
        self.tag_counts.clear()


    def construct_tag_counts(self):
        self.tag_counts = dict()
        for tags in self.img_tag_dict.values():
            for tag in tags:
                if tag in self.tag_counts.keys():
                    self.tag_counts[tag] += 1
                else:
                    self.tag_counts[tag] = 1


    def construct_tag_list_from(self, img_paths: List[str]) -> List[str]:
        # unique tags
        tags = set(tag for path in img_paths for tag in self.img_tag_dict.get(path))
        return [t for t in tags]
