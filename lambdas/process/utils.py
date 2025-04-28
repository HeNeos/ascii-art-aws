import logging
from typing import no_type_check

from ctypes import c_void_p, c_byte, byref, c_int, CDLL, Structure
from cairo import FontFace, Context, ImageSurface, FORMAT_A8, FORMAT_RGB24
from numpy.typing import NDArray
from numpy import (
    array,
    str_,
    uint8,
    int32,
    float64,
    clip,
    dot,
    digitize,
    linspace,
    ndarray,
)

from lambdas.utils.custom_types import AsciiColors, AsciiImage
from lambdas.utils.font import Font
from lambdas.process.ascii_dict import AsciiDict, display_formats
from lambdas.process.canvas_context.cairo_context import CairoContextFactory
from lambdas.process.dithering import DitheringStrategy

_initialized: bool = False
face: FontFace | None = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@no_type_check
def get_ascii_dict(width: int, height: int, output: str) -> AsciiDict:
    return (
        display_formats[output].value.HighAsciiDict
        if width * height >= (1600 // Font.Width.value) * (900 // Font.Height.value)
        else display_formats[output].value.LowAsciiDict
    )


def create_char_array(ascii_dict: AsciiDict) -> NDArray[str_]:
    return array(list(ascii_dict.value))


def map_to_char_vectorized(values: ndarray, char_array: ndarray) -> NDArray[str_]:
    positions: NDArray[int32] = (
        digitize(values, linspace(0, 256, len(char_array) + 1)) - 1
    )
    return char_array[positions]


def process_image(
    image: NDArray[uint8],
    char_array: NDArray[str_],
    dithering_strategy: type[DitheringStrategy] | None = None,
) -> tuple[AsciiImage, AsciiColors, NDArray[float64]]:
    gray_array: NDArray[float64] = clip(
        dot(image[..., :3], [0.3090, 0.5770, 0.1240]), 0.0, 255.0
    )

    if dithering_strategy is not None:
        gray_array = dithering_strategy.dithering(gray_array, len(char_array))

    ascii_chars: NDArray[str_] = map_to_char_vectorized(gray_array, char_array)

    return ascii_chars.tolist(), [row.tolist() for row in image], gray_array


def ascii_convert(
    image: NDArray[uint8],
    char_array: NDArray[str_],
    dithering_strategy: type[DitheringStrategy] | None,
    output: str,
) -> ImageSurface:
    grid, image_colors, gray_array = process_image(
        image=image, char_array=char_array, dithering_strategy=dithering_strategy
    )
    return create_ascii_image(grid, image_colors, gray_array, output)


# https://www.cairographics.org/cookbook/freetypepython/
@no_type_check
# mypy: disable-error-code=name-defined
def create_cairo_font_face_for_file(filename, faceindex=0, loadoptions=0) -> FontFace:
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:
        _freetype_so = CDLL("libfreetype.so.6")
        _cairo_so = CDLL("libcairo.so.2")
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [
            c_void_p,
            c_int,
        ]
        _cairo_so.cairo_font_face_get_user_data.restype = c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (c_void_p, c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (
            c_void_p,
            c_void_p,
            c_void_p,
            c_void_p,
        )
        _cairo_so.cairo_set_font_face.argtypes = [c_void_p, c_void_p]
        _cairo_so.cairo_font_face_status.argtypes = [c_void_p]
        _cairo_so.cairo_font_face_destroy.argtypes = (c_void_p,)
        _cairo_so.cairo_status.argtypes = [c_void_p]
        _ft_lib = c_void_p()
        status = _freetype_so.FT_Init_FreeType(byref(_ft_lib))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d initializing FreeType library." % status)

        class PycairoContext(Structure):
            _fields_ = [
                ("PyObject_HEAD", c_byte * object.__basicsize__),
                ("ctx", c_void_p),
                ("base", c_void_p),
            ]

        _surface = ImageSurface(FORMAT_A8, 0, 0)
        _ft_destroy_key = c_int()
        _initialized = True

    ft_face = c_void_p()
    cr_face = None
    try:
        status = _freetype_so.FT_New_Face(
            _ft_lib, filename.encode("utf-8"), faceindex, byref(ft_face)
        )
        if status != FT_Err_Ok:
            raise RuntimeError(
                "Error %d creating FreeType font face for %s" % (status, filename)
            )
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename)
            )
        if (
            _cairo_so.cairo_font_face_get_user_data(cr_face, byref(_ft_destroy_key))
            is None
        ):
            status = _cairo_so.cairo_font_face_set_user_data(
                cr_face, byref(_ft_destroy_key), ft_face, _freetype_so.FT_Done_Face
            )
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError(
                    "Error %d doing user_data dance for %s" % (status, filename)
                )
            ft_face = None
        cairo_ctx = Context(_surface)
        cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename)
            )

    finally:
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)

    face = cairo_ctx.get_font_face()
    return face


def create_ascii_image(
    ascii_art: AsciiImage,
    image_colors: AsciiColors,
    gray_array: NDArray[float64],
    output: str,
) -> ImageSurface:
    global face
    rows = len(ascii_art)
    columns = len(ascii_art[0])

    surface_width = int(Font.Width.value * columns)
    surface_height = int(Font.Height.value * rows)

    surface = ImageSurface(FORMAT_RGB24, surface_width, surface_height)
    context = CairoContextFactory.create(display_formats[output], surface)

    if face is None:
        face = create_cairo_font_face_for_file(f"lambdas/process/{Font.Name.value}", 0)
    context.context.set_font_face(face)
    context.context.set_font_size(Font.Size.value)
    context.context.set_source_rgb(0, 0, 0)
    context.context.paint()

    y = 0
    for row in range(rows):
        x = 0
        for column in range(columns):
            char = ascii_art[row][column]
            color = image_colors[row][column]
            luminance = gray_array[row][column]
            context.set_color(color, luminance)
            context.context.move_to(x, y + Font.Height.value)
            context.context.show_text(char)
            x += Font.Width.value
        y += Font.Height.value

    return surface
