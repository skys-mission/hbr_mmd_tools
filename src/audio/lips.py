# -*- coding: utf-8 -*-
# Copyright (c) 2024, https://github.com/skys-mission and Half-Bottled Reverie
"""
Lip sync generation.
"""
import os

from ..audio.ffmpeg import convert_to_wav_16000
from ..audio.rosa import rosa
from ..audio.viseme_curve import build_viseme_keyframes


class Lips:  # pylint: disable=too-few-public-methods
    """Lip sync generator."""

    @staticmethod
    def mmd_lips_gen(wav_path, buffer=0.05, approach_speed=3.0,
                     # pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
                     db_threshold=-50, rms_threshold=0.01, max_morph_value=1.0, start_frame=1,
                     fps=24, anticipation_scale=1.0):
        """Generate sparse viseme keyframes from an input audio file."""
        wav_path_16 = convert_to_wav_16000(wav_path)
        try:
            viseme_samples = rosa(
                wav_path_16,
                db_threshold=db_threshold,
                rms_threshold=rms_threshold,
            )
        finally:
            # 转码产物用完即删，避免在系统临时目录堆积
            try:
                os.remove(wav_path_16)
            except OSError:
                pass
        return build_viseme_keyframes(
            viseme_samples,
            start_frame=start_frame,
            fps=fps,
            max_morph_value=max_morph_value,
            buffer=buffer,
            approach_speed=approach_speed,
            anticipation_scale=anticipation_scale,
        )
