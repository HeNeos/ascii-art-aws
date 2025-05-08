from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from numba import njit

from . import DitheringStrategy


@njit(
    "void(int64, int64, float64[:, :], int64[:], float64[:])",
    nogil=True,
    fastmath=True,
    cache=True,
)
def dither_pixel(
    cur_x: int,
    cur_y: int,
    img: npt.NDArray[np.float64],
    weights: npt.NDArray[np.int64],
    error_array: npt.NDArray[np.float64],
) -> None:
    num_levels = len(weights)
    pixel_value_at_pos = img[cur_y, cur_x]

    err_sum = 0.0
    for i in range(num_levels):
        err_sum += error_array[i] * weights[i]

    target_value = pixel_value_at_pos + err_sum / weights[num_levels - 1]
    target_value_clamped = min(max(target_value, 0.0), 255.0)

    step = 255.0 / (num_levels - 1.0)
    level_index = int(target_value_clamped / step + 0.5)

    if level_index < 0:
        level_index = 0
    elif level_index >= num_levels:
        level_index = num_levels - 1

    final_quantized_value: float = float(level_index * step)
    new_error = pixel_value_at_pos - final_quantized_value
    img[cur_y, cur_x] = final_quantized_value

    for i in range(num_levels - 1):
        error_array[i] = error_array[i + 1]
    error_array[num_levels - 1] = new_error


@njit(
    "void(float64[:, :], int64, int64, int64[:], int64[:], int64[:], float64[:])",
    nogil=True,
    fastmath=True,
    cache=True,
)
def move_and_dither(
    img: npt.NDArray[np.float64],
    img_width: int,
    img_height: int,
    weights: npt.NDArray[np.int64],
    pos: npt.NDArray[np.int64],
    direction: npt.NDArray[np.int64],
    error_array: npt.NDArray[np.float64],
) -> None:
    if 0 <= pos[0] < img_width and 0 <= pos[1] < img_height:
        dither_pixel(pos[0], pos[1], img, weights, error_array)

    if direction[0] == 1:
        pos[0] -= 1
    elif direction[0] == 2:
        pos[1] -= 1
    elif direction[0] == 3:
        pos[0] += 1
    elif direction[0] == 4:
        pos[1] += 1


@njit(
    "void(int64, float64[:, :], int64, int64, int64[:], int64[:], int64[:], float64[:])",
    nogil=True,
    fastmath=True,
    cache=True,
)
def hilbert_level_1(
    direction: int,
    img: npt.NDArray[np.float64],
    img_width: int,
    img_height: int,
    weights: npt.NDArray[np.int64],
    pos: npt.NDArray[np.int64],
    dir_array: npt.NDArray[np.int64],
    error_array: npt.NDArray[np.float64],
) -> None:
    if direction == 1:
        dir_array[0] = 3
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 4
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 1
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
    elif direction == 2:
        dir_array[0] = 4
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 3
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 2
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
    elif direction == 3:
        dir_array[0] = 1
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 2
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 3
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
    elif direction == 4:
        dir_array[0] = 2
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 1
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )
        dir_array[0] = 4
        move_and_dither(
            img, img_width, img_height, weights, pos, dir_array, error_array
        )


@njit(
    "void(int64, int64, float64[:, :], int64, int64, int64[:], int64[:], int64[:], float64[:])",
    nogil=True,
    fastmath=True,
    # cache=True,
)
def hilbert_level(
    level: int,
    direction: int,
    img: npt.NDArray[np.float64],
    img_width: int,
    img_height: int,
    weights: npt.NDArray[np.int64],
    pos: npt.NDArray[np.int64],
    dir_array: npt.NDArray[np.int64],
    error_array: npt.NDArray[np.float64],
) -> None:
    if level == 1:
        hilbert_level_1(
            direction, img, img_width, img_height, weights, pos, dir_array, error_array
        )
    else:
        if direction == 1:
            hilbert_level(
                level - 1,
                2,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 3
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                1,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 4
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                1,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 1
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                4,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
        elif direction == 2:
            hilbert_level(
                level - 1,
                1,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 4
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                2,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 3
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                2,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 2
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                3,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
        elif direction == 3:
            hilbert_level(
                level - 1,
                4,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 1
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                3,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 2
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                3,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 3
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                2,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
        elif direction == 4:
            hilbert_level(
                level - 1,
                3,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 2
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                4,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 1
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                4,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )
            dir_array[0] = 4
            move_and_dither(
                img, img_width, img_height, weights, pos, dir_array, error_array
            )
            hilbert_level(
                level - 1,
                1,
                img,
                img_width,
                img_height,
                weights,
                pos,
                dir_array,
                error_array,
            )


@dataclass
class DitheringRiemersma(DitheringStrategy):
    name = "riemersma"

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

        if height == 0 or width == 0:
            return image_array.copy()

        SIZE = quantization_levels  # queue size: number of pixels remembered
        MAX = quantization_levels  # relative weight of youngest pixel in the queue

        weights = np.zeros(SIZE, dtype=np.int64)
        multiplier = np.exp(np.log(float(MAX)) / float(SIZE - 1))
        val = 1.0
        for i in range(SIZE):
            weights[i] = int(val + 0.5)
            val *= multiplier

        largest_side = max(width, height)
        if largest_side <= 0:
            level = 0
        else:
            level = int(np.ceil(np.log2(float(largest_side))))

        if level < 1:
            level = 1

        pos = np.zeros(2, dtype=np.int64)
        dir_array = np.zeros(1, dtype=np.int64)
        error_array = np.zeros(SIZE, dtype=np.float64)

        hilbert_level(
            level, 1, image_array, width, height, weights, pos, dir_array, error_array
        )

        dir_array[0] = 0
        move_and_dither(
            image_array, width, height, weights, pos, dir_array, error_array
        )

        return np.clip(image_array, 0.0, 255.0)
