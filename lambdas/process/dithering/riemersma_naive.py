from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from numba import njit

from . import DitheringStrategy


@dataclass
class DitheringRiemersmaNaive(DitheringStrategy):
    name = "riemersma_naive"

    @staticmethod
    @njit(
        "float64[:, :](float64[:, :], int64)",
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
        visited = np.zeros((height, width), dtype=np.bool_)
        error: float = 0.0

        spiral_directions: list[tuple[int, int]] = [
            (0, 1),
            (1, 0),
            (0, -1),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, -1),
            (-1, 1),
        ]

        row, column = 0, 0
        visited[row, column] = True

        for _ in range(height * width):
            old_pixel = image_array[row, column] + error
            new_pixel = np.round(old_pixel / scale) * scale
            error = old_pixel - new_pixel
            image_array[row, column] = new_pixel

            for dr, dc in spiral_directions:
                nr, nc = row + dr, column + dc
                if 0 <= nr < height and 0 <= nc < width and not visited[nr, nc]:
                    row, column = nr, nc
                    visited[row, column] = True
                    break
        image_array = np.clip(image_array, 0.0, 255.0)

        return image_array
