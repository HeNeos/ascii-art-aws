from enum import Enum
from dataclasses import dataclass


class ProviderName(Enum):
    AWS = "AWS"
    GCP = "GCP"


@dataclass
class StorageName:
    media = "media"
    audio = "audio"
    ascii_art = "ascii-art"


@dataclass
class NetworkName:
    api_gateway = "api-gateway"
    load_balancer_endpoint = "load-balancer-endpoint"
    load_balancer = "load-balancer"
    get_presigned_url = "endpoint"
    poll_ascii_art = "endpoint"


@dataclass
class ComputeName:
    downsize_media = "downsize-media"
    downsize_video = "downsize-video"
    extract_audio = "extract-audio"
    process_image = "process-image"
    merge_frames = "merge-frames"
    get_presigned_url = "get-presigned-url"
    poll = "poll"


@dataclass
class DatabaseName:
    state = "state"


@dataclass
class WorkflowName:
    workflow = "processing"


@dataclass
class EventListenerName:
    trigger = "trigger-workflow"


@dataclass
class ContainerRegistryName:
    container_registry = "lambda-images"
