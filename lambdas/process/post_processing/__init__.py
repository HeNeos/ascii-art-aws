from abc import ABC, abstractmethod
from dataclasses import dataclass
from numpy import uint8
from numpy.typing import NDArray
from enum import Enum


class PostProcessingStrategyName(Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    EXPOSURE = "exposure"
    SATURATION = "saturation"


@dataclass
class PostProcessingStrategy(ABC):
    name: PostProcessingStrategyName

    @abstractmethod
    def apply(self, image: NDArray[uint8], value: float) -> NDArray[uint8]:
        """
        Applies a post-processing effect to an image.

        Args:
            image: The input image as a NumPy array (BGR format).
            value: The intensity of the effect.

        Returns:
            The processed image as a NumPy array.
        """
        pass
