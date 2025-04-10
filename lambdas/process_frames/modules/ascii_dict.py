from enum import Enum
from typing import TypeAlias


class AsciiDictColor(Enum):
    BigAsciiDict = (
        " `-.'_:,"
        + '"'
        + "~^=;!><+\\/*?crL)7T(|zJsviCltF1}{I3fY[]5nu2xjZoSyeaEPVhkU694KGwbdqOpXHAmRD#08WBM%N$Qg&@"  # noqa: E501
    )
    HighAsciiDict = " :!si{35aVU9qOD#8$&@@"
    LowAsciiDict = " !loa6O#8&@"


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
    HighAsciiDict = "    ``.':;*c7t3eK6ON&@"
    LowAsciiDict = "  `.':;*vx5K4&@"


class DisplayFormats(Enum):
    COLOR = AsciiDictColor
    GRAY_SCALE = AsciiDictGrayScale
    BLACK_AND_WHITE = AsciiDictBlackWhite


AsciiDict: TypeAlias = AsciiDictBlackWhite | AsciiDictColor | AsciiDictGrayScale

display_formats: dict[str, DisplayFormats] = {
    str(DisplayFormats.BLACK_AND_WHITE.value): DisplayFormats.BLACK_AND_WHITE,
    str(DisplayFormats.COLOR.value): DisplayFormats.COLOR,
    str(DisplayFormats.GRAY_SCALE.value): DisplayFormats.GRAY_SCALE,
}
