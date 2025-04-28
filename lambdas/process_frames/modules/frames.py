from dataclasses import dataclass
from typing import TypeAlias
from numpy import uint8
from numpy.typing import NDArray


@dataclass
class FrameData:
    frame: NDArray[uint8]
    frame_id: int
    video_name: str


Frames: TypeAlias = list[FrameData]
