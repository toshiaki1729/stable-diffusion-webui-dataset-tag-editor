
BLIP2_CAPTIONING_NAMES = [
    "blip2-opt-2.7b",
    "blip2-opt-2.7b-coco",
    "blip2-opt-6.7b",
    "blip2-opt-6.7b-coco",
    "blip2-flan-t5-xl",
    "blip2-flan-t5-xl-coco",
    "blip2-flan-t5-xxl",
]


# {tagger name : default tagger threshold}
# v1: idk if it's okay  v2, v3: P=R thresholds on each repo https://huggingface.co/SmilingWolf
WD_TAGGERS = {
    "wd-v1-4-vit-tagger" : 0.35,
    "wd-v1-4-convnext-tagger" : 0.35,
    "wd-v1-4-vit-tagger-v2" : 0.3537,
    "wd-v1-4-convnext-tagger-v2" : 0.3685,
    "wd-v1-4-convnextv2-tagger-v2" : 0.371,
    "wd-v1-4-moat-tagger-v2" : 0.3771
}
WD_TAGGERS_TIMM = {
    "wd-v1-4-swinv2-tagger-v2" : 0.3771,
    "wd-vit-tagger-v3" : 0.2614,
    "wd-convnext-tagger-v3" : 0.2682,
    "wd-swinv2-tagger-v3" : 0.2653,
}