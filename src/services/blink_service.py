# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
随机眨眼服务。
"""

import random

from ..core.compat import get_action_fcurves
from ..core.config_manager import get_config_manager
from .selection_service import (
    clear_shape_key_keyframes_in_range,
    find_selected_meshes_with_shape_keys,
)


def load_blink_config(selection):
    """加载已选眨眼配置。"""
    if not selection:
        raise ValueError("Please select a configuration")

    config = get_config_manager().load_config("blink", selection)
    if not config:
        raise ValueError(f"Failed to load config: {selection}")
    return config


def generate_random_blink(context):
    """执行随机眨眼生成。"""
    scene = context.scene
    config = load_blink_config(scene.blink_config_selection)
    blink_data = generate_blink_frames(
        start_frame=scene.blink_start_frame,
        end_frame=scene.blink_end_frame,
        fps=scene.render.fps,
        interval_seconds=scene.blinking_frequency,
        wave_ratio=scene.blinking_wave_ratio,
        config=config,
        half_ratio=scene.blinking_half_ratio,
    )
    meshes = find_mmd_meshes_with_config(context, config)
    for mesh in meshes:
        apply_blink_animation_with_config(
            mesh,
            blink_data,
            scene.blink_start_frame,
            scene.blink_end_frame,
            config,
        )
    blink_shape_key = config.get("shape_keys", {}).get("blink", "まばたき")
    return {
        "config": config,
        "mesh_count": len(meshes),
        "blink_shape_key": blink_shape_key,
        "keyframe_count": len(blink_data.get(blink_shape_key, [])),
    }


def _generate_blink_times(start_frame, end_frame, fps, interval_seconds, wave_ratio):
    """生成眨眼时间点列表 [(time_seconds, is_double)]。"""
    current_time = start_frame / fps
    end_time = end_frame / fps
    std_dev = interval_seconds * max(0.01, wave_ratio) / 2.5
    all_blinks = []

    while current_time < end_time:
        next_interval = random.gauss(interval_seconds, std_dev)
        next_interval = max(0.3, next_interval)
        blink_time = current_time + next_interval

        if blink_time >= end_time:
            break

        all_blinks.append((blink_time, False))
        current_time = blink_time

        if random.random() < 0.10 and current_time + 0.30 < end_time:
            double_time = current_time + random.uniform(0.15, 0.30)
            if double_time < end_time:
                all_blinks.append((double_time, True))
                current_time = double_time

    return all_blinks


def _build_single_blink(blink_time, is_double, fps, blink_shape_key, half_ratio=0.15):
    """为单个眨眼生成关键帧列表。"""
    blink_frame = int(round(blink_time * fps))
    half_chance = min(1.0, half_ratio * 2.0) if is_double else half_ratio
    is_half = random.random() < half_chance
    peak_value = random.uniform(0.25, 0.55) if is_half else 1.0

    if is_double:
        duration = random.uniform(0.18, 0.28)
        close_ratio = random.uniform(0.30, 0.45)
        hold_ratio = random.uniform(0.05, 0.15)
    else:
        duration = random.uniform(0.28, 0.48)
        close_ratio = random.uniform(0.25, 0.40)
        hold_ratio = random.uniform(0.10, 0.25)

    close_frames = max(1, int(round(duration * close_ratio * fps)))
    hold_frames = max(0, int(round(duration * hold_ratio * fps)))
    open_frames = max(1, int(round(duration * (1.0 - close_ratio - hold_ratio) * fps)))

    keyframes = [{"frame": blink_frame - close_frames, "value": 0.0}]

    if close_frames >= 2:
        keyframes.append({"frame": blink_frame - close_frames // 2, "value": peak_value * 0.5})

    keyframes.append({"frame": blink_frame, "value": peak_value})

    if hold_frames >= 1:
        keyframes.append({"frame": blink_frame + hold_frames, "value": peak_value})

    if open_frames >= 3:
        keyframes.append(
            {"frame": blink_frame + hold_frames + open_frames // 2, "value": peak_value * 0.3}
        )

    keyframes.append({"frame": blink_frame + hold_frames + open_frames, "value": 0.0})
    return blink_shape_key, keyframes


def _dedup_sort(frame_list):
    """去重并按帧排序。"""
    seen = set()
    unique = []
    for kf in sorted(frame_list, key=lambda x: x["frame"]):
        if kf["frame"] not in seen:
            seen.add(kf["frame"])
            unique.append(kf)
    return unique


def generate_blink_frames(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    start_frame,
    end_frame,
    fps,
    interval_seconds,
    wave_ratio,
    config=None,
    half_ratio=0.15,
):
    """
    生成自然眨眼形态键动画帧序列。

    特性:
    - 正态分布的眨眼间隔
    - 支持双眨眼 (double blink)
    - 支持半眨眼 (half blink)，概率可调
    - 闭眼快、睁眼慢的不对称曲线
    """
    frames = {}
    blink_shape_key = (
        config.get("shape_keys", {}).get("blink", "まばたき")
        if config else "まばたき"
    )

    for blink_time, is_double in _generate_blink_times(
        start_frame, end_frame, fps, interval_seconds, wave_ratio,
    ):
        shape_key, keyframes = _build_single_blink(
            blink_time, is_double, fps, blink_shape_key, half_ratio,
        )
        frames.setdefault(shape_key, []).extend(keyframes)

    if blink_shape_key in frames:
        frames[blink_shape_key] = _dedup_sort(frames[blink_shape_key])

    frames.setdefault(blink_shape_key, []).insert(0, {"frame": start_frame, "value": 0.0})
    frames.setdefault(blink_shape_key, []).append({"frame": end_frame, "value": 0.0})

    if blink_shape_key in frames:
        frames[blink_shape_key] = _dedup_sort(frames[blink_shape_key])

    return frames


def find_mmd_meshes_with_config(context, config):
    """根据配置查找包含指定眨眼形态键的网格对象。"""
    blink_shape_key = (
        config.get("shape_keys", {}).get("blink", "まばたき")
        if config else "まばたき"
    )
    meshes = find_selected_meshes_with_shape_keys(context, [blink_shape_key])
    return meshes


def apply_blink_animation_with_config(mesh, frames, start_frame, end_frame, config=None):
    """根据配置文件将眨眼动画应用到网格对象。"""
    blink_shape_key = (
        config.get("shape_keys", {}).get("blink", "まばたき")
        if config else "まばたき"
    )

    for shape_key_name, keyframes in frames.items():
        if shape_key_name != blink_shape_key:
            continue

        shape_key = None
        for key_block in mesh.data.shape_keys.key_blocks:
            if key_block.name == shape_key_name:
                shape_key = key_block
                break

        if not shape_key:
            continue

        clear_shape_key_keyframes_in_range(mesh, shape_key_name, start_frame, end_frame)

        for keyframe in keyframes:
            shape_key.value = keyframe["value"]
            shape_key.keyframe_insert(data_path="value", frame=keyframe["frame"])

        # 设置关键帧 handle 类型使曲线更自然
        _set_keyframe_handles(mesh, shape_key_name)

        mesh.data.update_tag()


def _set_keyframe_handles(mesh, shape_key_name):
    """设置眨眼关键帧的 handle 类型为 AUTO_CLAMPED，使贝塞尔曲线更圆润。"""
    shape_keys = mesh.data.shape_keys
    anim_data = shape_keys.animation_data if shape_keys else None
    fcurves = get_action_fcurves(anim_data) if anim_data else None
    if not fcurves:
        return

    data_path = f'key_blocks["{shape_key_name}"].value'
    for fcurve in fcurves:
        if fcurve.data_path != data_path:
            continue
        for kp in fcurve.keyframe_points:
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"
            kp.interpolation = "BEZIER"
        break
