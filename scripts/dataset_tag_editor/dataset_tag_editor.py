import os
import re
from typing import Optional, List, Tuple, Set
from modules import shared
from modules.shared import opts, cmd_opts
from modules.textual_inversion.dataset import re_numbers_at_start
from PIL import Image
from enum import Enum

if cmd_opts.deepdanbooru:
    import modules.deepbooru as deepbooru

re_tags = re.compile(r'^(.+) \[\d+\]$')


class InterrogateMethod(Enum):
    NONE = 0
    PREFILL = 1
    OVERWRITE = 2
    PREPEND = 3
    APPEND = 4


def interrogate_image_clip(path):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        return shared.interrogator.interrogate(img)


def interrogate_image_booru(path):
    try:
        img = Image.open(path).convert('RGB')
    except:
        return ''
    else:
        return deepbooru.get_deepbooru_tags(img)


def get_filepath_set(dir: str, recursive: bool) -> Set[str]:
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
        self.img_tag_dict = {}
        self.img_tag_set_dict = {}
        self.tag_counts = {}
        self.img_filter_img_path_set = set()
        self.dataset_dir = ''


    def get_tag_list(self) -> List[str]:
        if len(self.tag_counts) == 0 and len(self.img_tag_dict) > 0:
            self.construct_tag_counts()
        return [key for key in self.tag_counts.keys()]


    def get_tag_set(self) -> Set[str]:
        if len(self.tag_counts) == 0 and len(self.img_tag_dict) > 0:
            self.construct_tag_counts()
        return {key for key in self.tag_counts.keys()}


    def get_tags_by_image_path(self, imgpath: str) -> Optional[List[str]]:
        return self.img_tag_dict.get(imgpath)

    
    def set_tags_by_image_path(self, imgpath: str, tags: List[str]):
        self.img_tag_dict[imgpath] = tags
        self.img_tag_set_dict[imgpath] = {t for t in tags if t}
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
                return sorted(tags, reverse=False)
            elif sort_order == 'Descending':
                return sorted(tags, reverse=True)
        elif sort_by == 'Frequency':
            if sort_order == 'Ascending':
                return sorted(tags, key=lambda t:(self.tag_counts.get(t), t), reverse=False)
            elif sort_order == 'Descending':
                return sorted(tags, key=lambda t:(-self.tag_counts.get(t), t), reverse=False)
        return []


    def set_img_filter_img_path(self, path:Optional[Set[str]] = None):
        if path:
            self.img_filter_img_path_set = self.get_img_path_set() & path
        else:
            self.img_filter_img_path_set = self.get_img_path_set()


    def get_img_filter_img_path(self) -> Set[str]:
        return self.img_filter_img_path_set


    def get_filtered_imgpath_and_tags(self, filter_tags: Optional[List[str]] = None, filter_word: Optional[str] = None) -> Tuple[List[str], Set[str]]:
        img_paths = self.get_img_filter_img_path().copy()
        if filter_tags and len(filter_tags) > 0:
            filter_tag_set = set(filter_tags)
            for path in self.get_img_filter_img_path():
                tags = self.img_tag_set_dict.get(path)
                if not filter_tag_set.issubset(tags):
                    img_paths.remove(path)
        
        tag_set = self.construct_tag_set_from(img_paths)
        img_paths = sorted(img_paths)

        if filter_word:
            # all tags with filter_word
            tag_set = {tag for tag in tag_set if filter_word in tag}
        
        return (img_paths, tag_set)


    def replace_tags(self, search_tags: List[str], replace_tags: List[str], filter_tags: Optional[List[str]] = None, prepend: bool = False):
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
            self.set_tags_by_image_path(img_path, tags_to_append + tags_replaced if prepend else tags_replaced + tags_to_append)
        
        self.construct_tag_counts()


    def get_img_path_list(self) -> List[str]:
        return [k for k in self.img_tag_dict.keys() if k]


    def get_img_path_set(self) -> Set[str]:
        return {k for k in self.img_tag_dict.keys() if k}



    def load_dataset(self, img_dir: str, recursive: bool = False, load_caption_from_filename: bool = True, interrogate_method: InterrogateMethod = InterrogateMethod.NONE, use_booru: bool = True, use_clip: bool = False):
        self.clear()
        print(f'Loading dataset from {img_dir}')
        if recursive:
            print(f'Also loading from subdirectories.')
        
        try:
            filepath_set = get_filepath_set(dir=img_dir, recursive=recursive)
        except Exception as e:
            print(e)
            print('Loading Aborted.')
            return

        self.dataset_dir = img_dir

        if use_booru and not cmd_opts.deepdanbooru:
            print('Cannot use DeepDanbooru without --deepdanbooru commandline option.')

        print(f'Total {len(filepath_set)} files under the directory including not image files.')

        def load_images(filepath_set: set[str]):
            for img_path in filepath_set:
                img_dir = os.path.dirname(img_path)
                img_filename, img_ext = os.path.splitext(os.path.basename(img_path))
                ext_supported = {e for e, str in Image.registered_extensions().items() if str in Image.OPEN}
                if img_ext not in ext_supported:
                    continue
                text_filename = os.path.join(img_dir, img_filename+'.txt')
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
                
                if interrogate_method != InterrogateMethod.NONE and ((interrogate_method != InterrogateMethod.PREFILL) or (interrogate_method == InterrogateMethod.PREFILL and not caption_text)):
                    try:
                        img = Image.open(img_path).convert('RGB')
                    except Exception as e:
                        print(e)
                    else:
                        interrogate_text = ''
                        if use_clip:
                            interrogate_text += shared.interrogator.generate_caption(img)
                            
                        if use_booru and cmd_opts.deepdanbooru:
                            tmp = deepbooru.get_tags_from_process(img)
                            interrogate_text += (', ' if interrogate_text and tmp else '') + tmp

                        if interrogate_method == InterrogateMethod.OVERWRITE:
                            caption_text = interrogate_text
                        elif interrogate_method == InterrogateMethod.PREPEND:
                            caption_text = interrogate_text + (', ' if interrogate_text and caption_text else '') + caption_text
                        else:
                            caption_text += (', ' if interrogate_text and caption_text else '') + interrogate_text
                
                self.set_tags_by_image_path(img_path, [t.strip() for t in caption_text.split(',')])

        try:
            if interrogate_method != InterrogateMethod.NONE:
                if use_clip:
                    shared.interrogator.load()
                if use_booru and cmd_opts.deepdanbooru:
                    db_opts = deepbooru.create_deepbooru_opts()
                    db_opts[deepbooru.OPT_INCLUDE_RANKS] = False
                    deepbooru.create_deepbooru_process(opts.interrogate_deepbooru_score_threshold, db_opts)

            load_images(filepath_set = filepath_set)
            
        finally:
            if interrogate_method != InterrogateMethod.NONE:
                if use_clip:
                    shared.interrogator.send_blip_to_ram()
                if use_booru and cmd_opts.deepdanbooru:
                    deepbooru.release_process()

        self.construct_tag_counts()
        self.set_img_filter_img_path()
        print(f'Loading Completed.')
 

    def save_dataset(self, backup: bool) -> Tuple[int, int, str]:
        if len(self.img_tag_dict) == 0:
            return (0, 0, '')

        saved_num = 0
        backup_num = 0
        img_dir = ''
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
        
        print(f'Backup text files: {backup_num}/{len(self.img_tag_dict)} under {self.dataset_dir}')
        print(f'Saved text files: {saved_num}/{len(self.img_tag_dict)} under {self.dataset_dir}')
        return (saved_num, len(self.img_tag_dict), self.dataset_dir)


    def clear(self):
        self.img_tag_dict.clear()
        self.img_tag_set_dict.clear()
        self.tag_counts.clear()
        self.img_filter_img_path_set.clear()
        self.dataset_dir = ''


    def construct_tag_counts(self):
        self.tag_counts = {}
        for tags in self.img_tag_dict.values():
            for tag in tags:
                if tag in self.tag_counts.keys():
                    self.tag_counts[tag] += 1
                else:
                    self.tag_counts[tag] = 1


    def construct_tag_set_from(self, img_paths: List[str]) -> Set[str]:
        # unique tags
        return {tag for path in img_paths for tag in self.img_tag_set_dict.get(path) if tag}
