from dataclasses import dataclass
from typing import cast

from cv2 import convertScaleAbs
from numpy import uint8
from numpy.typing import NDArray

from . import PostProcessingStrategy, PostProcessingStrategyName


@dataclass
class Contrast(PostProcessingStrategy):
    name: PostProcessingStrategyName = PostProcessingStrategyName.CONTRAST

    def apply(self, image: NDArray[uint8], value: float) -> NDArray[uint8]:
        """Adjusts the contrast of an image.
        value: float, contrast factor. >1 increases contrast, <1 decreases. e.g., 1.5
        """
        return cast("NDArray[uint8]", convertScaleAbs(image, alpha=value, beta=0))
