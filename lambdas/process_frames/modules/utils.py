import numpy as np
import cairo

from lambdas.font import Font

from lambdas.process_frames.modules.ascii_dict import AsciiDict
from lambdas.custom_types import AsciiImage, AsciiColors


def create_char_array(ascii_dict: AsciiDict) -> np.ndarray:
    return np.array(list(ascii_dict.value))


def map_to_char_vectorized(values: np.ndarray, char_array: np.ndarray) -> np.ndarray:
    return char_array[np.digitize(values, np.linspace(0, 256, len(char_array) + 1)) - 1]


def create_ascii_image(
    ascii_art: AsciiImage, image_colors: AsciiColors
) -> cairo.ImageSurface:
    rows = len(ascii_art)
    columns = len(ascii_art[0])

    surface_width = int(Font.Width.value * columns)
    surface_height = int(Font.Height.value * rows)

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, surface_width, surface_height)
    context = cairo.Context(surface)

    context.select_font_face(
        "Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL
    )
    context.set_font_size(12)

    y = 0
    for row in range(rows):
        x = 0
        for column in range(columns):
            char = ascii_art[row][column]
            color = image_colors[row][column]
            context.set_source_rgb(color[0] / 255, color[1] / 255, color[2] / 255)
            context.move_to(x, y + Font.Height.value)
            context.show_text(char)
            x += Font.Width.value
        y += Font.Height.value

    return surface
