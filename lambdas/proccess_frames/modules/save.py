from PIL import Image, ImageDraw, ImageFont

from lambdas.font import Font
from lambdas.custom_types import AsciiImage, AsciiColors


def save_ascii_image(ascii_art: AsciiImage, image_name: str, **kwargs):
    image: Image.Image = Image.new(
        "RGBA",
        (Font.Width.value * len(ascii_art[0]), Font.Height.value * len(ascii_art)),
        "black",
    )
    image_colors = kwargs["image_colors"]
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("consolas.ttf", 14)
    x, y = 0, 0
    for row in range(len(ascii_art)):
        for column in range(len(ascii_art[row])):
            color = image_colors[row][column]
            draw.text((x, y), ascii_art[row][column], font=font, fill=color)
            x += Font.Width.value
        x = 0
        y += Font.Height.value
    image.save(f"{image_name}_ascii.png")


def save_ascii(
    ascii_art: AsciiImage,
    image_name: str,
    image_colors: AsciiColors,
):
    save_ascii_image(ascii_art, image_name, image_colors=image_colors)
