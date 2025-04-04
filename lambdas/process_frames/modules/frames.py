from dataclasses import dataclass
from cv2.typing import MatLike
from PIL import Image
from typing import TypeAlias


@dataclass
class FrameData:
    frame: Image.Image | MatLike
    frame_id: int
    video_name: str


Frames: TypeAlias = list[FrameData]
