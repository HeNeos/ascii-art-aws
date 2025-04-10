from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

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
    random_id: str


class VideoExtension(Enum):
    MP4 = "mp4"
    WEBM = "webm"


@dataclass
class VideoFile:
    file_name: str
    extension: VideoExtension
    random_id: str


@dataclass
class R2Credentials:
    cloudflare_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    ascii_art_bucket_name: str


MediaFile: TypeAlias = ImageFile | VideoFile
