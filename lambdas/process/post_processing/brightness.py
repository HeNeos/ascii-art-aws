from typing import cast
from dataclasses import dataclass
from numpy import uint8, int16, clip
from numpy.typing import NDArray
from cv2 import COLOR_BGR2HSV, COLOR_HSV2BGR, split, cvtColor, merge

from . import PostProcessingStrategy, PostProcessingStrategyName


@dataclass
class Brightness(PostProcessingStrategy):
    name: PostProcessingStrategyName = PostProcessingStrategyName.BRIGHTNESS

    def apply(self, image: NDArray[uint8], value: float) -> NDArray[uint8]:
        """
        Adjusts the brightness of an image.
        """
        hsv: NDArray[uint8] = cast(NDArray[uint8], cvtColor(image, COLOR_BGR2HSV))
        h, s, v = split(hsv)

        v = clip(v.astype(int16) + value, 0, 255).astype(uint8)

        final_hsv = merge((h, s, v))
        return cast(NDArray[uint8], cvtColor(final_hsv, COLOR_HSV2BGR))
