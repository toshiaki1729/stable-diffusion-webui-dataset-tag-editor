from typing import Tuple
import math

from PIL import Image

if not hasattr(Image, 'Resampling'):  # Pillow<9.0
    Image.Resampling = Image


def resize(image: Image.Image, size: Tuple[int, int]):
    return image.resize(size, resample=Image.Resampling.LANCZOS)


def get_rgb_image(image:Image.Image):
    if image.mode not in ["RGB", "RGBA"]:
        image = image.convert("RGBA") if "transparency" in image.info else image.convert("RGB")
    if image.mode == "RGBA":
        white = Image.new("RGBA", image.size, (255, 255, 255, 255))
        white.alpha_composite(image)
        image = white.convert("RGB")
    return image


def resize_and_fill(image: Image.Image, size: Tuple[int, int], repeat_edge = True, fill_rgb:tuple[int,int,int] = (255, 255, 255)):
    width, height = size
    scale_w, scale_h = width / image.width, height / image.height
    resized_w, resized_h = width, height
    if scale_w < scale_h:
        resized_h = image.height * resized_w // image.width
    elif scale_h < scale_w:
        resized_w = image.width * resized_h // image.height

    resized = resize(image, (resized_w, resized_h))
    if resized_w == width and resized_h == height:
        return resized
    
    if repeat_edge:
        fill_l = math.floor((width - resized_w) / 2)
        fill_r = width - resized_w - fill_l
        fill_t = math.floor((height - resized_h) / 2)
        fill_b = height - resized_h - fill_t
        result = Image.new("RGB", (width, height))
        result.paste(resized, (fill_l, fill_t))
        if fill_t > 0:
            result.paste(resized.resize((width, fill_t), box=(0, 0, width, 0)), (0, 0))
        if fill_b > 0:
            result.paste(
                resized.resize(
                    (width, fill_b), box=(0, resized.height, width, resized.height)
                ),
                (0, resized.height + fill_t),
            )
        if fill_l > 0:
            result.paste(resized.resize((fill_l, height), box=(0, 0, 0, height)), (0, 0))
        if fill_r > 0:
            result.paste(
                resized.resize(
                    (fill_r, height), box=(resized.width, 0, resized.width, height)
                ),
                (resized.width + fill_l, 0),
            )
        return result
    else:
        result = Image.new("RGB", size, fill_rgb)
        result.paste(resized, box=((width - resized_w) // 2, (height - resized_h) // 2))
        return result.convert("RGB")


