from pathlib import Path
import re, sys
from typing import List, Set, Optional
from enum import Enum

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from PIL import Image
from tqdm import tqdm

from modules import shared
from modules.textual_inversion.dataset import re_numbers_at_start

from scripts.singleton import Singleton

from scripts import logger, utilities
from scripts.paths import paths

from . import (
    filters,
    dataset as ds,
    kohya_finetune_metadata as kohya_metadata,
    taggers_builtin
)
from .custom_scripts import CustomScripts
from .interrogator_names import BLIP2_CAPTIONING_NAMES, WD_TAGGERS, WD_TAGGERS_TIMM
from scripts.tokenizer import clip_tokenizer
from scripts.tagger import Tagger

re_tags = re.compile(r"^([\s\S]+?)( \[\d+\])?$")
re_newlines = re.compile(r"[\r\n]+")

def get_square_rgb(data:Image.Image):
    data_rgb = utilities.get_rgb_image(data)
    size = max(data.size)
    return utilities.resize_and_fill(data_rgb, (size, size))

class DatasetTagEditor(Singleton):
    class SortBy(Enum):
        ALPHA = "Alphabetical Order"
        FREQ = "Frequency"
        LEN = "Length"
        TOKEN = "Token Length"

    class SortOrder(Enum):
        ASC = "Ascending"
        DESC = "Descending"

    class InterrogateMethod(Enum):
        NONE = 0
        PREFILL = 1
        OVERWRITE = 2
        PREPEND = 3
        APPEND = 4

    def __init__(self):
        # from modules.textual_inversion.dataset
        self.re_word = (
            re.compile(shared.opts.dataset_filename_word_regex)
            if len(shared.opts.dataset_filename_word_regex) > 0
            else None
        )
        self.dataset = ds.Dataset()
        self.img_idx = dict()
        self.tag_counts = {}
        self.dataset_dir = ""
        self.images = {}
        self.tag_tokens = {}
        self.raw_clip_token_used = None
    
    def load_interrogators(self):
        custom_tagger_scripts = CustomScripts(paths.userscript_path / "taggers")
        custom_taggers:list[Tagger] = custom_tagger_scripts.load_derived_classes(Tagger)
        logger.write(f"Custom taggers loaded: {[tagger().name() for tagger in custom_taggers]}")

        def read_wd_batchsize(name:str):
            if "vit" in name:
                return shared.opts.dataset_editor_batch_size_vit
            elif "convnext" in name:
                return shared.opts.dataset_editor_batch_size_convnext
            elif "swinv2" in name:
                return shared.opts.dataset_editor_batch_size_swinv2
        
        self.INTERROGATORS = (
            [taggers_builtin.BLIP()]
            + [taggers_builtin.BLIP2(name) for name in BLIP2_CAPTIONING_NAMES]
            + [taggers_builtin.GITLarge()]
            + [taggers_builtin.DeepDanbooru()]
            + [
                taggers_builtin.WaifuDiffusion(name, threshold)
                for name, threshold in WD_TAGGERS.items()
            ]
            + [
                taggers_builtin.WaifuDiffusionTimm(name, threshold, int(read_wd_batchsize(name)))
                for name, threshold in WD_TAGGERS_TIMM.items()
            ]
            + [taggers_builtin.Z3D_E621()]
            + [cls_tagger() for cls_tagger in custom_taggers]
        )
        self.INTERROGATOR_NAMES = [it.name() for it in self.INTERROGATORS]

    def interrogate_image(self, path: str, interrogator_name: str, threshold_booru, threshold_wd, threshold_z3d):
        try:
            img = get_square_rgb(Image.open(path))
        except:
            return ""
        else:
            for it in self.INTERROGATORS:
                if it.name() == interrogator_name:
                    if isinstance(it, taggers_builtin.DeepDanbooru):
                        with it as tg:
                            res = tg.predict(img, threshold_booru)
                    elif isinstance(it, taggers_builtin.WaifuDiffusion) or isinstance(it, taggers_builtin.WaifuDiffusionTimm):
                        with it as tg:
                            res = tg.predict(img, threshold_wd)
                    elif isinstance(it, taggers_builtin.Z3D_E621):
                        with it as tg:
                            res = tg.predict(img, threshold_z3d)
                    else:
                        with it as cap:
                            res = cap.predict(img)
            return ", ".join(res)

    def get_tag_list(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_infos()
        return [key for key in self.tag_counts.keys()]

    def get_tag_set(self):
        if len(self.tag_counts) == 0:
            self.construct_tag_infos()
        return {key for key in self.tag_counts.keys()}

    def get_tags_by_image_path(self, imgpath: str):
        return self.dataset.get_data_tags(imgpath)

    def set_tags_by_image_path(self, imgpath: str, tags: list[str]):
        self.dataset.append_data(ds.Data(imgpath, ",".join(tags)))
        self.construct_tag_infos()

    def write_tags(self, tags: list[str], sort_by: SortBy = SortBy.FREQ):
        sort_by = self.SortBy(sort_by)
        if tags:
            if sort_by == self.SortBy.FREQ:
                return [
                    f"{tag} [{self.tag_counts.get(tag) or 0}]" for tag in tags if tag
                ]
            elif sort_by == self.SortBy.LEN:
                return [f"{tag} [{len(tag)}]" for tag in tags if tag]
            elif sort_by == self.SortBy.TOKEN:
                return [
                    f"{tag} [{self.tag_tokens.get(tag, (0, 0))[1]}]"
                    for tag in tags
                    if tag
                ]
            else:
                return [f"{tag}" for tag in tags if tag]
        else:
            return []

    def read_tags(self, tags: list[str]):
        if tags:
            tags = [re_tags.match(tag).group(1) for tag in tags if tag]
            return [t for t in tags if t]
        else:
            return []

    def sort_tags(
        self,
        tags: list[str],
        sort_by: SortBy = SortBy.ALPHA,
        sort_order: SortOrder = SortOrder.ASC,
    ):
        sort_by = self.SortBy(sort_by)
        sort_order = self.SortOrder(sort_order)
        if sort_by == self.SortBy.ALPHA:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, reverse=True)
        elif sort_by == self.SortBy.FREQ:
            if sort_order == self.SortOrder.ASC:
                return sorted(
                    tags, key=lambda t: (self.tag_counts.get(t, 0), t), reverse=False
                )
            elif sort_order == self.SortOrder.DESC:
                return sorted(
                    tags, key=lambda t: (-self.tag_counts.get(t, 0), t), reverse=False
                )
        elif sort_by == self.SortBy.LEN:
            if sort_order == self.SortOrder.ASC:
                return sorted(tags, key=lambda t: (len(t), t), reverse=False)
            elif sort_order == self.SortOrder.DESC:
                return sorted(tags, key=lambda t: (-len(t), t), reverse=False)
        elif sort_by == self.SortBy.TOKEN:
            if sort_order == self.SortOrder.ASC:
                return sorted(
                    tags,
                    key=lambda t: (self.tag_tokens.get(t, (0, 0))[1], t),
                    reverse=False,
                )
            elif sort_order == self.SortOrder.DESC:
                return sorted(
                    tags,
                    key=lambda t: (-self.tag_tokens.get(t, (0, 0))[1], t),
                    reverse=False,
                )
        return list(tags)

    def get_filtered_imgpaths(self, filters: list[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)

        img_paths = sorted(filtered_set.datas.keys())

        return img_paths

    def get_filtered_imgs(self, filters: list[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)

        img_paths = sorted(filtered_set.datas.keys())

        return [self.images.get(path) for path in img_paths]

    def get_filtered_imgindices(self, filters: list[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)

        img_paths = sorted(filtered_set.datas.keys())

        return [self.img_idx.get(p) for p in img_paths]

    def get_filtered_tags(
        self,
        filters: list[filters.Filter] = [],
        filter_word: str = "",
        filter_tags=True,
        prefix=False,
        suffix=False,
        regex=False,
    ):
        if filter_tags:
            filtered_set = self.dataset.copy()
            for filter in filters:
                filtered_set.filter(filter)
            tags: set[str] = filtered_set.get_tagset()
        else:
            tags: set[str] = self.dataset.get_tagset()

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

    def cleanup_tags(self, tags: list[str]):
        current_dataset_tags = self.dataset.get_tagset()
        return [t for t in tags if t in current_dataset_tags]

    def cleanup_tagset(self, tags: set[str]):
        current_dataset_tagset = self.dataset.get_tagset()
        return tags & current_dataset_tagset

    def get_common_tags(self, filters: list[filters.Filter] = []):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)

        result = filtered_set.get_tagset()
        for d in filtered_set.datas.values():
            result &= d.tagset

        return sorted(result)

    def replace_tags(
        self,
        search_tags: list[str],
        replace_tags: list[str],
        filters: list[filters.Filter] = [],
        prepend: bool = False,
    ):
        img_paths = self.get_filtered_imgpaths(filters=filters)
        tags_to_append = replace_tags[len(search_tags) :]
        tags_to_remove = search_tags[len(replace_tags) :]
        tags_to_replace = {}
        for i in range(min(len(search_tags), len(replace_tags))):
            if replace_tags[i] is None or replace_tags[i] == "":
                tags_to_remove.append(search_tags[i])
            else:
                tags_to_replace[search_tags[i]] = replace_tags[i]
        for img_path in img_paths:
            tags_removed = [
                t
                for t in self.dataset.get_data_tags(img_path)
                if t not in tags_to_remove
            ]
            tags_replaced = [
                tags_to_replace.get(t) if t in tags_to_replace.keys() else t
                for t in tags_removed
            ]
            self.set_tags_by_image_path(
                img_path,
                tags_to_append + tags_replaced
                if prepend
                else tags_replaced + tags_to_append,
            )

        self.construct_tag_infos()

    def get_replaced_tagset(
        self, tags: set[str], search_tags: list[str], replace_tags: list[str]
    ):
        tags_to_remove = search_tags[len(replace_tags) :]
        tags_to_replace = {}
        for i in range(min(len(search_tags), len(replace_tags))):
            if replace_tags[i] is None or replace_tags[i] == "":
                tags_to_remove.append(search_tags[i])
            else:
                tags_to_replace[search_tags[i]] = replace_tags[i]
        tags_removed = {t for t in tags if t not in tags_to_remove}
        tags_replaced = {
            tags_to_replace.get(t) if t in tags_to_replace.keys() else t
            for t in tags_removed
        }
        return {t for t in tags_replaced if t}

    def search_and_replace_caption(
        self,
        search_text: str,
        replace_text: str,
        filters: list[filters.Filter] = [],
        use_regex: bool = False,
    ):
        img_paths = self.get_filtered_imgpaths(filters=filters)

        for img_path in img_paths:
            caption = ", ".join(self.dataset.get_data_tags(img_path))
            if use_regex:
                caption = [
                    t.strip()
                    for t in re.sub(search_text, replace_text, caption).split(",")
                ]
            else:
                caption = [
                    t.strip()
                    for t in caption.replace(search_text, replace_text).split(",")
                ]
            caption = [t for t in caption if t]
            self.set_tags_by_image_path(img_path, caption)

        self.construct_tag_infos()

    def search_and_replace_selected_tags(
        self,
        search_text: str,
        replace_text: str,
        selected_tags: Optional[set[str]],
        filters: list[filters.Filter] = [],
        use_regex: bool = False,
    ):
        img_paths = self.get_filtered_imgpaths(filters=filters)

        for img_path in img_paths:
            tags = self.dataset.get_data_tags(img_path)
            tags = self.search_and_replace_tag_list(
                search_text, replace_text, tags, selected_tags, use_regex
            )
            self.set_tags_by_image_path(img_path, tags)

        self.construct_tag_infos()

    def search_and_replace_tag_list(
        self,
        search_text: str,
        replace_text: str,
        tags: list[str],
        selected_tags: Optional[set[str]] = None,
        use_regex: bool = False,
    ):
        if use_regex:
            if selected_tags is None:
                tags = [re.sub(search_text, replace_text, t) for t in tags]
            else:
                tags = [
                    re.sub(search_text, replace_text, t) if t in selected_tags else t
                    for t in tags
                ]
        else:
            if selected_tags is None:
                tags = [t.replace(search_text, replace_text) for t in tags]
            else:
                tags = [
                    t.replace(search_text, replace_text) if t in selected_tags else t
                    for t in tags
                ]
        tags = [t2 for t1 in tags for t2 in t1.split(",") if t2]
        return [t for t in tags if t]

    def search_and_replace_tag_set(
        self,
        search_text: str,
        replace_text: str,
        tags: set[str],
        selected_tags: Optional[set[str]] = None,
        use_regex: bool = False,
    ):
        if use_regex:
            if selected_tags is None:
                tags = {re.sub(search_text, replace_text, t) for t in tags}
            else:
                tags = {
                    re.sub(search_text, replace_text, t) if t in selected_tags else t
                    for t in tags
                }
        else:
            if selected_tags is None:
                tags = {t.replace(search_text, replace_text) for t in tags}
            else:
                tags = {
                    t.replace(search_text, replace_text) if t in selected_tags else t
                    for t in tags
                }
        tags = {t2 for t1 in tags for t2 in t1.split(",") if t2}
        return {t for t in tags if t}

    def remove_duplicated_tags(self, filters: list[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = []
            for t in tags:
                if t not in res:
                    res.append(t)
            self.set_tags_by_image_path(path, res)

    def remove_tags(self, tags: set[str], filters: list[filters.Filter] = []):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            res = self.dataset.get_data_tags(path)
            res = [t for t in res if t not in tags]
            self.set_tags_by_image_path(path, res)

    def sort_filtered_tags(self, filters: list[filters.Filter] = [], **sort_args):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = self.sort_tags(tags, **sort_args)
            self.set_tags_by_image_path(path, res)
        logger.write(
            f'Tags are sorted by {sort_args.get("sort_by").value} ({sort_args.get("sort_order").value})'
        )

    def truncate_filtered_tags_by_token_count(
        self, filters: list[filters.Filter] = [], max_token_count: int = 75
    ):
        img_paths = self.get_filtered_imgpaths(filters)
        for path in img_paths:
            tags = self.dataset.get_data_tags(path)
            res = []
            for tag in tags:
                _, token_count = clip_tokenizer.tokenize(", ".join(res + [tag]))
                if token_count <= max_token_count:
                    res.append(tag)
                else:
                    break
            self.set_tags_by_image_path(path, res)

        self.construct_tag_infos()
        logger.write(f"Tags are truncated into token count <= {max_token_count}")

    def get_img_path_list(self):
        return [k for k in self.dataset.datas.keys() if k]

    def get_img_path_set(self):
        return {k for k in self.dataset.datas.keys() if k}

    def delete_dataset(
        self,
        caption_ext: str,
        filters: list[filters.Filter],
        delete_image: bool = False,
        delete_caption: bool = False,
        delete_backup: bool = False,
    ):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.delete_dataset_file(
                path, caption_ext, delete_image, delete_caption, delete_backup
            )

        if delete_image:
            self.dataset.remove(filtered_set)
            self.construct_tag_infos()

    def move_dataset(
        self,
        dest_dir: str,
        caption_ext: str,
        filters: list[filters.Filter],
        move_image: bool = False,
        move_caption: bool = False,
        move_backup: bool = False,
    ):
        filtered_set = self.dataset.copy()
        for filter in filters:
            filtered_set.filter(filter)
        for path in filtered_set.datas.keys():
            self.move_dataset_file(
                path, caption_ext, dest_dir, move_image, move_caption, move_backup
            )

        if move_image:
            self.construct_tag_infos()

    def delete_dataset_file(
        self,
        img_path: str,
        caption_ext: str,
        delete_image: bool = False,
        delete_caption: bool = False,
        delete_backup: bool = False,
    ):
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
                    logger.write(f"Deleted {img_path_obj.absolute()}")
            except Exception as e:
                logger.error(e)

        if delete_caption:
            try:
                txt_path_obj = img_path_obj.with_suffix(caption_ext)
                if txt_path_obj.is_file():
                    txt_path_obj.unlink()
                    logger.write(f"Deleted {txt_path_obj.absolute()}")
            except Exception as e:
                logger.error(e)

        if delete_backup:
            try:
                for extnum in range(1000):
                    bak_path_obj = img_path_obj.with_suffix(f".{extnum:0>3d}")
                    if bak_path_obj.is_file():
                        bak_path_obj.unlink()
                        logger.write(f"Deleted {bak_path_obj.absolute()}")
            except Exception as e:
                logger.error(e)

    def move_dataset_file(
        self,
        img_path: str,
        caption_ext: str,
        dest_dir: str,
        move_image: bool = False,
        move_caption: bool = False,
        move_backup: bool = False,
    ):
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
                    logger.write(
                        f"Moved {img_path_obj.absolute()} -> {dst_path_obj.absolute()}"
                    )
            except Exception as e:
                logger.error(e)

        if move_caption:
            try:
                txt_path_obj = img_path_obj.with_suffix(caption_ext)
                dst_path_obj = dest_dir_obj / txt_path_obj.name
                if txt_path_obj.is_file():
                    txt_path_obj.replace(dst_path_obj)
                    logger.write(
                        f"Moved {txt_path_obj.absolute()} -> {dst_path_obj.absolute()}"
                    )
            except Exception as e:
                logger.error(e)

        if move_backup:
            try:
                for extnum in range(1000):
                    bak_path_obj = img_path_obj.with_suffix(f".{extnum:0>3d}")
                    dst_path_obj = dest_dir_obj / bak_path_obj.name
                    if bak_path_obj.is_file():
                        bak_path_obj.replace(dst_path_obj)
                        logger.write(
                            f"Moved {bak_path_obj.absolute()} -> {dst_path_obj.absolute()}"
                        )
            except Exception as e:
                logger.error(e)


    def load_dataset(
        self,
        img_dir: str,
        caption_ext: str,
        recursive: bool,
        load_caption_from_filename: bool,
        replace_new_line: bool,
        interrogate_method: InterrogateMethod,
        interrogator_names: list[str],
        threshold_booru: float,
        threshold_waifu: float,
        threshold_z3d: float,
        use_temp_dir: bool,
        kohya_json_path: Optional[str], 
        max_res:float
    ):
        self.clear()

        img_dir_obj = Path(img_dir)

        logger.write(f"Loading dataset from {img_dir_obj.absolute()}")
        if recursive:
            logger.write(f"Also loading from subdirectories.")

        try:
            filepaths = img_dir_obj.glob("**/*") if recursive else img_dir_obj.glob("*")
            filepaths = [p for p in filepaths if p.is_file()]
        except Exception as e:
            logger.error(e)
            logger.write("Loading Aborted.")
            return

        self.dataset_dir = img_dir

        logger.write(
            f"Total {len(filepaths)} files under the directory including not image files."
        )

        def load_images(filepaths: list[Path]):
            imgpaths = []
            images = {}
            for img_path in filepaths:
                if img_path.suffix == caption_ext:
                    continue
                try:
                    img = Image.open(img_path)
                except:
                    continue
                else:
                    abs_path = str(img_path.absolute())
                    images[abs_path] = img
                    imgpaths.append(abs_path)
            return imgpaths, images
        
        def load_thumbnails(images_raw: dict[str, Image.Image]):
            images = {}
            if max_res > 0:
                for img_path, img in images_raw.items():
                    img_res = int(max_res), int(max_res)
                    images[img_path] = img.copy()
                    images[img_path].thumbnail(img_res)
            else:
                for img_path, img in images_raw.items():
                    if not use_temp_dir:
                        img.already_saved_as = img_path
                    images[img_path] = img
            return images

        def load_captions(imgpaths: list[str]):
            taglists = []
            for abs_path in imgpaths:
                img_path = Path(abs_path)
                text_path = img_path.with_suffix(caption_ext)
                caption_text = ""
                if interrogate_method != self.InterrogateMethod.OVERWRITE:
                    # from modules/textual_inversion/dataset.py, modified
                    if text_path.is_file():
                        caption_text = text_path.read_text("utf8")
                    elif load_caption_from_filename:
                        caption_text = img_path.stem
                        caption_text = re.sub(re_numbers_at_start, "", caption_text)
                        if self.re_word:
                            tokens = self.re_word.findall(caption_text)
                            caption_text = (
                                shared.opts.dataset_filename_join_string or ""
                            ).join(tokens)

                if replace_new_line:
                    caption_text = re_newlines.sub(",", caption_text)

                caption_tags = [t.strip() for t in caption_text.split(",")]
                caption_tags = [t for t in caption_tags if t]
                taglists.append(caption_tags)

            return taglists
        
        tagger_thresholds:list[tuple[Tagger, float]] = []
        if interrogate_method != self.InterrogateMethod.NONE:
            for it in self.INTERROGATORS:
                if it.name() in interrogator_names:
                    if isinstance(it, taggers_builtin.DeepDanbooru):
                        tagger_thresholds.append((it, threshold_booru))
                    elif isinstance(it, taggers_builtin.WaifuDiffusion) or isinstance(it, taggers_builtin.WaifuDiffusionTimm):
                        tagger_thresholds.append((it, threshold_waifu))
                    elif isinstance(it, taggers_builtin.Z3D_E621):
                        tagger_thresholds.append((it, threshold_z3d))
                    else:
                        tagger_thresholds.append((it, None))

        if kohya_json_path:
            imgpaths, images_raw, taglists = kohya_metadata.read(
                img_dir, kohya_json_path, use_temp_dir
            )
        else:
            imgpaths, images_raw = load_images(filepaths)
            taglists = load_captions(imgpaths)
        
        self.images = load_thumbnails(images_raw)
        
        interrogate_tags = {img_path : [] for img_path in imgpaths}
        
        img_to_interrogate = [
        img_path for i, img_path in enumerate(imgpaths) 
            if (not taglists[i] or interrogate_method != self.InterrogateMethod.PREFILL)
        ]

        if interrogate_method != self.InterrogateMethod.NONE and img_to_interrogate:
            logger.write("Preprocess images...")
            max_workers = shared.opts.dataset_editor_num_cpu_workers
            if max_workers < 0:
                import os
                max_workers = os.cpu_count() + 1
            
            def gen_data(paths:list[str], images:dict[str, Image.Image]):
                for img_path in paths:
                    yield images[img_path]
            
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                result = list(executor.map(get_square_rgb, gen_data(img_to_interrogate, images_raw)))
            logger.write("Preprocess completed")
            
            for tg, th in tqdm(tagger_thresholds):
                use_pipe = True
                tg.start()

                try:
                    tg.predict_pipe(None)
                except NotImplementedError:
                    use_pipe = False
                except Exception as e:
                    tb = sys.exc_info()[2]
                    logger.error(e.with_traceback(tb))
                    continue
                try:
                    if use_pipe:
                        for img_path, tags in tqdm(zip(img_to_interrogate, tg.predict_pipe(result, th)), desc=tg.name(), total=len(img_to_interrogate)):
                            interrogate_tags[img_path] += tags
                    else:
                        for img_path, data in tqdm(zip(img_to_interrogate, result), desc=tg.name(), total=len(img_to_interrogate)):
                            interrogate_tags[img_path] += tg.predict(data, th)
                except Exception as e:
                    tb = sys.exc_info()[2]
                    logger.error(e.with_traceback(tb))
                finally:
                    tg.stop()
        
        for img_path, tags in zip(imgpaths, taglists):
            if (interrogate_method == self.InterrogateMethod.PREFILL and not tags) or (interrogate_method == self.InterrogateMethod.OVERWRITE):
                tags = interrogate_tags[img_path]
            elif interrogate_method == self.InterrogateMethod.PREPEND:
                tags = interrogate_tags[img_path] + tags
            elif interrogate_method != self.InterrogateMethod.PREFILL:
                tags = tags + interrogate_tags[img_path]

            self.set_tags_by_image_path(img_path, tags)

        for i, p in enumerate(sorted(self.dataset.datas.keys())):
            self.img_idx[p] = i

        self.construct_tag_infos()
        logger.write(f"Loading Completed: {len(self.dataset)} images found")

    def save_dataset(
        self,
        backup: bool,
        caption_ext: str,
        write_kohya_metadata: bool,
        meta_out_path: str,
        meta_in_path: Optional[str],
        meta_overwrite: bool,
        meta_as_caption: bool,
        meta_full_path: bool,
    ):
        if len(self.dataset) == 0:
            return (0, 0, "")

        saved_num = 0
        backup_num = 0
        for data in self.dataset.datas.values():
            img_path, tags = Path(data.imgpath), data.tags
            txt_path = img_path.with_suffix(caption_ext)
            # make backup
            if backup and txt_path.is_file():
                for extnum in range(1000):
                    bak_path = img_path.with_suffix(f".{extnum:0>3d}")
                    if not bak_path.is_file():
                        break
                    else:
                        bak_path = None
                if bak_path is None:
                    logger.write(
                        f"There are too many backup files with same filename. A backup file of {txt_path} cannot be created."
                    )
                else:
                    try:
                        txt_path.rename(bak_path)
                    except Exception as e:
                        print(e)
                        logger.write(
                            f"A backup file of {txt_path} cannot be created."
                        )
                    else:
                        backup_num += 1
            # save
            try:
                txt_path.write_text(", ".join(tags), "utf8")
            except Exception as e:
                print(e)
                logger.warn(f"{txt_path} cannot be saved.")
            else:
                saved_num += 1
        logger.write(
            f"Backup text files: {backup_num}/{len(self.dataset)} under {self.dataset_dir}"
        )
        logger.write(
            f"Saved text files: {saved_num}/{len(self.dataset)} under {self.dataset_dir}"
        )

        if write_kohya_metadata:
            kohya_metadata.write(
                dataset=self.dataset,
                dataset_dir=self.dataset_dir,
                out_path=meta_out_path,
                in_path=meta_in_path,
                overwrite=meta_overwrite,
                save_as_caption=meta_as_caption,
                use_full_path=meta_full_path,
            )
            logger.write(f"Saved json metadata file in {meta_out_path}")
        return (saved_num, len(self.dataset), self.dataset_dir)

    def clear(self):
        self.dataset.clear()
        self.tag_counts.clear()
        self.tag_tokens.clear()
        self.img_idx.clear()
        self.dataset_dir = ""
        for img in self.images:
            if isinstance(img, Image.Image):
                img.close()
        self.images.clear()

    def construct_tag_infos(self):
        self.tag_counts = {}
        update_token_count = (
            self.raw_clip_token_used is None
            or self.raw_clip_token_used != shared.opts.dataset_editor_use_raw_clip_token
        )

        if update_token_count:
            self.tag_tokens.clear()

        for data in self.dataset.datas.values():
            for tag in data.tags:
                if tag in self.tag_counts.keys():
                    self.tag_counts[tag] += 1
                else:
                    self.tag_counts[tag] = 1
                if tag not in self.tag_tokens:
                    self.tag_tokens[tag] = clip_tokenizer.tokenize(
                        tag, shared.opts.dataset_editor_use_raw_clip_token
                    )
        self.raw_clip_token_used = shared.opts.dataset_editor_use_raw_clip_token
