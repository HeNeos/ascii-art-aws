from abc import ABC, abstractmethod

from cairo import Context, ImageSurface

from lambdas.models.media_file import Color
from lambdas.process.ascii_dict import DisplayFormats


class CairoContext(ABC, Context):
    def __init__(self, surface: ImageSurface) -> None:
        self.context = Context(surface)

    @abstractmethod
    def set_color(self, color: Color, luminance: float) -> None:
        pass


class CairoColorContext(CairoContext):
    def set_color(self, color: Color, luminance: float) -> None:
        self.context.set_source_rgb(color[0] / 255, color[1] / 255, color[2] / 255)


class CairoGrayContext(CairoContext):
    def set_color(self, color: Color, luminance: float) -> None:
        self.context.set_source_rgb(luminance / 255, luminance / 255, luminance / 255)


class CairoBlackAndWhiteContext(CairoContext):
    def set_color(self, color: Color, luminance: float) -> None:
        self.context.set_source_rgb(1.0, 1.0, 1.0)


class CairoContextFactory:
    @staticmethod
    def create(display_format: DisplayFormats, surface: ImageSurface) -> CairoContext:
        match display_format:
            case DisplayFormats.COLOR:
                return CairoColorContext(surface)
            case DisplayFormats.GRAY_SCALE:
                return CairoGrayContext(surface)
            case DisplayFormats.BLACK_AND_WHITE:
                return CairoBlackAndWhiteContext(surface)
