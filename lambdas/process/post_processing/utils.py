from functools import cache
from importlib import import_module
from typing import cast

from numpy import uint8
from numpy.typing import NDArray

from . import PostProcessingStrategy


class PostProcessingLoader:
    @staticmethod
    def _get_module_and_class(strategy_name: str) -> tuple[str, str]:
        module_name = f".{strategy_name}"
        class_name = strategy_name.capitalize()
        return module_name, class_name

    @staticmethod
    @cache
    def get_strategy(name: str) -> PostProcessingStrategy | None:
        try:
            module_name, class_name = PostProcessingLoader._get_module_and_class(name)
            module = import_module(module_name, package=__package__)
            strategy_class = getattr(module, class_name)
            return cast("PostProcessingStrategy", strategy_class())
        except (ImportError, AttributeError):
            return None


def get_post_processing_strategy(name: str) -> PostProcessingStrategy | None:
    return PostProcessingLoader.get_strategy(name)


def apply_post_processing(image: NDArray[uint8]) -> NDArray[uint8]:
    post_processing_parameters: dict[str, float] = {
        "brightness": 6.0,
        "contrast": 1.28,
        "saturation": 1.22,
        "exposure": 1.18,
    }

    for filter, value in post_processing_parameters.items():
        filter_strategy: PostProcessingStrategy | None = get_post_processing_strategy(
            filter,
        )
        if filter_strategy:
            image = filter_strategy.apply(image, value)
    return image
