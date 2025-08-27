from typing import cast
from dataclasses import dataclass
from . import PostProcessingStrategy, PostProcessingStrategyName

from numpy import uint8, float32, clip
from numpy.typing import NDArray
from cv2 import cvtColor, COLOR_HSV2BGR, COLOR_BGR2HSV, split, merge


@dataclass
class Saturation(PostProcessingStrategy):
    name: PostProcessingStrategyName = PostProcessingStrategyName.SATURATION

    def apply(self, image: NDArray[uint8], value: float) -> NDArray[uint8]:
        """
        Adjusts the saturation of an image.
        value: float, saturation factor. >1 increases saturation, <1 decreases. e.g., 1.5
        """
        hsv = cvtColor(image, COLOR_BGR2HSV)
        h, s, v = split(hsv)

        s = clip(s.astype(float32) * value, 0, 255).astype(uint8)

        final_hsv = merge((h, s, v))
        return cast(NDArray[uint8], cvtColor(final_hsv, COLOR_HSV2BGR))
