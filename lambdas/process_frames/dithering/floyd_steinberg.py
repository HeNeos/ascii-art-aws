from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from numba import jit

from . import DitheringStrategy


@dataclass
class DitheringFloydSteinberg(DitheringStrategy):
    name = "floyd_steinberg"

    @staticmethod
    @jit(
        "float64[:, :](float64[:, :], int64)",
        nopython=True,
        nogil=True,
        fastmath=True,
        cache=True,
    )
    def dithering(
        image_array: npt.NDArray[np.float64], quantization_levels: int
    ) -> npt.NDArray[np.float64]:
        height: int = image_array.shape[0]
        width: int = image_array.shape[1]

        scale: float = 255 / (quantization_levels - 1)

        for row in range(height):
            for column in range(width):
                old_pixel = image_array[row, column]
                new_pixel = np.round(old_pixel / scale) * scale
                image_array[row, column] = new_pixel
                error = old_pixel - new_pixel
                if column + 1 < width:
                    image_array[row, column + 1] += error * 7 / 16
                if row + 1 < height and column > 0:
                    image_array[row + 1, column - 1] += error * 3 / 16
                if row + 1 < height:
                    image_array[row + 1, column] += error * 5 / 16
                if row + 1 < height and column + 1 < width:
                    image_array[row + 1, column + 1] += error * 1 / 16
        image_array = np.clip(image_array, 0.0, 255.0)

        return image_array
