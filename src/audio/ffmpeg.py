# -*- coding: utf-8 -*-
# Copyright (c) 2024, https://github.com/skys-mission and Half-Bottled Reverie
"""
ffmpeg
"""
import os
import platform
import subprocess
import tempfile
from pathlib import Path


def convert_to_wav_16000(audio_path):
    """
    将任意音频转码为 16kHz 单声道 WAV，并返回输出路径。

    输出文件位于系统临时目录，调用方在使用完成后负责清理。
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Input file does not exist: {audio_path}")

    # 截断文件名前缀：Windows MAX_PATH 260，长文件名叠加 Temp 目录可能溢出
    base_name = Path(audio_path).stem[:32]
    fd, output_path = tempfile.mkstemp(prefix=f"{base_name}_hbr16khz_", suffix=".wav")
    os.close(fd)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    if platform.system() == "Windows":
        ffmpeg_filename = "ffmpeg.exe"
    else:
        ffmpeg_filename = "ffmpeg"
    ffmpeg_path = os.path.join(script_dir, "lib", ffmpeg_filename)

    if not os.path.isfile(ffmpeg_path):
        raise FileNotFoundError(
            f"'ffmpeg' executable not found: {ffmpeg_path}. "
            f"Please ensure the file exists and is executable."
        )

    if platform.system() != "Windows" and not os.access(ffmpeg_path, os.X_OK):
        try:
            os.chmod(ffmpeg_path, 0o755)
        except OSError as exc:
            raise PermissionError(
                f"Failed to make FFmpeg executable at {ffmpeg_path}. "
                f"Please run manually: chmod +x {ffmpeg_path}"
            ) from exc

    command = [
        ffmpeg_path,
        "-i", audio_path,
        "-max_muxing_queue_size", "1024",
        "-buffer_size", "4096K",
        "-threads", str(os.cpu_count() or 2),
        "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path,
    ]

    try:
        subprocess.run(command, check=True, timeout=1800, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise RuntimeError(f"FFmpeg failed: {stderr}") from exc

    return output_path
