# This code is based on following codes written by kohya-ss and modified by toshiaki1729.
# https://github.com/kohya-ss/sd-scripts/blob/main/finetune/merge_captions_to_metadata.py
# https://github.com/kohya-ss/sd-scripts/blob/main/finetune/merge_dd_tags_to_metadata.py

# The original code is distributed in the Apache License 2.0.
# Full text of the license is available at the following link.
# https://www.apache.org/licenses/LICENSE-2.0

# implement metadata output compatible to kohya-ss's finetuning captions
# on commit hash: ae33d724793e14f16b4c68bdad79f836c86b1b8e

import json
from pathlib import Path

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
        
        img_key = str(img_path) if use_full_path else img_path.stem
        save_caption = ', '.join(tags) if save_as_caption else tags
        
        if img_key not in result:
            result[img_key] = {}
        
        result[img_key][tags_key] = save_caption

    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        json.dump(result, f, indent=2)