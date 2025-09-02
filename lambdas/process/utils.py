import logging
from ctypes import CDLL, Structure, byref, c_byte, c_int, c_void_p
from typing import no_type_check

from cairo import FORMAT_A8, FORMAT_RGB24, Context, FontFace, ImageSurface
from numba import jit
from numpy import (
    array,
    clip,
    digitize,
    dot,
    float64,
    int32,
    linspace,
    ndarray,
    str_,
    uint8,
    zeros_like,
)
from numpy.typing import NDArray

from lambdas.models.font import Font
from lambdas.models.media_file import AsciiColors, AsciiImage, Color
from lambdas.process.ascii_dict import AsciiDict, AsciiDictEdges, display_formats
from lambdas.process.canvas_context.cairo_context import CairoContextFactory
from lambdas.process.dithering import DitheringStrategy
from lambdas.process.edge_detection import EdgeDetection

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


@jit(
    "int32(float64)",
    nopython=True,
    nogil=True,
    fastmath=True,
    cache=True,
)
def map_angle_to_ascii(angle: float) -> int:
    if -22.5 <= angle < 22.5 or 157.5 <= angle <= 180 or -180 <= angle < -157.5:
        return 0  # |
    if 67.5 <= angle < 112.5 or -112.5 <= angle < -67.5:
        return -1  # _
    if 22.5 <= angle < 67.5 or -157.5 <= angle < -112.5:
        return 2  # /
    if 112.5 <= angle < 157.5 or -67.5 <= angle < -22.5:
        return 3  # \
    return -1  # No edge


@jit(
    "int32[:, :](float64[:, :], float64[:, :])",
    nopython=True,
    nogil=True,
    fastmath=True,
    cache=True,
)
def _map_edges_to_positions(
    angles: NDArray[float64],
    magnitudes: NDArray[float64],
) -> NDArray[int32]:
    positions: NDArray[int32] = zeros_like(angles, dtype=int32)
    for i in range(angles.shape[0]):
        for j in range(angles.shape[1]):
            if magnitudes[i, j] < 0.55:
                positions[i, j] = -1
            else:
                positions[i, j] = map_angle_to_ascii(angles[i, j])
    return positions


def map_to_char_vectorized(
    values: ndarray,
    char_array: ndarray,
    edge_detection_parameters: EdgeDetection,
) -> NDArray[str_]:
    positions: NDArray[int32] = (
        digitize(values, linspace(0, 256, len(char_array) + 1)) - 1
    )
    output: NDArray[str_] = char_array[positions]

    angles = edge_detection_parameters.angles
    magnitudes = edge_detection_parameters.magnitudes
    canny_array = edge_detection_parameters.canny_array

    if angles is not None and magnitudes is not None:
        edges_positions: NDArray[int32] = _map_edges_to_positions(angles, magnitudes)
        mask = edges_positions != -1
        if canny_array is not None:
            canny_array = canny_array.reshape(values.shape)
            mask &= canny_array != 0
        output[mask] = AsciiDictEdges[edges_positions[mask]]

    return output


def process_image(
    image: NDArray[uint8],
    char_array: NDArray[str_],
    dithering_strategy: type[DitheringStrategy] | None = None,
    edge_detection: bool = False,
) -> tuple[AsciiImage, AsciiColors, NDArray[float64]]:
    gray_array: NDArray[float64] = clip(
        dot(image[..., :3], [0.3090, 0.5670, 0.1240]),
        0.0,
        255.0,
    )

    edge_detection_parameters: EdgeDetection = EdgeDetection()
    if edge_detection:
        edge_detection_parameters.apply_canny(image)
        edge_detection_parameters.apply_sobel(gray_array)

    if dithering_strategy is not None:
        gray_array = dithering_strategy.dithering(gray_array, len(char_array))

    ascii_chars: NDArray[str_] = map_to_char_vectorized(
        gray_array,
        char_array,
        edge_detection_parameters,
    )

    return ascii_chars.tolist(), [row.tolist() for row in image], gray_array


def ascii_convert(
    image: NDArray[uint8],
    char_array: NDArray[str_],
    dithering_strategy: type[DitheringStrategy] | None,
    output: str,
    edge_detection: bool = False,
) -> ImageSurface:
    grid, image_colors, gray_array = process_image(
        image=image,
        char_array=char_array,
        dithering_strategy=dithering_strategy,
        edge_detection=edge_detection,
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
            _ft_lib,
            filename.encode("utf-8"),
            faceindex,
            byref(ft_face),
        )
        if status != FT_Err_Ok:
            raise RuntimeError(
                "Error %d creating FreeType font face for %s" % (status, filename),
            )
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename),
            )
        if (
            _cairo_so.cairo_font_face_get_user_data(cr_face, byref(_ft_destroy_key))
            is None
        ):
            status = _cairo_so.cairo_font_face_set_user_data(
                cr_face,
                byref(_ft_destroy_key),
                ft_face,
                _freetype_so.FT_Done_Face,
            )
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError(
                    "Error %d doing user_data dance for %s" % (status, filename),
                )
            ft_face = None
        cairo_ctx = Context(_surface)
        cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename),
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
    rows: int = len(ascii_art)
    columns: int = len(ascii_art[0])

    surface_width: int = int(Font.Width.value * columns)
    surface_height: int = int(Font.Height.value * rows)

    surface: ImageSurface = ImageSurface(FORMAT_RGB24, surface_width, surface_height)
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
            char: str = ascii_art[row][column]
            color: Color = image_colors[row][column]
            luminance = gray_array[row][column]
            context.set_color(color, luminance)
            context.context.move_to(x, y + Font.Height.value)
            context.context.show_text(char)
            x += Font.Width.value
        y += Font.Height.value

    return surface
