from dataclasses import dataclass
from abc import ABC
from typing import TypeAlias

from diagrams import Cluster
from diagrams.aws.compute import Lambda, EC2ContainerRegistry
from diagrams.aws.integration import StepFunctions
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import (
    APIGateway as AwsApiGateway,
    APIGatewayEndpoint as AwsApiGatewayEndpoint,
    ElasticLoadBalancing as AwsElasticLoadBalancing,
)
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.aws.integration import Eventbridge

from diagrams.gcp.compute import Functions
from diagrams.gcp.storage import Storage
from diagrams.gcp.api import (
    APIGateway as GcpApiGateway,
    Endpoints as GcpApiGatewayEndpoint,
)
from diagrams.gcp.network import LoadBalancing as GcpElasticLoadBalancing
from diagrams.gcp.database import Firestore
from diagrams.gcp.devtools import ContainerRegistry
from diagrams.custom import Custom

from .names import (
    ProviderName,
    NetworkName,
    ComputeName,
    ContainerRegistryName,
    StorageName,
    DatabaseName,
    WorkflowName,
    EventListenerName,
)


cluster_graph_attr = {"fontsize": "18"}

GenericStorage: TypeAlias = SimpleStorageServiceS3Bucket | Storage
GenericApiGateway: TypeAlias = AwsApiGateway | GcpApiGateway
GenericLoadBalancer: TypeAlias = AwsElasticLoadBalancing | GcpElasticLoadBalancing
GenericApiGatewayEndpoint: TypeAlias = AwsApiGatewayEndpoint | GcpApiGatewayEndpoint
GenericFunction: TypeAlias = Lambda | Functions
GenericDatabase: TypeAlias = Dynamodb | Firestore
GenericWorkflow: TypeAlias = StepFunctions | Custom
GenericEventListener: TypeAlias = Eventbridge | Custom
GenericContainerRegistry: TypeAlias = EC2ContainerRegistry | ContainerRegistry


@dataclass
class AsciiArtStorage(ABC):
    media: GenericStorage
    audio: GenericStorage
    ascii_art: GenericStorage


@dataclass
class AsciiArtNetwork(ABC):
    api_gateway: GenericApiGateway
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


@dataclass
class AsciiArtEventListener(ABC):
    trigger: GenericEventListener


@dataclass
class AsciiArtContainerRegistry(ABC):
    container_registry: GenericContainerRegistry


class AwsStorage(AsciiArtStorage):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            # with Cluster("Storage", direction="TB"):
            self.media = SimpleStorageServiceS3Bucket(StorageName.media)
            self.ascii_art = SimpleStorageServiceS3Bucket(StorageName.ascii_art)
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Video", graph_attr=cluster_graph_attr):
                    with Cluster("Audio", graph_attr=cluster_graph_attr):
                        self.audio = SimpleStorageServiceS3Bucket(StorageName.audio)


class GcpStorage(AsciiArtStorage):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            # with Cluster("Storage", direction="TB"):
            self.media = Storage(StorageName.media)
            self.ascii_art = Storage(StorageName.ascii_art)
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Video", graph_attr=cluster_graph_attr):
                    with Cluster("Audio", graph_attr=cluster_graph_attr):
                        self.audio = Storage(StorageName.audio)


class AwsNetwork(AsciiArtNetwork):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            with Cluster("API-GW", graph_attr=cluster_graph_attr):
                self.api_gateway = AwsApiGateway(NetworkName.api_gateway)
                with Cluster("Get-Presigned-Url", graph_attr=cluster_graph_attr):
                    self.get_presigned_url = AwsApiGatewayEndpoint(
                        NetworkName.get_presigned_url
                    )
                with Cluster("Poll", graph_attr=cluster_graph_attr):
                    self.poll_ascii_art = AwsApiGatewayEndpoint(
                        NetworkName.poll_ascii_art
                    )


class GcpNetwork(AsciiArtNetwork):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            with Cluster("API-GW", graph_attr=cluster_graph_attr):
                self.api_gateway = GcpApiGateway(NetworkName.api_gateway)
                with Cluster("Get-Presigned-Url", graph_attr=cluster_graph_attr):
                    self.get_presigned_url = GcpApiGatewayEndpoint(
                        NetworkName.get_presigned_url
                    )
                with Cluster("Poll", graph_attr=cluster_graph_attr):
                    self.poll_ascii_art = GcpApiGatewayEndpoint(
                        NetworkName.poll_ascii_art
                    )


