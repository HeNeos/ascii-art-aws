from dataclasses import dataclass

from numpy import float64, uint8
from numpy.typing import NDArray


@dataclass
class EdgeDetection:
    canny_array: NDArray[float64] | None = None
    angles: NDArray[float64] | None = None
    magnitudes: NDArray[float64] | None = None

    def apply_canny(self, img_array: NDArray[uint8]) -> None:
        from cv2 import Canny

        self.canny_array = Canny(img_array, 100, 200).astype(float64)

    def apply_sobel(self, dog_array: NDArray[float64]) -> None:
        from .sobel import sobel_filter

        self.angles, self.magnitudes = sobel_filter(dog_array)
