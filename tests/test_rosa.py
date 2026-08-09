# -*- coding: utf-8 -*-
"""Tests for the pure-standard-library audio analysis module."""
import math
import os
import random
import struct
import tempfile
import unittest
import wave

from src.audio.rosa import (  # pylint: disable=import-error,protected-access
    FRAME_LENGTH,
    _decode_pcm_samples,
    _estimate_formants,
    _hann_window,
    fft_power_spectrum,
    frame_signal,
    load_audio,
    rosa,
)
from src.audio.viseme_curve import CANONICAL_VISEMES  # pylint: disable=import-error


def _write_wav(file_path, samples, sample_rate=16000, channels=1):
    """Write 16-bit PCM samples (already interleaved) to a WAV file."""
    # pylint: disable=no-member
    with wave.open(file_path, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _naive_dft_power(samples):
    """Reference O(N^2) DFT power spectrum for validation."""
    size = len(samples)
    result = []
    for k in range(size // 2 + 1):
        real = 0.0
        imag = 0.0
        for t, value in enumerate(samples):
            angle = -2.0 * math.pi * k * t / size
            real += value * math.cos(angle)
            imag += value * math.sin(angle)
        result.append(real * real + imag * imag)
    return result


class LoadAudioTests(unittest.TestCase):
    """Tests for WAV decoding."""

    def setUp(self):
        self._temp_paths = []

    def tearDown(self):
        for path in self._temp_paths:
            if os.path.exists(path):
                os.remove(path)

    def _make_temp_wav(self, samples, sample_rate=16000, channels=1):
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        _write_wav(path, samples, sample_rate, channels)
        self._temp_paths.append(path)
        return path

    def test_load_audio_normalizes_pcm16_mono(self):
        """16-bit mono samples should be normalized to [-1, 1]."""
        raw = [0, 16384, -16384, 32767, -32768]
        path = self._make_temp_wav(raw, sample_rate=22050)
        samples, sample_rate = load_audio(path)
        self.assertEqual(sample_rate, 22050)
        self.assertEqual(len(samples), 5)
        self.assertAlmostEqual(samples[0], 0.0, places=6)
        self.assertAlmostEqual(samples[1], 0.5, places=4)
        self.assertAlmostEqual(samples[2], -0.5, places=4)
        self.assertAlmostEqual(samples[3], 32767 / 32768.0, places=6)
        self.assertAlmostEqual(samples[4], -1.0, places=6)

    def test_load_audio_downmixes_stereo(self):
        """Interleaved stereo input should be averaged to mono."""
        interleaved = [16384, 0, 16384, 0]
        path = self._make_temp_wav(interleaved, channels=2)
        samples, sample_rate = load_audio(path)
        self.assertEqual(sample_rate, 16000)
        self.assertEqual(len(samples), 2)
        self.assertAlmostEqual(samples[0], 0.25, places=4)
        self.assertAlmostEqual(samples[1], 0.25, places=4)

    def test_decode_rejects_unsupported_sample_width(self):
        """Unsupported PCM widths should raise a clear error."""
        with self.assertRaises(ValueError):
            _decode_pcm_samples(b"\x00\x00\x00\x00\x00", 5)


class FramingAndWindowTests(unittest.TestCase):
    """Tests for framing and the Hann window."""

    def test_frame_signal_produces_overlapping_frames(self):
        """Frame count and content should match librosa.util.frame semantics."""
        samples = [float(value) for value in range(8)]
        frames = list(frame_signal(samples, frame_length=4, hop_length=2))
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(frames[1], [2.0, 3.0, 4.0, 5.0])
        self.assertEqual(frames[2], [4.0, 5.0, 6.0, 7.0])

    def test_frame_signal_pads_short_input(self):
        """Inputs shorter than one frame should be zero-padded."""
        frames = list(frame_signal([1.0, 2.0], frame_length=4, hop_length=2))
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0], [1.0, 2.0, 0.0, 0.0])

    def test_hann_window_matches_reference(self):
        """The window should match numpy.hanning (symmetric Hann)."""
        size = 32
        window = _hann_window(size)
        self.assertEqual(len(window), size)
        for index, value in enumerate(window):
            expected = 0.5 - 0.5 * math.cos(2.0 * math.pi * index / (size - 1))
            self.assertAlmostEqual(value, expected, places=12)
        self.assertAlmostEqual(window[0], 0.0, places=12)
        self.assertAlmostEqual(window[-1], 0.0, places=12)


class FftTests(unittest.TestCase):
    """Tests for the pure-Python FFT."""

    def test_fft_matches_naive_dft(self):
        """FFT power spectrum should match a naive DFT reference."""
        rng = random.Random(42)
        samples = [rng.uniform(-1.0, 1.0) for _ in range(64)]
        actual = fft_power_spectrum(samples)
        expected = _naive_dft_power(samples)
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            tolerance = 1e-6 * max(1.0, expected_value)
            self.assertAlmostEqual(actual_value, expected_value, delta=tolerance)

    def test_fft_peak_tracks_sine_bin(self):
        """A pure sine centered on a bin should peak at that bin."""
        size = FRAME_LENGTH
        target_bin = 50
        samples = [math.sin(2.0 * math.pi * target_bin * n / size) for n in range(size)]
        spectrum = fft_power_spectrum(samples)
        peak_bin = max(range(len(spectrum)), key=lambda index: spectrum[index])
        self.assertEqual(peak_bin, target_bin)

    def test_fft_requires_power_of_two(self):
        """Non power-of-two sizes should raise an error."""
        with self.assertRaises(ValueError):
            fft_power_spectrum([0.0] * 3)


