from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.client import Users
from diagram import (
    AsciiArt,
    CloudProvider,
    AwsNetwork,
    AwsStorage,
    AwsCompute,
    AwsDatabase,
    AwsWorkflow,
    AwsEventListener,
    AwsContainerRegistry,
    GcpStorage,
    GcpNetwork,
    GcpCompute,
    GcpDatabase,
    GcpWorkflow,
    GcpEventListener,
    GcpContainerRegistry,
    cluster_graph_attr,
)
from diagram.names import ProviderName


with Diagram(
    "Ascii Art Architecture",
    filename="diagram/ascii_art",
    show=False,
    direction="TB",
    curvestyle="ortho",
    outformat="pdf",
    graph_attr={
        "pad": "2.0",
        "fontname": "Sans-Serif",
        "fontsize": "32",
    },
    node_attr={"fontname": "Mono", "fontsize": "15"},
):
    users = Users("users")
    ascii_art = AsciiArt(
        AWS=CloudProvider(
            storage=AwsStorage(),
            network=AwsNetwork(),
            compute=AwsCompute(),
            database=AwsDatabase(),
            workflow=AwsWorkflow(),
            event_listener=AwsEventListener(),
            container_registry=AwsContainerRegistry(),
            name=ProviderName.AWS.value,
        ),
        GCP=CloudProvider(
            storage=GcpStorage(),
            network=GcpNetwork(),
            compute=GcpCompute(),
            database=GcpDatabase(),
            workflow=GcpWorkflow(),
            event_listener=GcpEventListener(),
            container_registry=GcpContainerRegistry(),
            name=ProviderName.GCP.value,
        ),
    )

    endpoints = [
        ascii_art.AWS.network.get_presigned_url,
        ascii_art.AWS.network.poll_ascii_art,
    ]

    users - ascii_art.load_balancer_endpoint - ascii_art.load_balancer

    for network_resources in [ascii_art.AWS.network, ascii_art.GCP.network]:
        (
            ascii_art.load_balancer
            - Edge(**ascii_art.network_edge_params)
            - network_resources.api_gateway
        )
        (
            network_resources.api_gateway
            - Edge(**ascii_art.network_edge_params)
            - network_resources.get_presigned_url
        )
        (
            network_resources.api_gateway
            - Edge(**ascii_art.network_edge_params)
            - network_resources.poll_ascii_art
        )

    for cloud_resources in [ascii_art.AWS, ascii_art.GCP]:
        (
            cloud_resources.network.poll_ascii_art
            - Edge(**ascii_art.network_edge_params)
            - cloud_resources.compute.poll
        )
        (
            cloud_resources.network.get_presigned_url
            - Edge(**ascii_art.network_edge_params)
            - cloud_resources.compute.get_presigned_url
            >> Edge(**ascii_art.network_edge_params)
            >> cloud_resources.database.state
        )
        (
            cloud_resources.compute.poll
            - Edge(**ascii_art.network_edge_params)
            - cloud_resources.database.state
        )
        (
            cloud_resources.storage.media
            - Edge(**ascii_art.network_edge_params)
            - cloud_resources.compute.get_presigned_url
        )

    for cloud_resources in [ascii_art.AWS, ascii_art.GCP]:
        (
            cloud_resources.container_registry.container_registry
            - Edge(**ascii_art.container_registry_edge_params)
            - [
                cloud_resources.compute.process_image,
                cloud_resources.compute.downsize_video,
                cloud_resources.compute.downsize_media,
                cloud_resources.compute.extract_audio,
                cloud_resources.compute.merge_frames,
            ]
        )

    for cloud_resources in [ascii_art.AWS, ascii_art.GCP]:
        with Cluster(cloud_resources.name, graph_attr=cluster_graph_attr):
            with Cluster(f"Processing", graph_attr=cluster_graph_attr):
                with Cluster("Video", graph_attr=cluster_graph_attr):
                    with Cluster(
                        "MapProcessFrames",
                        direction="TB",
                        graph_attr=cluster_graph_attr,
                    ):
                        lambda_process_frames = [
                            cloud_resources.compute.process_image.__class__(
                                f"ProcessFrames#{x+1}"
                            )
                            for x in range(1)
                        ]

        (
            users
            >> Edge(color="#b81f1f", style="bold")
            >> cloud_resources.storage.media
            >> Edge(color="#b81f1f", style="dashed")
            >> cloud_resources.event_listener.trigger
            >> cloud_resources.workflow.workflow
        )
        (
            cloud_resources.workflow.workflow
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.compute.downsize_media
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.compute.process_image
        )
        (
            cloud_resources.compute.downsize_media
            - Edge(**ascii_art.lambda_edge_params)
            - cloud_resources.storage.media
            >> Edge(**ascii_art.storage_edge_params)
            >> cloud_resources.compute.process_image
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.database.state
        )
        (
            cloud_resources.compute.process_image
            >> Edge(**ascii_art.lambda_edge_params, style="bold")
            >> ascii_art.ascii_art_storage
        )

        (
            cloud_resources.workflow.workflow
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.compute.downsize_video
            >> Edge(**ascii_art.lambda_edge_params)
            >> [
                *lambda_process_frames,
                cloud_resources.compute.extract_audio,
            ]
        )
        (
            cloud_resources.compute.downsize_video
            - Edge(**ascii_art.lambda_edge_params)
            - cloud_resources.storage.media
        )
        (
            cloud_resources.storage.media
            >> Edge(**ascii_art.storage_edge_params)
            >> lambda_process_frames
        )
        (
            cloud_resources.compute.extract_audio
            << Edge(**ascii_art.storage_edge_params)
            << cloud_resources.storage.media
        )
        (
            cloud_resources.compute.extract_audio
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.storage.audio
            >> Edge(**ascii_art.storage_edge_params)
            >> cloud_resources.compute.merge_frames
        )
        (
            lambda_process_frames
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.compute.merge_frames
        )
        (
            lambda_process_frames
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.storage.ascii_art
        )

        (
            cloud_resources.compute.merge_frames
            << Edge(**ascii_art.lambda_edge_params)
            << cloud_resources.storage.ascii_art
        )
        (
            cloud_resources.compute.merge_frames
            >> Edge(**ascii_art.lambda_edge_params, style="bold")
            >> ascii_art.ascii_art_storage
        )
        (
            cloud_resources.compute.merge_frames
            >> Edge(**ascii_art.lambda_edge_params)
            >> cloud_resources.database.state
        )
