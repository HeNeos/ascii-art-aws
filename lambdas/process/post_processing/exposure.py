from typing import cast
from dataclasses import dataclass
from . import PostProcessingStrategy, PostProcessingStrategyName

from numpy import uint8, array, arange
from numpy.typing import NDArray
from cv2 import LUT


@dataclass
class Exposure(PostProcessingStrategy):
    name: PostProcessingStrategyName = PostProcessingStrategyName.EXPOSURE

    def apply(self, image: NDArray[uint8], value: float) -> NDArray[uint8]:
        """
        Adjusts the exposure of an image using gamma correction.
        value: float, gamma value. >1 makes it darker, <1 makes it brighter. e.g., 0.5
        """
        if value <= 0:
            return image

        inv_gamma = 1.0 / value
        table = array(
            [((i / 255.0) ** inv_gamma) * 255 for i in arange(0, 256)]
        ).astype("uint8")

        return cast(NDArray[uint8], LUT(image, table))
