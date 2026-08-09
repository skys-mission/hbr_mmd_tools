# -*- coding: utf-8 -*-
"""Tests for viseme curve helpers."""
import unittest

from src.audio.viseme_curve import (  # pylint: disable=import-error
    build_viseme_keyframes,
    compute_openness,
    gate_viseme_weights,
    score_visemes,
)


def _weights(**overrides):
    weights = {"a": 0.0, "i": 0.0, "u": 0.0, "e": 0.0, "o": 0.0, "n": 0.0}
    weights.update(overrides)
    return weights


class VisemeCurveTests(unittest.TestCase):
    """Regression tests for viseme curve generation."""

    def test_compute_openness_grows_with_energy(self):
        """Openness should increase with stronger audio energy."""
        quiet = compute_openness(-55.0, 0.01, -50.0, 0.05)
        loud = compute_openness(-18.0, 0.20, -50.0, 0.05)
        self.assertLess(quiet, loud)
        self.assertGreaterEqual(loud, 0.0)
        self.assertLessEqual(loud, 1.0)

    def test_score_visemes_prefers_matching_formant_prototype(self):
        """Formant prototypes should map to the expected dominant viseme."""
        a_weights = score_visemes(850.0, 1450.0)
        i_weights = score_visemes(320.0, 2250.0)
        self.assertEqual(max(a_weights, key=a_weights.get), "a")
        self.assertEqual(max(i_weights, key=i_weights.get), "i")

    def test_build_viseme_keyframes_keeps_soft_transition(self):
        """Keyframes should preserve a smooth transition between visemes."""
        samples = [
            {"time": 0.0, "openness": 0.0, "weights": _weights()},
            {"time": 0.04, "openness": 0.8, "weights": _weights(a=1.0)},
            {"time": 0.08, "openness": 0.85, "weights": _weights(a=0.2, i=0.8)},
            {"time": 0.12, "openness": 0.0, "weights": _weights()},
        ]

        keyframes = build_viseme_keyframes(samples, start_frame=1, fps=24, max_morph_value=1.0)
        a_values = [point for point in keyframes["a"] if point["value"] > 0.0]
        i_values = [point for point in keyframes["i"] if point["value"] > 0.0]

        self.assertTrue(a_values)
        self.assertTrue(i_values)
        self.assertLessEqual(i_values[0]["frame"], 2.92)
        self.assertEqual(keyframes["a"][0]["value"], 0.0)
        self.assertEqual(keyframes["i"][0]["value"], 0.0)

    def test_gate_viseme_weights_full_confidence_takes_new(self):
        """confidence=1 时应完全采用新分布。"""
        gated = gate_viseme_weights(_weights(a=1.0), 1.0, _weights(i=1.0))
        self.assertEqual(gated["a"], 1.0)
        self.assertEqual(gated["i"], 0.0)

    def test_gate_viseme_weights_low_confidence_holds_previous(self):
        """低置信时应向上一帧分布靠拢，confidence=0 时完全保持。"""
        new = _weights(a=1.0)
        previous = _weights(i=1.0)
        gated = gate_viseme_weights(new, 0.0, previous)
        self.assertEqual(gated["i"], 1.0)
        self.assertEqual(gated["a"], 0.0)

        partial = gate_viseme_weights(new, 0.25, previous)
        self.assertAlmostEqual(partial["a"], 0.25, places=6)
        self.assertAlmostEqual(partial["i"], 0.75, places=6)

    def test_gate_viseme_weights_clamps_out_of_range_confidence(self):
        """超出 [0, 1] 的置信度应被截断而不是产生负权重。"""
        new = _weights(a=1.0)
        previous = _weights(i=1.0)
        self.assertEqual(gate_viseme_weights(new, 5.0, previous)["a"], 1.0)
        self.assertEqual(gate_viseme_weights(new, -1.0, previous)["i"], 1.0)


if __name__ == "__main__":
    unittest.main()
