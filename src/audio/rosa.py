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
import statistics
import sys
import wave

from ..util.logger import Log
from .viseme_curve import compute_openness, gate_viseme_weights, score_visemes, zero_weights


FRAME_LENGTH = 1024
HOP_LENGTH = 160

# 挑峰前对功率谱做滑动平均的半径（bin），抑制谐波毛刺
_SPECTRUM_SMOOTH_RADIUS = 2
# 置信度：最强平滑峰与频段中位功率之比映射到 [0, 1]
_CONFIDENCE_RATIO_MIN = 4.0
_CONFIDENCE_RATIO_MAX = 40.0

_FFT_PLANS = {}
_WINDOW_CACHE = {}


def load_audio(file_path):
    """读取 PCM WAV 音频，返回 (归一化到 [-1, 1] 的 array('d') 采样序列, 采样率)。"""
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
    """将小端 PCM 字节流解码为 [-1.0, 1.0] 范围的 array('d') 采样序列。

    采样以 double 紧凑存储（8 字节/采样），避免百万级 Python float
    对象带来的内存膨胀；除以 2 的幂为精确缩放，数值与此前列表实现一致。
    """
    if sample_width == 1:
        return array.array("d", ((byte - 128) / 128.0 for byte in raw_data))
    if sample_width not in (2, 3, 4):
        raise ValueError(f"Unsupported PCM sample width: {sample_width}")

    scale = 1.0 / (1 << (sample_width * 8 - 1))
    # 16/32-bit 走定宽整数数组快速解包（itemsize 与平台相关，不满足时回退通用路径）
    typecode = {2: "h", 4: "i"}.get(sample_width)
    if typecode is not None and array.array(typecode).itemsize == sample_width:
        unpacked = array.array(typecode)
        unpacked.frombytes(raw_data)
        if sys.byteorder != "little":
            unpacked.byteswap()
        return array.array("d", (value * scale for value in unpacked))

    return array.array("d", (
        int.from_bytes(raw_data[offset:offset + sample_width], "little", signed=True) * scale
        for offset in range(0, len(raw_data), sample_width)
    ))


def _downmix_to_mono(samples, channels):
    """将交错的多声道采样混缩为单声道。"""
    return array.array("d", (
        sum(samples[offset:offset + channels]) / channels
        for offset in range(0, len(samples), channels)
    ))


def frame_signal(samples, frame_length, hop_length):
    """惰性生成固定长度的重叠帧，尾部不足一帧的采样被丢弃。

    逐帧 yield 切片而非物化全部帧（重叠分帧会放大数倍引用），
    调用方顺序消费时内存占用与帧数无关。
    """
    if len(samples) < frame_length:
        samples = list(samples)
        samples.extend([0.0] * (frame_length - len(samples)))
    frame_count = 1 + (len(samples) - frame_length) // hop_length
    for start in range(0, frame_count * hop_length, hop_length):
        yield samples[start:start + frame_length]


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


def _fft_complex(values):
    """迭代 radix-2 复数 FFT，返回与输入等长的变换结果。"""
    size = len(values)
    bit_reversed, twiddle_stages = _get_fft_plan(size)

    data = [complex(values[index]) for index in bit_reversed]

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

    return data


def fft_power_spectrum(samples):
    """计算实数序列 rfft 结果的模平方（功率谱），长度为 size // 2 + 1。

    实数输入按奇偶打包成半长复数序列，做 half-size FFT 后分裂重建
    （X[k] = (Z[k] + conj(Z[N/2-k]))/2 - j·W^k·(Z[k] - conj(Z[N/2-k]))/2），
    蝶形运算量约为直接全复数 FFT 的一半。
    """
    size = len(samples)
    if size < 2 or size & (size - 1):
        raise ValueError(f"FFT size must be a power of 2, got {size}")

    half = size >> 1
    packed = [
        complex(samples[2 * index], samples[2 * index + 1])
        for index in range(half)
    ]
    transformed = packed if half == 1 else _fft_complex(packed)

    spectrum = [0.0] * (half + 1)
    zero_bin = transformed[0]
    dc_value = zero_bin.real + zero_bin.imag
    nyquist_value = zero_bin.real - zero_bin.imag
    spectrum[0] = dc_value * dc_value
    spectrum[half] = nyquist_value * nyquist_value

    step = complex(math.cos(2.0 * math.pi / size), -math.sin(2.0 * math.pi / size))
    twiddle = step
    for index in range(1, half):
        mirrored = transformed[half - index].conjugate()
        difference = transformed[index] - mirrored
        value = 0.5 * (transformed[index] + mirrored) - 0.5j * twiddle * difference
        spectrum[index] = value.real * value.real + value.imag * value.imag
        twiddle *= step

    return spectrum