class AwsCompute(AsciiArtCompute):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Image", graph_attr=cluster_graph_attr):
                    self.downsize_media = Lambda(ComputeName.downsize_media)
                    self.process_image = Lambda(ComputeName.process_image)
                with Cluster("Video", graph_attr=cluster_graph_attr):
                    self.downsize_video = Lambda(ComputeName.downsize_video)
                    self.merge_frames = Lambda(ComputeName.merge_frames)
                    with Cluster("Audio", graph_attr=cluster_graph_attr):
                        self.extract_audio = Lambda(ComputeName.extract_audio)
            with Cluster("API-GW", graph_attr=cluster_graph_attr):
                with Cluster("Get-Presigned-Url", graph_attr=cluster_graph_attr):
                    self.get_presigned_url = Lambda(ComputeName.get_presigned_url)
                with Cluster("Poll", graph_attr=cluster_graph_attr):
                    self.poll = Lambda(ComputeName.poll)


class GcpCompute(AsciiArtCompute):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Image", graph_attr=cluster_graph_attr):
                    self.downsize_media = Functions(ComputeName.downsize_media)
                    self.process_image = Functions(ComputeName.process_image)
                with Cluster("Video", graph_attr=cluster_graph_attr):
                    self.downsize_video = Functions(ComputeName.downsize_video)
                    self.merge_frames = Functions(ComputeName.merge_frames)
                    with Cluster("Audio", graph_attr=cluster_graph_attr):
                        self.extract_audio = Functions(ComputeName.extract_audio)
            with Cluster("API-GW", graph_attr=cluster_graph_attr):
                with Cluster("Get-Presigned-Url", graph_attr=cluster_graph_attr):
                    self.get_presigned_url = Functions(ComputeName.get_presigned_url)
                with Cluster("Poll", graph_attr=cluster_graph_attr):
                    self.poll = Functions(ComputeName.poll)


class AwsDatabase(AsciiArtDatabase):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            self.state = Dynamodb(DatabaseName.state)


class GcpDatabase(AsciiArtDatabase):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            self.state = Firestore(DatabaseName.state)


class AwsWorkflow(AsciiArtWorkflow):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Put-Event", graph_attr=cluster_graph_attr):
                    self.workflow = StepFunctions(WorkflowName.workflow)


class GcpWorkflow(AsciiArtWorkflow):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Put-Event", graph_attr=cluster_graph_attr):
                    self.workflow = Custom(WorkflowName.workflow, "./workflows.png")


class AwsEventListener(AsciiArtEventListener):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Put-Event", graph_attr=cluster_graph_attr):
                    self.trigger = Eventbridge(EventListenerName.trigger)


class GcpEventListener(AsciiArtEventListener):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            with Cluster("Processing", graph_attr=cluster_graph_attr):
                with Cluster("Put-Event", graph_attr=cluster_graph_attr):
                    self.trigger = Custom(EventListenerName.trigger, "./eventarc.png")


class AwsContainerRegistry(AsciiArtContainerRegistry):
    def __init__(self) -> None:
        with Cluster(ProviderName.AWS.value, graph_attr=cluster_graph_attr):
            self.container_registry = EC2ContainerRegistry(
                ContainerRegistryName.container_registry
            )


class GcpContainerRegistry(AsciiArtContainerRegistry):
    def __init__(self) -> None:
        with Cluster(ProviderName.GCP.value, graph_attr=cluster_graph_attr):
            self.container_registry = ContainerRegistry(
                ContainerRegistryName.container_registry
            )


@dataclass
class CloudProvider:
    storage: AsciiArtStorage
    network: AsciiArtNetwork
    compute: AsciiArtCompute
    database: AsciiArtDatabase
    workflow: AsciiArtWorkflow
    event_listener: AsciiArtEventListener
    container_registry: AsciiArtContainerRegistry
    name: str


@dataclass
class AsciiArt:
    AWS: CloudProvider
    GCP: CloudProvider

    def __post_init__(self) -> None:
        self.load_balancer_endpoint = Custom(
            NetworkName.load_balancer_endpoint, "./cloudflare_workers.png"
        )
        self.load_balancer = Custom(
            NetworkName.load_balancer, "./cloudflare_workers.png"
        )
        self.ascii_art_storage = Custom(StorageName.ascii_art, "./cloudflare_r2.png")

        self.lambda_edge_params = {"color": "#151269"}
        self.storage_edge_params = {"style": "bold", "color": "darkgreen"}
        self.container_registry_edge_params = {"style": "dashed"}
        self.network_edge_params = {"style": "bold", "color": "#670e69"}
