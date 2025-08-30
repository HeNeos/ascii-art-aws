from typing import cast

from cv2 import CV_64F, Sobel
from numba import njit
from numpy import arctan2, float64, max, pi, sqrt
from numpy.typing import NDArray


@njit(fastmath=True, cache=True)
def calculate_magnitudes_and_angles(
    grad_x: NDArray[float64],
    grad_y: NDArray[float64],
) -> tuple[NDArray[float64], NDArray[float64]]:
    magnitudes = sqrt(grad_x**2 + grad_y**2)
    max_value = max(magnitudes)
    if max_value > 0:
        magnitudes /= max_value
    angles = arctan2(grad_y, grad_x) * 180 / pi
    return angles, magnitudes


def sobel_filter(
    dog_array: NDArray[float64],
) -> tuple[NDArray[float64], NDArray[float64]]:
    grad_x: NDArray[float64] = cast(
        "NDArray[float64]",
        Sobel(dog_array, CV_64F, 1, 0, ksize=3),
    )
    grad_y: NDArray[float64] = cast(
        "NDArray[float64]",
        Sobel(dog_array, CV_64F, 0, 1, ksize=3),
    )

    angles, magnitudes = calculate_magnitudes_and_angles(grad_x, grad_y)

    return angles, magnitudes
