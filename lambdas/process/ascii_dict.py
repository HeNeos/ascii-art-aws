from enum import Enum
from typing import TypeAlias
from numpy import array


class AsciiDictColor(Enum):
    BigAsciiDict = (
        " `-.'_:,"
        + '"'
        + "~^=;!><+\\/*?crL)7T(|zJsviCltF1}{I3fY[]5nu2xjZoSyeaEPVhkU694KGwbdqOpXHAmRD#08WBM%N$Qg&@"  # noqa: E501
    )
    HighAsciiDict = " :!*si{35aVU9qOD#8$&@"
    LowAsciiDict = " :!loa6O#&@"


class AsciiDictGrayScale(Enum):
    BigAsciiDict = (
        " `-.'_:,"
        + '"'
        + "~^=;!><+\\/*?crL)7T(|zJsviCltF1}{I3fY[]5nu2xjZoSyeaEPVhkU694KGwbdqOpXHAmRD#08WBM%N$Qg&@"  # noqa: E501
    )
    HighAsciiDict = " !*i713noah6bdwmD08B@"
    LowAsciiDict = " !*i1oawhb8B@"


class AsciiDictBlackWhite(Enum):
    BigAsciiDict = (
        " `-.'_:,"
        + '"'
        + "~^=;!><+\\/*?crL)7T(|zJsviCltF1}{I3fY[]5nu2xjZoSyeaEPVhkU694KGwbdqOpXHAmRD#08WBM%N$Qg&@"  # noqa: E501
    )
    HighAsciiDict = "  ```.':,;+*c7t13ueK6O#&@"
    LowAsciiDict = "  `.':;*vx5K4&@"


AsciiDictEdges = array(list("|_/\\"))


class DisplayFormats(Enum):
    COLOR = AsciiDictColor
    GRAY_SCALE = AsciiDictGrayScale
    BLACK_AND_WHITE = AsciiDictBlackWhite


AsciiDict: TypeAlias = AsciiDictBlackWhite | AsciiDictColor | AsciiDictGrayScale

display_formats: dict[str, DisplayFormats] = {
    DisplayFormats.BLACK_AND_WHITE.name: DisplayFormats.BLACK_AND_WHITE,
    DisplayFormats.COLOR.name: DisplayFormats.COLOR,
    DisplayFormats.GRAY_SCALE.name: DisplayFormats.GRAY_SCALE,
}