def _smooth_spectrum_band(spectrum, low_bin, high_bin, radius=_SPECTRUM_SMOOTH_RADIUS):
    """对分析频段做滑动平均，返回与 [low_bin, high_bin] 对齐的平滑功率列表。"""
    last_bin = len(spectrum) - 1
    smoothed = []
    for index in range(low_bin, high_bin + 1):
        start = max(0, index - radius)
        end = min(last_bin, index + radius)
        total = 0.0
        for cursor in range(start, end + 1):
            total += spectrum[cursor]
        smoothed.append(total / (end - start + 1))
    return smoothed


def _estimate_confidence(smoothed, ranked_indexes, low_bin):
    """由最强平滑峰与频段中位功率之比估计共振峰置信度。

    浊音的谐波峰远高于频段中位水平（比值通常 >100），清音/噪声的
    谱峰平缓（比值个位数），比值越低说明挑出的峰越不可信。
    """
    median = statistics.median(smoothed)
    if median <= 1e-20:
        return 0.0
    strongest = smoothed[ranked_indexes[0] - low_bin]
    ratio = strongest / median
    span = _CONFIDENCE_RATIO_MAX - _CONFIDENCE_RATIO_MIN
    return max(0.0, min(1.0, (ratio - _CONFIDENCE_RATIO_MIN) / span))


def _pick_formants(ranked_indexes, bin_hz):
    """从按强度排序的候选峰中选出 F1/F2，约束不满足时回退到最强两峰。"""
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


def _estimate_formants(frame, sr):
    """基于功率谱峰值估计第一、第二共振峰频率，返回 (f1, f2, 置信度)。

    挑峰前先做小窗滑动平均并只取局部极大值，抑制周期图谐波毛刺
    导致的共振峰跳变；置信度反映峰值的突出程度，供调用方门控。
    """
    size = len(frame)
    spectrum = fft_power_spectrum(frame)
    bin_hz = float(sr) / size

    low_bin = max(1, math.ceil(180.0 / bin_hz))
    high_bin = min(size >> 1, math.floor(3200.0 / bin_hz))
    if low_bin > high_bin:
        return None, None, 0.0

    smoothed = _smooth_spectrum_band(spectrum, low_bin, high_bin)
    candidates = [
        low_bin + offset
        for offset in range(1, len(smoothed) - 1)
        if smoothed[offset] >= smoothed[offset - 1]
        and smoothed[offset] >= smoothed[offset + 1]
    ]
    if not candidates:
        candidates = list(range(low_bin, high_bin + 1))

    peak_count = min(12, len(candidates))
    ranked_indexes = heapq.nlargest(
        peak_count,
        candidates,
        key=lambda index: smoothed[index - low_bin],
    )
    confidence = _estimate_confidence(smoothed, ranked_indexes, low_bin)
    f1, f2 = _pick_formants(ranked_indexes, bin_hz)
    return f1, f2, confidence


def rosa(audio_path, db_threshold=-50, rms_threshold=0.01):  # pylint: disable=too-many-locals
    """对 16kHz 单声道 PCM WAV 计算 viseme 时间序列样本。

    调用方须保证输入为 16kHz 单声道 WAV（共振峰频率阈值按此调参，
    lips.py 经 ffmpeg 转码满足该契约）；分析完成后删除 audio_path 临时文件。
    """
    y, sr = load_audio(audio_path)
    frames = frame_signal(y, FRAME_LENGTH, HOP_LENGTH)
    window = _hann_window(FRAME_LENGTH)

    results = []
    previous_weights = zero_weights()
    for index, frame in enumerate(frames):
        windowed = [sample * weight for sample, weight in zip(frame, window)]
        frame_rms = math.sqrt(sum(value * value for value in windowed) / FRAME_LENGTH)
        frame_db = 20.0 * math.log10(frame_rms + 1e-10)
        openness = compute_openness(frame_db, frame_rms, db_threshold, rms_threshold)
        timestamp = round(((index * HOP_LENGTH) + (FRAME_LENGTH / 2.0)) / sr, 4)

        weights = zero_weights()
        if openness > 1e-3:
            f1, f2, confidence = _estimate_formants(windowed, sr)
            # 低置信帧（清辅音/噪声）向上一帧分布靠拢，保持嘴型连续
            weights = gate_viseme_weights(score_visemes(f1, f2), confidence, previous_weights)
        if sum(weights.values()) > 1e-4:
            previous_weights = weights

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
