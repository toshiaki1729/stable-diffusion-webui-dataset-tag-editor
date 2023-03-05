# This code is based on following codes written by kohya-ss and modified by toshiaki1729.
# https://github.com/kohya-ss/sd-scripts/blob/main/finetune/merge_captions_to_metadata.py
# https://github.com/kohya-ss/sd-scripts/blob/main/finetune/merge_dd_tags_to_metadata.py

# The original code is distributed in the Apache License 2.0.
# Full text of the license is available at the following link.
# https://www.apache.org/licenses/LICENSE-2.0

# implement metadata output compatible to kohya-ss's finetuning captions
# on commit hash: ae33d724793e14f16b4c68bdad79f836c86b1b8e

import json
from glob import glob
from pathlib import Path
from PIL import Image

def write(dataset, dataset_dir, out_path, in_path=None, overwrite=False, save_as_caption=False, use_full_path=False):
    dataset_dir = Path(dataset_dir)
    if in_path is None and Path(out_path).is_file() and not overwrite:
        in_path = out_path
    
    result = {}
    if in_path is not None:
        try:
            result = json.loads(Path(in_path).read_text(encoding='utf-8'))
        except:
            result = {}

    tags_key = 'caption' if save_as_caption else 'tags'

    for data in dataset.datas.values():
        img_path, tags = Path(data.imgpath), data.tags
        
        img_key = str(img_path.absolute()) if use_full_path else img_path.stem
        save_caption = ', '.join(tags) if save_as_caption else tags
        
        if img_key not in result:
            result[img_key] = {}
        
        result[img_key][tags_key] = save_caption

    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        json.dump(result, f, indent=2)


def read(dataset_dir, json_path, use_temp_dir:bool):
    dataset_dir = Path(dataset_dir)
    json_path = Path(json_path)
    metadata = json.loads(json_path.read_text('utf8'))
    imgpaths = []
    images = {}
    taglists = []

    def load_image(img_path):
        img_path = Path(path)
        try:
            img = Image.open(img_path)
        except:
            return None, None
        else:
            abs_path = str(img_path.absolute())
            if not use_temp_dir:
                img.already_saved_as = abs_path
            return abs_path, img

    for image_key, img_md in metadata.items():
        img_path = Path(image_key)
        abs_path = None
        img = None
        if img_path.is_file():
            abs_path, img = load_image(img_path)
            if abs_path is None or img is None:
                continue
            images[abs_path] = img
        else:
            for path in glob(str(dataset_dir.absolute() / (image_key + '.*'))):
                abs_path, img = load_image(path)
                if abs_path is None or img is None:
                    continue
                images[abs_path] = img
                break
        if abs_path is None or img is None:
            continue
        caption = img_md.get('caption')
        tags = img_md.get('tags')
        if tags is None:
            tags = []
        if caption is not None and isinstance(caption, str):
            caption = [s.strip() for s in caption.split(',')]
            tags = [s for s in caption if s] + tags
        imgpaths.append(abs_path)
        taglists.append(tags)
    
    return imgpaths, images, taglists