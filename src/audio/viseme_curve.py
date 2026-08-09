# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
Viseme curve generation helpers.
"""
import math


CANONICAL_VISEMES = ("a", "i", "u", "e", "o", "n")
FORMANT_PROTOTYPES = {
    "a": {"f1": 850.0, "f2": 1450.0, "spread_f1": 220.0, "spread_f2": 320.0},
    "i": {"f1": 320.0, "f2": 2250.0, "spread_f1": 150.0, "spread_f2": 420.0},
    "u": {"f1": 360.0, "f2": 900.0, "spread_f1": 160.0, "spread_f2": 220.0},
    "e": {"f1": 530.0, "f2": 1850.0, "spread_f1": 170.0, "spread_f2": 360.0},
    "o": {"f1": 500.0, "f2": 980.0, "spread_f1": 180.0, "spread_f2": 200.0},
    "n": {"f1": 280.0, "f2": 1350.0, "spread_f1": 130.0, "spread_f2": 240.0},
}


def clamp(value, min_value=0.0, max_value=1.0):
    """Clamp a numeric value to the provided range."""
    return max(min_value, min(max_value, value))


def zero_weights():
    """Return a zero-filled viseme weight dictionary."""
    return {viseme: 0.0 for viseme in CANONICAL_VISEMES}


def normalize_weights(weights):
    """Normalize a viseme weight dictionary."""
    total = sum(max(0.0, value) for value in weights.values())
    if total <= 1e-8:
        return zero_weights()
    return {
        viseme: max(0.0, weights.get(viseme, 0.0)) / total
        for viseme in CANONICAL_VISEMES
    }


def compute_openness(frame_db, frame_rms, db_threshold, rms_threshold):
    """Convert energy metrics to a normalized mouth openness value."""
    db_span = max(12.0, abs(float(db_threshold)))
    db_component = clamp((frame_db - float(db_threshold)) / db_span)

    rms_floor = max(float(rms_threshold), 1e-4)
    rms_span = max(rms_floor * 6.0, 0.05)
    rms_component = clamp((frame_rms - rms_floor) / rms_span)

    openness = (db_component * 0.4) + (math.sqrt(rms_component) * 0.6)
    return clamp(openness)


def score_visemes(f1, f2):
    """Estimate continuous viseme weights from formant candidates."""
    if f1 is None or f2 is None:
        return zero_weights()

    weights = {}
    for viseme, prototype in FORMANT_PROTOTYPES.items():
        f1_delta = (f1 - prototype["f1"]) / prototype["spread_f1"]
        f2_delta = (f2 - prototype["f2"]) / prototype["spread_f2"]
        weights[viseme] = math.exp(-0.5 * ((f1_delta * f1_delta) + (f2_delta * f2_delta)))

    if f1 > 750.0:
        weights["a"] *= 1.15
    if f2 > 2050.0:
        weights["i"] *= 1.1
    if f2 < 950.0:
        weights["u"] *= 1.05
        weights["o"] *= 1.05

    return normalize_weights(weights)


def gate_viseme_weights(new_weights, confidence, previous_weights):
    """按估计置信度在新旧分布间插值。

    共振峰估计在清辅音/噪声帧上不可靠，低置信时向上一帧分布靠拢，
    避免嘴型在辅音段随机跳动；confidence >= 1 时完全采用新分布。
    """
    blend = clamp(confidence)
    if blend >= 1.0:
        return {
            viseme: max(0.0, new_weights.get(viseme, 0.0))
            for viseme in CANONICAL_VISEMES
        }
    return {
        viseme: (
            blend * max(0.0, new_weights.get(viseme, 0.0))
            + (1.0 - blend) * max(0.0, previous_weights.get(viseme, 0.0))
        )
        for viseme in CANONICAL_VISEMES
    }


def apply_temporal_smoothing(
    samples,
    anticipation=0.22,
    attack=0.65,
    release=0.35,
    contrast=1.2,
):  # pylint: disable=too-many-locals
    """Smooth viseme weights over time and add look-ahead coarticulation."""
    if not samples:
        return []

    anticipated = []
    for index, sample in enumerate(samples):
        blended = zero_weights()
        for viseme in CANONICAL_VISEMES:
            current = sample["weights"].get(viseme, 0.0)
            next_one = 0.0
            next_two = 0.0
            if index + 1 < len(samples):
                next_one = samples[index + 1]["weights"].get(viseme, 0.0)
            if index + 2 < len(samples):
                next_two = samples[index + 2]["weights"].get(viseme, 0.0)
            blended[viseme] = current + (next_one * anticipation) + (next_two * anticipation * 0.35)

        blended = normalize_weights(blended)
        if contrast != 1.0:
            blended = normalize_weights({
                viseme: value ** contrast
                for viseme, value in blended.items()
            })

        anticipated.append({
            "time": sample["time"],
            "openness": sample["openness"],
            "weights": blended,
        })

    smoothed = []
    state = zero_weights()
    previous_openness = 0.0
    for sample in anticipated:
        target_openness = sample["openness"]
        openness_alpha = 0.55 if target_openness > previous_openness else 0.30
        openness = previous_openness + ((target_openness - previous_openness) * openness_alpha)
        previous_openness = openness

        current_weights = {}
        for viseme in CANONICAL_VISEMES:
            target_value = sample["weights"].get(viseme, 0.0) * openness
            previous_value = state[viseme]
            alpha = attack if target_value > previous_value else release
            current_value = previous_value + ((target_value - previous_value) * alpha)
            state[viseme] = current_value
            current_weights[viseme] = current_value

        capped_weights = cap_total_weight(current_weights, openness)
        state.update(capped_weights)
        smoothed.append({
            "time": sample["time"],
            "weights": capped_weights,
        })

    return smoothed


def cap_total_weight(weights, limit):
    """Cap the accumulated viseme weight to the current openness envelope."""
    normalized_limit = max(0.0, float(limit))
    if normalized_limit <= 1e-8:
        return zero_weights()

    total = sum(max(0.0, value) for value in weights.values())
    if total <= normalized_limit:
        return {viseme: clamp(weights.get(viseme, 0.0)) for viseme in CANONICAL_VISEMES}

    scale = normalized_limit / total
    return {
        viseme: clamp(max(0.0, weights.get(viseme, 0.0)) * scale)
        for viseme in CANONICAL_VISEMES
    }


def build_viseme_keyframes(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    samples,
    start_frame=1,
    fps=24,
    max_morph_value=1.0,
    buffer=0.05,
    approach_speed=3.0,
    anticipation_scale=1.0,
):
    """Convert frame-wise viseme samples into sparse animation keyframes."""
    if not samples:
        return {viseme: _build_empty_track(start_frame) for viseme in CANONICAL_VISEMES}

    anticipation, attack, release, contrast = _derive_smoothing_params(
        buffer,
        approach_speed,
        anticipation_scale,
    )
    smoothed = apply_temporal_smoothing(
        samples,
        anticipation=anticipation,
        attack=attack,
        release=release,
        contrast=contrast,
    )
    smoothed = _append_release_tail(smoothed)

    result = {}
    for viseme in CANONICAL_VISEMES:
        track = []
        for sample in smoothed:
            frame = float(start_frame) + (sample["time"] * float(fps))
            track.append({
                "frame": round(frame, 3),
                "value": round(clamp(sample["weights"].get(viseme, 0.0) * max_morph_value), 4),
                "frame_type": "sample",
            })
        result[viseme] = _simplify_track(track, start_frame)

    return result


def _append_release_tail(samples):
    if not samples:
        return []

    tail = list(samples)
    if len(samples) == 1:
        step = 0.05
    else:
        step = max(0.01, samples[-1]["time"] - samples[-2]["time"])

    last_time = samples[-1]["time"]
    for offset in range(1, 4):
        tail.append({
            "time": round(last_time + (step * offset), 4),
            "weights": zero_weights(),
        })
    return tail


def _derive_smoothing_params(buffer, approach_speed, anticipation_scale):
    normalized_buffer = clamp(float(buffer), 0.0, 1.0)
    normalized_speed = clamp(float(approach_speed), 0.1, 10.0)
    anticipation_scale = clamp(float(anticipation_scale), 0.2, 1.5)

    anticipation = (0.14 + (normalized_buffer * 0.18)) * anticipation_scale
    attack = clamp(
        0.72 - (normalized_buffer * 0.28) + ((normalized_speed - 1.0) * 0.025),
        0.35,
        0.9,
    )
    release = clamp(0.28 + (normalized_buffer * 0.15), 0.2, 0.55)
    contrast = clamp(1.0 + ((normalized_speed - 1.0) * 0.07), 1.0, 1.8)
    return anticipation, attack, release, contrast


def _build_empty_track(start_frame):
    frame = float(start_frame)
    return [
        {"frame": frame, "value": 0.0, "frame_type": "sample"},
        {"frame": round(frame + 1.0, 3), "value": 0.0, "frame_type": "sample"},
    ]


def _simplify_track(track, start_frame):
    if not track:
        return _build_empty_track(start_frame)

    points = _inject_boundaries(track, start_frame)
    points = _deduplicate_points(points)
    if len(points) <= 2:
        return points

    simplified = [points[0]]
    max_gap = 3.0
    epsilon = 0.015
    for index in range(1, len(points) - 1):
        previous_kept = simplified[-1]
        current = points[index]
        next_point = points[index + 1]

        deviation = _linear_deviation(previous_kept, current, next_point)
        is_turning_point = (
            (
                (current["value"] - previous_kept["value"])
                * (next_point["value"] - current["value"])
            ) <= 0.0
            and (
                abs(current["value"] - previous_kept["value"]) >= epsilon
                or abs(next_point["value"] - current["value"]) >= epsilon
            )
        )
        crosses_silence = (
            (previous_kept["value"] <= epsilon < current["value"])
            or (current["value"] <= epsilon < previous_kept["value"])
        )
        exceeds_gap = (current["frame"] - previous_kept["frame"]) >= max_gap

        if deviation >= epsilon or is_turning_point or crosses_silence or exceeds_gap:
            simplified.append(current)

    simplified.append(points[-1])
    return _deduplicate_points(simplified)


def _inject_boundaries(track, start_frame):
    points = list(track)
    start = float(start_frame)
    if points[0]["frame"] != start or points[0]["value"] != 0.0:
        points.insert(0, {"frame": start, "value": 0.0, "frame_type": "sample"})

    if points[-1]["value"] != 0.0:
        points.append({
            "frame": round(points[-1]["frame"] + 1.0, 3),
            "value": 0.0,
            "frame_type": "sample",
        })

    return points


def _deduplicate_points(points):
    deduplicated = []
    for point in points:
        if deduplicated and abs(deduplicated[-1]["frame"] - point["frame"]) <= 1e-4:
            deduplicated[-1] = point
            continue
        deduplicated.append(point)
    return deduplicated


def _linear_deviation(previous_point, current_point, next_point):
    frame_span = next_point["frame"] - previous_point["frame"]
    if frame_span <= 1e-8:
        return 0.0

    ratio = (current_point["frame"] - previous_point["frame"]) / frame_span
    expected_value = previous_point["value"] + (
        (next_point["value"] - previous_point["value"]) * ratio
    )
    return abs(current_point["value"] - expected_value)
