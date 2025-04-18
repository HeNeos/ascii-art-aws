from dataclasses import dataclass
from abc import ABC
from typing import TypeAlias

from diagrams import Cluster, Diagram
from diagrams.onprem.client import Users
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import StepFunctions
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import (
    APIGateway as AwsApiGateway,
    APIGatewayEndpoint as AwsApiGatewayEndpoint,
    ElasticLoadBalancing as AwsElasticLoadBalancing,
)
from diagrams.aws.storage import SimpleStorageServiceS3Bucket

from diagrams.gcp.compute import Functions
from diagrams.gcp.storage import Storage
from diagrams.gcp.api import (
    APIGateway as GcpApiGateway,
    Endpoints as GcpApiGatewayEndpoint,
)
from diagrams.gcp.network import LoadBalancing as GcpElasticLoadBalancing
from diagrams.gcp.database import Firestore
from diagrams.custom import Custom

GenericStorage: TypeAlias = SimpleStorageServiceS3Bucket | Storage
GenericApiGateway: TypeAlias = AwsApiGateway | GcpApiGateway
GenericLoadBalancer: TypeAlias = AwsElasticLoadBalancing | GcpElasticLoadBalancing
GenericApiGatewayEndpoint: TypeAlias = AwsApiGatewayEndpoint | GcpApiGatewayEndpoint
GenericFunction: TypeAlias = Lambda | Functions
GenericDatabase: TypeAlias = Dynamodb | Firestore
GenericWorkflow: TypeAlias = StepFunctions | Custom


@dataclass
class StorageName:
    media = "media-storage"
    audio = "audio-storage"
    ascii_art = "ascii-art-storage"


@dataclass
class NetworkName:
    api_gateway = "api-gateway"
    load_balancer_endpoint = "load_balancer-endpoint"
    load_balancer = "load-balancer"
    get_presigned_url = "get-presigned-url-endpoint"
    poll_ascii_art = "poll-ascii-art-endpoint"


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
class AsciiArtStorage(ABC):
    media: GenericStorage
    audio: GenericStorage
    ascii_art: GenericStorage


@dataclass
class AsciiArtNetwork(ABC):
    api_gateway: GenericApiGateway
    load_balancer_endpoint: GenericApiGatewayEndpoint
    load_balancer: GenericLoadBalancer
    get_presigned_url: GenericApiGatewayEndpoint
    poll_ascii_art: GenericApiGatewayEndpoint


@dataclass
class AsciiArtCompute(ABC):
    downsize_media: GenericFunction
    downsize_video: GenericFunction
    extract_audio: GenericFunction
    process_image: GenericFunction
    merge_frames: GenericFunction
    get_presigned_url: GenericFunction
    poll: GenericFunction


@dataclass
class AsciiArtDatabase(ABC):
    state: GenericDatabase


@dataclass
class AsciiArtWorkflow(ABC):
    workflow: GenericWorkflow


class AwsStorage(AsciiArtStorage):
    def __init__(self) -> None:
        with Cluster("AWS"):
            with Cluster("Storage"):
                self.media = SimpleStorageServiceS3Bucket(StorageName.media)
                self.audio = SimpleStorageServiceS3Bucket(StorageName.audio)
                self.ascii_art = SimpleStorageServiceS3Bucket(StorageName.ascii_art)


class GcpStorage(AsciiArtStorage):
    def __init__(self) -> None:
        with Cluster("GCP"):
            with Cluster("Storage"):
                self.media = Storage(StorageName.media)
                self.audio = Storage(StorageName.audio)
                self.ascii_art = Storage(StorageName.ascii_art)


class AwsNetwork(AsciiArtNetwork):
    def __init__(self) -> None:
        with Cluster("AWS"):
            with Cluster("Load-Balancer"):
                self.load_balancer_endpoint = AwsApiGatewayEndpoint(
                    NetworkName.load_balancer_endpoint
                )
                self.load_balancer = AwsElasticLoadBalancing(NetworkName.load_balancer)
            with Cluster("API-GW"):
                self.api_gateway = AwsApiGateway(NetworkName.api_gateway)
                with Cluster("Get-Presigned-Url"):
                    self.get_presigned_url = AwsApiGatewayEndpoint(
                        NetworkName.get_presigned_url
                    )
                with Cluster("Poll"):
                    self.poll_ascii_art = AwsApiGatewayEndpoint(
                        NetworkName.poll_ascii_art
                    )


class GcpNetwork(AsciiArtNetwork):
    def __init__(self) -> None:
        with Cluster("GCP"):
            with Cluster("Load-Balancer"):
                self.load_balancer_endpoint = GcpApiGatewayEndpoint(
                    NetworkName.load_balancer_endpoint
                )
                self.load_balancer = GcpElasticLoadBalancing(NetworkName.load_balancer)
            with Cluster("API-GW"):
                self.api_gateway = GcpApiGateway(NetworkName.api_gateway)
                with Cluster("Get-Presigned-Url"):
                    self.get_presigned_url = GcpApiGatewayEndpoint(
                        NetworkName.get_presigned_url
                    )
                with Cluster("Poll"):
                    self.poll_ascii_art = GcpApiGatewayEndpoint(
                        NetworkName.poll_ascii_art
                    )


