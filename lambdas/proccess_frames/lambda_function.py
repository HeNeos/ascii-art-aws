from PIL import Image
from typing import Tuple
from modules.ascii_dict import AsciiDict
from modules.utils import map_to_char
from lambdas.proccess_frames.modules.save import save_ascii
from lambdas.types import AsciiImage, AsciiColors


def process_image(image: Image.Image) -> Tuple[AsciiImage, AsciiColors]:
    pix = image.load()

    gray_image: Image.Image = image.convert("LA")
    width, height = gray_image.size

    ascii_dict = (
        AsciiDict.HighAsciiDict
        if width * height >= 150 * 150
        else AsciiDict.LowAsciiDict
    )

    grid: AsciiImage = [["X"] * width for _ in range(height)]
    image_colors: AsciiColors = [[(255, 255, 255)] * width for _ in range(height)]

    gray_pixels = gray_image.load()
    for y in range(height):
        for x in range(width):
            current_char: str = map_to_char(gray_pixels[x, y][0], ascii_dict)
            grid[y][x] = current_char
            image_colors[y][x] = pix[x, y]

    return grid, image_colors


def ascii_convert(image_path: str) -> AsciiImage:

    image_name, image_extension = image_path.split(".")
    image: Image.Image = Image.open(image_path).convert("RGB")
    grid, image_colors = process_image(image=image)

    save_ascii(
        ascii_art=grid,
        image_name=image_name,
        image_colors=image_colors,
    )
    return grid


def lambda_handler(event, context):
    ascii_convert()
    return
