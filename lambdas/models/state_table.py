from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class AsciiArtTableKeys(Enum):
    HASH_KEY = "status"
    RANGE_KEY = "id"


class AsciiArtTableStatus(Enum):
    FINISHED = "FINISHED"
    PENDING = "PENDING"


@dataclass
class AsciiArtTableItem:
    status: AsciiArtTableStatus
    id: str
    dithering: str
    edge_detection: bool
    resolution: str
    output: str


class AsciiArtTableItemResponseString(TypedDict):
    S: str


class AsciiArtTableItemResponseBool(TypedDict):
    BOOL: bool


class AsciiArtTableItemResponse(TypedDict):
    status: AsciiArtTableItemResponseString
    id: AsciiArtTableItemResponseString
    dithering: AsciiArtTableItemResponseString
    edge_detection: AsciiArtTableItemResponseBool
    resolution: AsciiArtTableItemResponseString
    output: AsciiArtTableItemResponseString
