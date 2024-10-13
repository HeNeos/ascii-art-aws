import numpy as np

from typing import cast
from PIL import Image, ImageDraw, ImageFont

from lambdas.font import Font

from lambdas.process_frames.modules.ascii_dict import AsciiDict
from lambdas.custom_types import AsciiImage, AsciiColors, Color


def create_char_array(ascii_dict: AsciiDict) -> np.ndarray:
    return np.array(list(ascii_dict.value))


def map_to_char_vectorized(values: np.ndarray, char_array: np.ndarray) -> np.ndarray:
    return char_array[np.digitize(values, np.linspace(0, 256, len(char_array) + 1)) - 1]


def create_ascii_image(ascii_art: AsciiImage, image_colors: AsciiColors) -> Image.Image:
    image: Image.Image = Image.new(
        "RGB",
        (Font.Width.value * len(ascii_art[0]), Font.Height.value * len(ascii_art)),
        "black",
    )
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("consolas.ttf", 12)
    x, y = 0, 0
    for row in range(len(ascii_art)):
        for column in range(len(ascii_art[row])):
            color: Color = cast(Color, tuple(image_colors[row][column]))
            draw.text((x, y), ascii_art[row][column], font=font, fill=color)
            x += Font.Width.value
        x = 0
        y += Font.Height.value
    return image
