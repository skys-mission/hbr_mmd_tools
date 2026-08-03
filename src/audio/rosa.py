# -*- coding: utf-8 -*-
# Copyright (c) 2024, https://github.com/skys-mission and Half-Bottled Reverie
"""
Audio analysis for lip sync generation.

仅使用 Python 标准库实现：WAV 解码、分帧、Hann 窗、功率谱（FFT）
与共振峰估计，不再依赖 librosa / numpy。
"""
import array
import heapq
import math
import os
import sys
import wave

from ..util.logger import Log
from .viseme_curve import compute_openness, score_visemes, zero_weights


FRAME_LENGTH = 1024
HOP_LENGTH = 160

_FFT_PLANS = {}
_WINDOW_CACHE = {}


def load_audio(file_path):
    """读取 PCM WAV 音频，返回 (归一化到 [-1, 1] 的采样列表, 采样率)。"""
    with wave.open(file_path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        raw_data = wav_file.readframes(wav_file.getnframes())

    samples = _decode_pcm_samples(raw_data, sample_width)
    if channels > 1:
        samples = _downmix_to_mono(samples, channels)
    return samples, sample_rate


def _decode_pcm_samples(raw_data, sample_width):
    """将小端 PCM 字节流解码为 [-1.0, 1.0] 范围的浮点采样列表。"""
    if sample_width == 1:
        return [(byte - 128) / 128.0 for byte in raw_data]
    if sample_width == 2:
        unpacked = array.array("h")
        unpacked.frombytes(raw_data)
        if sys.byteorder != "little":
            unpacked.byteswap()
        return [value / 32768.0 for value in unpacked]
    if sample_width == 3:
        return [
            int.from_bytes(raw_data[offset:offset + 3], "little", signed=True) / 8388608.0
            for offset in range(0, len(raw_data), 3)
        ]
    if sample_width == 4:
        unpacked = array.array("i")
        unpacked.frombytes(raw_data)
        if sys.byteorder != "little":
            unpacked.byteswap()
        return [value / 2147483648.0 for value in unpacked]
    raise ValueError(f"Unsupported PCM sample width: {sample_width}")


def _downmix_to_mono(samples, channels):
    """将交错的多声道采样混缩为单声道。"""
    return [
        sum(samples[offset:offset + channels]) / channels
        for offset in range(0, len(samples), channels)
    ]


def frame_signal(samples, frame_length, hop_length):
    """将采样序列切分为固定长度的重叠帧，尾部不足一帧的采样被丢弃。"""
    if len(samples) < frame_length:
        samples = samples + [0.0] * (frame_length - len(samples))
    frame_count = 1 + (len(samples) - frame_length) // hop_length
    return [
        samples[start:start + frame_length]
        for start in range(0, frame_count * hop_length, hop_length)
    ]


def _hann_window(size):
    """生成并缓存与 numpy.hanning 一致的对称 Hann 窗。"""
    window = _WINDOW_CACHE.get(size)
    if window is None:
        if size <= 1:
            window = [1.0] * size
        else:
            denominator = float(size - 1)
            window = [
                0.5 - 0.5 * math.cos(2.0 * math.pi * index / denominator)
                for index in range(size)
            ]
        _WINDOW_CACHE[size] = window
    return window


def _get_fft_plan(size):
    """构建并缓存指定大小的位反转表与各阶段旋转因子表。"""
    plan = _FFT_PLANS.get(size)
    if plan is not None:
        return plan

    if size < 2 or size & (size - 1):
        raise ValueError(f"FFT size must be a power of 2, got {size}")

    bits = size.bit_length() - 1
    bit_reversed = []
    for index in range(size):
        reversed_index = 0
        value = index
        for _ in range(bits):
            reversed_index = (reversed_index << 1) | (value & 1)
            value >>= 1
        bit_reversed.append(reversed_index)

    twiddle_stages = []
    length = 2
    while length <= size:
        half = length >> 1
        angle_step = -math.pi / half
        twiddle_stages.append([
            complex(math.cos(angle_step * k), math.sin(angle_step * k))
            for k in range(half)
        ])
        length <<= 1

    plan = (bit_reversed, twiddle_stages)
    _FFT_PLANS[size] = plan
    return plan


def fft_power_spectrum(samples):
    """计算实数序列 rfft 结果的模平方（功率谱），长度为 size // 2 + 1。"""
    size = len(samples)
    bit_reversed, twiddle_stages = _get_fft_plan(size)

    data = [complex(samples[index]) for index in bit_reversed]

    length = 2
    for twiddles in twiddle_stages:
        half = length >> 1
        for start in range(0, size, length):
            even_index = start
            odd_index = start + half
            for twiddle in twiddles:
                odd_value = data[odd_index] * twiddle
                even_value = data[even_index]
                data[even_index] = even_value + odd_value
                data[odd_index] = even_value - odd_value
                even_index += 1
                odd_index += 1
        length <<= 1

    return [
        value.real * value.real + value.imag * value.imag
        for value in data[:(size >> 1) + 1]
    ]


def _estimate_formants(frame, sr):
    """基于功率谱峰值估计第一、第二共振峰频率。"""
    size = len(frame)
    spectrum = fft_power_spectrum(frame)
    bin_hz = float(sr) / size

    low_bin = max(1, math.ceil(180.0 / bin_hz))
    high_bin = min(size >> 1, math.floor(3200.0 / bin_hz))
    if low_bin > high_bin:
        return None, None

    peak_count = min(12, high_bin - low_bin + 1)
    ranked_indexes = heapq.nlargest(
        peak_count,
        range(low_bin, high_bin + 1),
        key=lambda index: spectrum[index],
    )

    f1 = None
    f2 = None
    for index in ranked_indexes:
        frequency = index * bin_hz
        if f1 is None and 180.0 <= frequency <= 1100.0:
            f1 = frequency
            continue
        if f1 is not None and frequency >= max(700.0, f1 + 120.0):
            f2 = frequency
            break

    if f1 is not None and f2 is not None:
        return f1, f2

    fallback_freqs = sorted(index * bin_hz for index in ranked_indexes[:2])
    if len(fallback_freqs) == 2:
        return fallback_freqs[0], fallback_freqs[1]
    return None, None


def rosa(audio_path, db_threshold=-50, rms_threshold=0.01):  # pylint: disable=too-many-locals
    """对 16kHz 单声道 PCM WAV 计算 viseme 时间序列样本。

    调用方须保证输入为 16kHz 单声道 WAV（共振峰频率阈值按此调参，
    lips.py 经 ffmpeg 转码满足该契约）；分析完成后删除 audio_path 临时文件。
    """
    y, sr = load_audio(audio_path)
    frames = frame_signal(y, FRAME_LENGTH, HOP_LENGTH)
    window = _hann_window(FRAME_LENGTH)

    results = []
    for index, frame in enumerate(frames):
        windowed = [sample * weight for sample, weight in zip(frame, window)]
        frame_rms = math.sqrt(sum(value * value for value in windowed) / FRAME_LENGTH)
        frame_db = 20.0 * math.log10(frame_rms + 1e-10)
        openness = compute_openness(frame_db, frame_rms, db_threshold, rms_threshold)
        timestamp = round(((index * HOP_LENGTH) + (FRAME_LENGTH / 2.0)) / sr, 4)

        weights = zero_weights()
        if openness > 1e-3:
            f1, f2 = _estimate_formants(windowed, sr)
            weights = score_visemes(f1, f2)

        results.append({
            "time": timestamp,
            "openness": round(openness, 4),
            "weights": weights,
        })

    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except OSError as exc:
            Log.warning(f"Failed to remove temp audio file {audio_path}: {exc}")
    return results
