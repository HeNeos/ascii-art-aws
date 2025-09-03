import io
import logging
from typing import cast

from cairo import FORMAT_ARGB32, FORMAT_RGB24, ImageSurface
from cv2 import COLOR_BGRA2BGR, IMWRITE_JPEG_QUALITY, cvtColor, imwrite
from mypy_boto3_s3.client import S3Client
from numpy import ndarray, uint8
from numpy.typing import NDArray

from lambdas.models.media_file import ImageExtension
from lambdas.process.post_processing.utils import apply_post_processing

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ImageCairo:
    def __init__(self, image: ImageSurface, image_format: ImageExtension) -> None:
        self.image = image
        self.height: int = image.get_height()
        self.width: int = image.get_width()
        self.surface_format = image.get_format()
        self.buffer: io.BytesIO = io.BytesIO()
        self.image_format: ImageExtension = image_format

    def to_ndarray(self) -> NDArray[uint8]:
        image_bgr: NDArray[uint8]
        if self.surface_format == FORMAT_ARGB32:
            # TODO: fix format
            cairo_data_bgra: NDArray[uint8] = ndarray(
                shape=(self.height, self.width, 4),
                dtype=uint8,
                buffer=self.image.get_data(),
                strides=(self.image.get_stride(), 4, 1),
            )
            image_bgr = cast("NDArray[uint8]", cvtColor(cairo_data_bgra, COLOR_BGRA2BGR))
        elif self.surface_format == FORMAT_RGB24:
            cairo_data_bgrx: NDArray[uint8] = ndarray(
                shape=(self.height, self.width, 4),
                dtype=uint8,
                buffer=self.image.get_data(),
                strides=(self.image.get_stride(), 4, 1),
            )
            image_bgr = cairo_data_bgrx[:, :, :3]
        else:
            raise f"Error: Unsupported Cairo surface format {self.surface_format}"
        return image_bgr
