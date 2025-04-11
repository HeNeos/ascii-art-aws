from logging import LoggerAdapter
from diagrams import Cluster, Diagram
from diagrams.onprem.client import Users
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import StepFunctions
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway, APIGatewayEndpoint
from diagrams.aws.storage import SimpleStorageServiceS3Bucket

with Diagram("Ascii Art", show=False, direction="LR"):
    users = Users("users")
    api_gateway = APIGateway("ascii_art")
    get_presigned_url = APIGatewayEndpoint("get_presigned_url")
    poll_ascii_art = APIGatewayEndpoint("poll_ascii_art")

    with Cluster("Endpoints"):
        endpoints = [get_presigned_url, poll_ascii_art]

    get_presigned_url_lambda = Lambda("get_presigned_url")
    poll_lambda = Lambda("poll_lambda")

    state_table = Dynamodb("state_table")

    users >> api_gateway >> endpoints
    get_presigned_url >> get_presigned_url_lambda >> [users, state_table]
    poll_ascii_art >> poll_lambda
    state_table >> poll_lambda

    media_bucket = SimpleStorageServiceS3Bucket("media_bucket")
    audio_bucket = SimpleStorageServiceS3Bucket("audio_bucket")
    ascii_art_bucket = SimpleStorageServiceS3Bucket("ascii_art_bucket")

    media_bucket >> get_presigned_url_lambda

    step_function = StepFunctions("ascii_art_workflow")
    downsize_media = Lambda("DownsizeMedia")
    downsize_video = Lambda("DownsizeVideo")
    extract_audio = Lambda("ExtractAudio")
    process_frames = Lambda("ProcessFrames")
    merge_frames = Lambda("MergeFrames")

    with Cluster("Processing"):
        lambda_functions = [
            downsize_media,
            downsize_video,
            extract_audio,
            process_frames,
            merge_frames,
        ]
        with Cluster("MapProcessFrames"):
            lambda_process_frames = [Lambda(f"ProcessFrames#{x+1}") for x in range(3)]

    users >> media_bucket >> step_function
    (
        step_function
        >> downsize_media
        >> process_frames
        >> [state_table, ascii_art_bucket]
    )
    downsize_media >> media_bucket >> process_frames
    (
        step_function
        >> downsize_video
        >> [*lambda_process_frames, media_bucket, extract_audio]
    )
    media_bucket >> lambda_process_frames
    extract_audio >> audio_bucket >> merge_frames
    lambda_process_frames >> merge_frames
    lambda_process_frames >> ascii_art_bucket
    merge_frames >> [state_table, ascii_art_bucket]

    ascii_art_bucket >> [merge_frames, process_frames]