class FormantTests(unittest.TestCase):
    """Tests for formant estimation."""

    def test_estimate_formants_two_tone(self):
        """A 500 Hz + 1500 Hz mix should resolve to those formants."""
        window = _hann_window(FRAME_LENGTH)
        frame = [
            window[n] * (
                math.sin(2.0 * math.pi * 500.0 * n / 16000.0)
                + math.sin(2.0 * math.pi * 1500.0 * n / 16000.0)
            )
            for n in range(FRAME_LENGTH)
        ]
        f1, f2, confidence = _estimate_formants(frame, 16000)
        self.assertAlmostEqual(f1, 500.0, delta=16.0)
        self.assertAlmostEqual(f2, 1500.0, delta=16.0)
        self.assertGreater(confidence, 0.5)

    def test_estimate_formants_returns_none_when_band_empty(self):
        """Sample rates too low to cover 180-3200 Hz should yield None."""
        frame = [0.0] * FRAME_LENGTH
        f1, f2, confidence = _estimate_formants(frame, 200)
        self.assertIsNone(f1)
        self.assertIsNone(f2)
        self.assertEqual(confidence, 0.0)

    def test_estimate_formants_confidence_distinguishes_noise(self):
        """White noise should score much lower confidence than a vowel-like tone."""
        window = _hann_window(FRAME_LENGTH)
        rng = random.Random(7)
        voiced = [
            window[n] * (
                math.sin(2.0 * math.pi * 700.0 * n / 16000.0)
                + 0.6 * math.sin(2.0 * math.pi * 1200.0 * n / 16000.0)
            )
            for n in range(FRAME_LENGTH)
        ]
        noise = [window[n] * rng.uniform(-1.0, 1.0) for n in range(FRAME_LENGTH)]

        _, _, voiced_confidence = _estimate_formants(voiced, 16000)
        _, _, noise_confidence = _estimate_formants(noise, 16000)

        self.assertGreater(voiced_confidence, 0.5)
        self.assertLess(noise_confidence, voiced_confidence)
        self.assertLess(noise_confidence, 0.5)


class RosaEndToEndTests(unittest.TestCase):
    """End-to-end tests for the rosa pipeline."""

    def test_rosa_generates_viseme_samples_and_cleans_up(self):
        """Silence should stay closed, tone should open, temp file removed."""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        tone_start = 2000
        total = 8000
        amplitude = int(0.6 * 32767)
        samples = []
        for n in range(total):
            if n < tone_start:
                samples.append(0)
            else:
                value = amplitude * math.sin(2.0 * math.pi * 500.0 * n / 16000.0)
                samples.append(int(value))
        _write_wav(path, samples)

        results = rosa(path)

        self.assertFalse(os.path.exists(path))
        expected_frames = 1 + (total - FRAME_LENGTH) // 160
        self.assertEqual(len(results), expected_frames)

        for sample in results[:6]:
            self.assertEqual(sample["openness"], 0.0)
            for viseme in CANONICAL_VISEMES:
                self.assertEqual(sample["weights"][viseme], 0.0)

        active = results[25:40]
        self.assertTrue(active)
        for sample in active:
            self.assertGreater(sample["openness"], 0.0)
            self.assertGreater(sum(sample["weights"].values()), 0.0)
            self.assertEqual(set(sample["weights"]), set(CANONICAL_VISEMES))

        times = [sample["time"] for sample in results]
        self.assertEqual(times, sorted(times))

    def test_rosa_holds_viseme_through_unvoiced_noise(self):
        """低置信噪声段应保持前一浊音段的口型分布，而非随机指派。"""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        rng = random.Random(11)
        amplitude = int(0.6 * 32767)
        samples = []
        for n in range(12000):
            if n < 2000:
                samples.append(0)
            elif n < 6000:
                samples.append(int(amplitude * math.sin(2.0 * math.pi * 500.0 * n / 16000.0)))
            else:
                samples.append(int(0.6 * amplitude * rng.uniform(-1.0, 1.0)))
        _write_wav(path, samples)

        results = rosa(path)

        tone_dominant = max(CANONICAL_VISEMES, key=lambda v: results[22]["weights"][v])
        for sample in results[40:50]:
            # 噪声帧能量足够，openness 仍大于 0
            self.assertGreater(sample["openness"], 0.0)
            self.assertGreater(sum(sample["weights"].values()), 0.5)
            dominant = max(CANONICAL_VISEMES, key=lambda v, s=sample: s["weights"][v])
            self.assertEqual(dominant, tone_dominant)


if __name__ == "__main__":
    unittest.main()
