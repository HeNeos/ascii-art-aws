from typing import TypeAlias
from PIL import Image
from dataclasses import dataclass
from enum import Enum
from cv2.typing import MatLike

Scale: TypeAlias = float | int
Color: TypeAlias = tuple[int, int, int]
AsciiImage: TypeAlias = list[list[str]]
AsciiColors: TypeAlias = list[list[Color]]


class ImageExtension(Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


@dataclass
class ImageFile:
    file_name: str
    extension: ImageExtension


class VideoExtension(Enum):
    MP4 = "mp4"
    WEBM = "webm"


@dataclass
class VideoFile:
    file_name: str
    extension: VideoExtension


MediaFile: TypeAlias = ImageFile | VideoFile


@dataclass
class FrameData:
    frame: Image.Image | MatLike
    frame_id: int
    video_name: str


Frames: TypeAlias = list[FrameData]
