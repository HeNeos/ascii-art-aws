import subprocess
from uuid import uuid4

import pathlib


def get_video_framerate(video_path: str) -> float:
    ffprobe_command = [
        "ffprobe",
        "-v",
        "0",
        "-of",
        "csv=p=0",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        f"{video_path}",
    ]
    ffprobe_result = subprocess.run(ffprobe_command, capture_output=True, text=True)
    x, y = map(int, ffprobe_result.stdout.strip().split("/"))
    frame_rate: float = float(x / y)
    return frame_rate


def get_total_frames(video_path: str) -> int:
    ffprobe_command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_packets",
        "-show_entries",
        "stream=nb_read_packets",
        "-of",
        "csv=p=0",
        f"{video_path}",
    ]
    ffprobe_result = subprocess.run(ffprobe_command, capture_output=True, text=True)
    frames: int = int(ffprobe_result.stdout.strip())
    return frames


def get_video_resolution(video_path: str) -> tuple[int, int]:
    ffprobe_command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_path,
    ]
    ffprobe_result = subprocess.run(ffprobe_command, capture_output=True, text=True)

    video_width, video_height = map(
        int, ffprobe_result.stdout.strip().split()[0].split("x")
    )
    return video_width, video_height


def resize_video(
    video_path: str,
    width: int,
    height: int,
    output_path: str,
    compression_level: int = 20,
) -> None:
    ffmpeg_command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        video_path,
        "-threads",
        "0",
        "-vf",
        f"scale={width}:{height}",
        "-crf",
        f"{compression_level}",
        "-preset",
        "fast",
        output_path,
    ]
    subprocess.run(ffmpeg_command, check=True)


def extract_audio(video_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "mp3",
        output_path,
    ]
    subprocess.run(command, check=True)


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]

    subprocess.run(command, check=True)


def merge_videos(video_files: list[str], output_path: str) -> None:
    random_id = uuid4()
    concat_file = f"/tmp/concat_list-{random_id}.txt"
    with open(concat_file, "w") as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")

    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        output_path,
    ]

    subprocess.run(command, check=True)


def merge_frames(
    frames_filename: list[str], frame_rate: float, output_path: str, crf: int = 28
) -> None:
    random_id = uuid4()
    concat_file = f"/tmp/concat_list-{random_id}.txt"
    with open(concat_file, "w+") as f:
        for frame_filename in frames_filename:
            path: str = str((pathlib.Path().joinpath(frame_filename)).resolve())
            f.write(f"file '{path}'\n")

    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-r",
        str(frame_rate),
        "-f",
        "concat",
        "-safe",
        "0",
        "-threads",
        "0",
        "-i",
        concat_file,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-g",
        "128",
        "-crf",
        f"{crf}",
        "-preset",
        "faster",
        output_path,
    ]
    subprocess.run(command, check=True)


def get_video_length(video_path: str) -> float:
    ffmpeg_command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    video_length: str = subprocess.run(
        ffmpeg_command, capture_output=True, text=True
    ).stdout.strip()
    return float(video_length)


def trim_video(
    video_path: str, start_time: str, duration: str | None, output_path: str
) -> None:
    ffmpeg_command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-ss",
        start_time,
        "-i",
        video_path,
    ]

    if duration:
        ffmpeg_command += ["-t", duration]

    # It's re-encoding again to avoid miss key-frames
    ffmpeg_command += ["-async", "1", output_path]

    # # trying copying the video stream
    # ffmpeg_command += ["-c", "copy", "-y", output_path]

    subprocess.run(ffmpeg_command, check=True)
