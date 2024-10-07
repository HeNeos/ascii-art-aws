import boto3
import cv2

from typing import cast
from PIL import Image
from lambdas.font import Font
from lambdas.types import (
    MediaFile,
    ImageFile,
    VideoFile,
    ImageExtension,
    VideoExtension,
)
from lambdas.utils import split_file_name, calculate_scale, download_from_s3, save_image


s3_client = boto3.client("s3")


def find_media_type(file_path: str) -> MediaFile:
    file_name, file_extension = split_file_name(file_path)
    if file_extension in ImageExtension._value2member_map_:
        return ImageFile(file_name, ImageExtension(file_extension))
    if file_extension in VideoExtension._value2member_map_:
        return VideoFile(file_name, VideoExtension(file_extension))

    raise ValueError(f"Unsupported file extension: {file_extension}")


def rescale_image(image: Image.Image, image_file: ImageFile, bucket_name: str) -> str:
    width, height = image.size
    image_name: str = image_file.file_name
    image_extension: str = image_file.extension
    rescale: int = calculate_scale(height)
    resized_width: int = int(width * (Font.Height.value / Font.Width.value) // rescale)
    resized_height: int = height // rescale
    resized_image_name: str = f"{image_name}_resized.{image_extension}"
    resized_image = image.resize((resized_width, resized_height))
    return save_image(
        s3_client,
        resized_image,
        image_file.extension.value,
        bucket_name,
        resized_image_name,
    )


def resize_frame(frame):
    height, width, _ = frame.shape
    scale = calculate_scale(height)
    return cv2.resize(
        frame,
        (
            int(Font.Height.value / Font.Width.value * width / scale),
            int(height / scale),
        ),
    )


def extract_frames(
    video_capture: cv2.VideoCapture, video_file: VideoFile, bucket_name: str
) -> str:
    frame_id: int = 1
    video_name: str = video_file.file_name
    while True:
        ret, frame = video_capture.read()
        if ret:
            resized_frame: Image.Image = Image.fromarray(
                cv2.cvtColor(resize_frame(frame), cv2.COLOR_BGR2RGB)
            )
            save_image(
                s3_client,
                resized_frame,
                "png",
                bucket_name,
                f"{video_name}/{frame_id:06d}.png",
            )
            frame_id += 1
        else:
            break
    return f"proccessed/{video_name}"


def lambda_handler(event: dict, _) -> dict:
    file_path: str = event["s3"]["object"]["key"]
    bucket_name: str = event["s3"]["bucket"]["name"]
    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    is_video: bool = media_file.extension is VideoExtension
    is_image: bool = media_file.extension is ImageExtension

    response = {"key": file_path, "is_video": is_video, "is_image": is_image}

    if is_video:
        video_capture: cv2.VideoCapture = cv2.VideoCapture(local_file)
        proccessed_key = extract_frames(
            video_capture, cast(VideoFile, media_file), bucket_name
        )
        video_capture.release()
        return {**response, "proccessed_key": proccessed_key}
    if is_image:
        image: Image.Image = Image.open(local_file).convert("RGB")
        proccessed_key = rescale_image(image, cast(ImageFile, media_file), bucket_name)
        return {**response, "proccessed_key": proccessed_key}

    return response