class AwsCompute(AsciiArtCompute):
    def __init__(self) -> None:
        with Cluster("AWS"):
            with Cluster("Processing"):
                self.downsize_media = Lambda(ComputeName.downsize_media)
                self.downsize_video = Lambda(ComputeName.downsize_video)
                self.extract_audio = Lambda(ComputeName.extract_audio)
                self.process_image = Lambda(ComputeName.process_image)
                self.merge_frames = Lambda(ComputeName.merge_frames)
            with Cluster("API-GW"):
                with Cluster("Get-Presigned-Url"):
                    self.get_presigned_url = Lambda(ComputeName.get_presigned_url)
                with Cluster("Poll"):
                    self.poll = Lambda(ComputeName.poll)


class GcpCompute(AsciiArtCompute):
    def __init__(self) -> None:
        with Cluster("GCP"):
            with Cluster("Processing"):
                self.downsize_media = Functions(ComputeName.downsize_media)
                self.downsize_video = Functions(ComputeName.downsize_video)
                self.extract_audio = Functions(ComputeName.extract_audio)
                self.process_image = Functions(ComputeName.process_image)
                self.merge_frames = Functions(ComputeName.merge_frames)
            with Cluster("API-GW"):
                with Cluster("Get-Presigned-Url"):
                    self.get_presigned_url = Functions(ComputeName.get_presigned_url)
                with Cluster("Poll"):
                    self.poll = Functions(ComputeName.poll)


class AwsDatabase(AsciiArtDatabase):
    def __init__(self) -> None:
        with Cluster("AWS"):
            self.state = Dynamodb(DatabaseName.state)


class GcpDatabase(AsciiArtDatabase):
    def __init__(self) -> None:
        with Cluster("GCP"):
            self.state = Firestore(DatabaseName.state)


class AwsWorkflow(AsciiArtWorkflow):
    def __init__(self) -> None:
        with Cluster("AWS"):
            self.workflow = StepFunctions(WorkflowName.workflow)


class GcpWorkflow(AsciiArtWorkflow):
    def __init__(self) -> None:
        with Cluster("GCP"):
            self.workflow = Custom(WorkflowName.workflow, "./workflows.png")


@dataclass
class CloudProvider:
    storage: AsciiArtStorage
    network: AsciiArtNetwork
    compute: AsciiArtCompute
    database: AsciiArtDatabase
    workflow: AsciiArtWorkflow
    name: str


@dataclass
class AsciiArt:
    AWS: CloudProvider
    GCP: CloudProvider


with Diagram("Ascii Art", show=False, direction="TB"):
    users = Users("users")
    ascii_art = AsciiArt(
        AWS=CloudProvider(
            storage=AwsStorage(),
            network=AwsNetwork(),
            compute=AwsCompute(),
            database=AwsDatabase(),
            workflow=AwsWorkflow(),
            name="AWS",
        ),
        GCP=CloudProvider(
            storage=GcpStorage(),
            network=GcpNetwork(),
            compute=GcpCompute(),
            database=GcpDatabase(),
            workflow=GcpWorkflow(),
            name="GCP",
        ),
    )

    # TODO: Change for cloudflare kv
    requests_table = Dynamodb("requests_table")

    for network_resources in [ascii_art.AWS.network, ascii_art.GCP.network]:
        (
            users
            >> network_resources.api_gateway
            >> network_resources.load_balancer_endpoint
            >> network_resources.load_balancer - requests_table
        )

    with Cluster("Endpoints"):
        endpoints = [
            ascii_art.AWS.network.get_presigned_url,
            ascii_art.AWS.network.poll_ascii_art,
        ]

    for cloud_resources in [ascii_art.AWS, ascii_art.GCP]:
        cloud_resources.network.load_balancer >> endpoints
        (
            cloud_resources.network.get_presigned_url
            >> cloud_resources.compute.get_presigned_url
            >> [users, cloud_resources.database.state]
        )
        (
            cloud_resources.network.poll_ascii_art
            >> cloud_resources.compute.poll - cloud_resources.database.state
        )
        cloud_resources.storage.media >> cloud_resources.compute.get_presigned_url

    for cloud_resources in [ascii_art.AWS, ascii_art.GCP]:
        with Cluster(cloud_resources.name):
            with Cluster(f"Processing"):
                with Cluster("MapProcessFrames"):
                    lambda_process_frames = [
                        cloud_resources.compute.process_image.__class__(
                            f"ProcessFrames#{x+1}"
                        )
                        for x in range(3)
                    ]

                (
                    users
                    >> cloud_resources.storage.media
                    >> cloud_resources.workflow.workflow
                )
                (
                    cloud_resources.workflow.workflow
                    >> cloud_resources.compute.downsize_media
                    >> [
                        cloud_resources.compute.process_image,
                        cloud_resources.storage.media,
                    ]
                )
                cloud_resources.compute.process_image >> [
                    cloud_resources.database.state,
                    cloud_resources.storage.ascii_art,
                ]
                cloud_resources.storage.media >> cloud_resources.compute.process_image

                (
                    cloud_resources.workflow.workflow
                    >> cloud_resources.compute.downsize_video
                    >> [
                        *lambda_process_frames,
                        cloud_resources.storage.media,
                        cloud_resources.compute.extract_audio,
                    ]
                )
                cloud_resources.storage.media >> lambda_process_frames
                (
                    cloud_resources.compute.extract_audio
                    >> cloud_resources.storage.audio
                    >> cloud_resources.compute.merge_frames
                )
                lambda_process_frames >> cloud_resources.compute.merge_frames
                lambda_process_frames >> cloud_resources.storage.ascii_art

                (
                    cloud_resources.compute.merge_frames
                    - cloud_resources.storage.ascii_art
                    >> cloud_resources.compute.process_image
                )
                cloud_resources.compute.merge_frames >> cloud_resources.database.state
