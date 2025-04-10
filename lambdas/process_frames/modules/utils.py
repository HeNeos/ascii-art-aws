import ctypes as ct
from typing import no_type_check

import cairo
import numpy as np
import numpy.typing as npt

from lambdas.utils.custom_types import AsciiColors, AsciiImage
from lambdas.utils.font import Font
from lambdas.process_frames.modules.ascii_dict import AsciiDict, display_formats
from lambdas.process_frames.canvas_context.cairo_context import CairoContextFactory

_initialized: bool = False
face: cairo.FontFace | None = None


@no_type_check
def get_ascii_dict(width: int, height: int, output: str) -> AsciiDict:
    return (
        display_formats[output].value.HighAsciiDict
        if width * height >= (1600 // Font.Width.value) * (900 // Font.Height.value)
        else display_formats[output].value.LowAsciiDict
    )


def create_char_array(ascii_dict: AsciiDict) -> npt.NDArray[np.str_]:
    return np.array(list(ascii_dict.value))


def map_to_char_vectorized(
    values: np.ndarray, char_array: np.ndarray
) -> npt.NDArray[np.str_]:
    positions: npt.NDArray[np.int32] = (
        np.digitize(values, np.linspace(0, 256, len(char_array) + 1)) - 1
    )
    return char_array[positions]


# https://www.cairographics.org/cookbook/freetypepython/
@no_type_check
# mypy: disable-error-code=name-defined
def create_cairo_font_face_for_file(
    filename, faceindex=0, loadoptions=0
) -> cairo.FontFace:
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:
        _freetype_so = ct.CDLL("libfreetype.so.6")
        _cairo_so = ct.CDLL("libcairo.so.2")
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [
            ct.c_void_p,
            ct.c_int,
        ]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
        )
        _cairo_so.cairo_set_font_face.argtypes = [ct.c_void_p, ct.c_void_p]
        _cairo_so.cairo_font_face_status.argtypes = [ct.c_void_p]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ct.c_void_p]
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d initializing FreeType library." % status)

        class PycairoContext(ct.Structure):
            _fields_ = [
                ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                ("ctx", ct.c_void_p),
                ("base", ct.c_void_p),
            ]

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int()
        _initialized = True

    ft_face = ct.c_void_p()
    cr_face = None
    try:
        status = _freetype_so.FT_New_Face(
            _ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face)
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
            _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key))
            is None
        ):
            status = _cairo_so.cairo_font_face_set_user_data(
                cr_face, ct.byref(_ft_destroy_key), ft_face, _freetype_so.FT_Done_Face
            )
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError(
                    "Error %d doing user_data dance for %s" % (status, filename)
                )
            ft_face = None
        cairo_ctx = cairo.Context(_surface)
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
    gray_array: npt.NDArray[np.float64],
    output: str,
) -> cairo.ImageSurface:
    global face
    rows = len(ascii_art)
    columns = len(ascii_art[0])

    surface_width = int(Font.Width.value * columns)
    surface_height = int(Font.Height.value * rows)

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, surface_width, surface_height)
    context = CairoContextFactory.create(display_formats[output], surface)

    if face is None:
        face = create_cairo_font_face_for_file(Font.Name.value, 0)
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
