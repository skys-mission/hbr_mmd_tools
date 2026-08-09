# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
口型生成服务。
"""

from ..audio.lips import Lips
from ..core.config_manager import get_config_manager
from ..core.config_schema import CANONICAL_LIP_SYNC_KEYS
from ..core.lip_sync_profiles import get_lip_sync_preset_values
from ..core.sequencer import find_strip_by_name, get_scene_strips, get_strip_audio_filepath
from .selection_service import (
    clear_shape_key_keyframes_in_range,
    find_selected_meshes_with_shape_keys,
)
from ..util.logger import Log


def load_lip_sync_config(selection):
    """加载已选口型配置。"""
    if not selection:
        raise ValueError("Please select a configuration")

    config = get_config_manager().load_config("lip_sync", selection)
    if not config:
        raise ValueError(f"Failed to load config: {selection}")
    return config


def generate_lip_sync(context):
    """执行口型生成。"""
    scene = context.scene
    fps = scene.render.fps
    wav_path = _resolve_audio_path(scene)

    start_frame = scene.lips_start_frame
    if scene.lips_audio_source == 'timeline':
        strip = _find_timeline_audio_strip(scene)
        if strip is not None:
            timeline_start = int(strip.frame_final_start)
            if timeline_start != start_frame:
                Log.info(
                    f"Locking start frame to timeline audio start: "
                    f"{start_frame} -> {timeline_start}"
                )
                start_frame = timeline_start

    config = load_lip_sync_config(scene.lips_config_selection)
    tuning = _resolve_lip_sync_tuning(scene)
    lips = Lips.mmd_lips_gen(
        wav_path=wav_path,
        buffer=tuning["buffer"],
        approach_speed=tuning["approach_speed"],
        db_threshold=tuning["db_threshold"],
        rms_threshold=tuning["rms_threshold"],
        max_morph_value=tuning["max_morph_value"],
        start_frame=start_frame,
        fps=fps,
        anticipation_scale=tuning["anticipation_scale"],
    )
    meshes = find_mesh_with_config(context, config)
    for mesh in meshes:
        set_lips_to_mesh_with_config(mesh, lips, start_frame, config)
    return {
        "config": config,
        "mesh_count": len(meshes),
        "lips": lips,
    }


def _find_timeline_audio_strip(scene):
    """根据场景属性查找选中的时间线音频片段。"""
    return find_strip_by_name(
        get_scene_strips(scene),
        scene.lips_timeline_audio_strip,
    )


def _resolve_audio_path(scene):
    """根据音频源设置解析音频文件路径。"""
    import bpy  # pylint: disable=import-outside-toplevel,import-error

    if scene.lips_audio_source == 'file':
        path = scene.lips_audio_path
        if not path:
            raise ValueError("No audio file path specified")
        return path

    # timeline mode
    strip = _find_timeline_audio_strip(scene)
    if strip is None:
        raise ValueError(
            "No audio strip selected from timeline. "
            "Please add audio to the VSE timeline and select a strip."
        )

    filepath = get_strip_audio_filepath(strip)
    if not filepath:
        raise ValueError(f"Selected strip '{strip.name}' has no valid audio filepath.")

    abs_path = bpy.path.abspath(filepath)
    Log.info(f"Timeline audio resolved: {strip.name} -> {abs_path}")
    return abs_path


def _resolve_lip_sync_tuning(scene):
    if getattr(scene, "lips_use_custom_tuning", False):
        return {
            "buffer": scene.buffer_frame,
            "approach_speed": scene.approach_speed,
            "db_threshold": scene.db_threshold,
            "rms_threshold": scene.rms_threshold,
            "max_morph_value": scene.max_morph_value,
            "anticipation_scale": 1.0,
        }
    return get_lip_sync_preset_values(scene.lips_generation_preset)


def find_mesh_with_config(context, config):
    """根据配置查找包含指定形态键的对象。"""
    shape_keys = list(config.get("shape_keys", {}).values())
    found_objects = find_selected_meshes_with_shape_keys(context, shape_keys)
    if found_objects:
        Log.info(f"Found {len(found_objects)} objects containing configured shape keys")
        for obj in found_objects:
            Log.info(f"Object {obj.name} found with configured shape keys")
    return found_objects


def set_lips_to_mesh_with_config(mesh, lips, start_frame, config):  # pylint: disable=too-many-locals,too-many-branches
    """根据配置将 lips 数据应用到网格模型上。"""
    shape_key_mapping = config.get("shape_keys", {})
    adjustment_rules = config.get("adjustment_rules", {})
    target_tracks = _build_target_tracks(lips, shape_key_mapping, adjustment_rules)

    start = float(max(start_frame, 1))
    end = start
    for track in target_tracks.values():
        for keyframe in track:
            end = max(end, float(keyframe["frame"]))

    existing_morphs = {
        key.name for key in mesh.data.shape_keys.key_blocks
    } if mesh.data.shape_keys else set()

    for morph_key in target_tracks:
        if morph_key in existing_morphs:
            clear_shape_key_keyframes_in_range(mesh, morph_key, start, end)

    for target_morph_key, morph_frames in target_tracks.items():
        if target_morph_key not in existing_morphs:
            Log.warning(f"Target shape key '{target_morph_key}' not found in mesh")
            continue

        for morph_frame in morph_frames:
            if morph_frame["frame"] < start:
                continue
            set_shape_key_value(
                obj=mesh,
                shape_key_name=target_morph_key,
                value=morph_frame["value"],
                frame=morph_frame["frame"],
                f_type=morph_frame["frame_type"],
            )


def _build_target_tracks(lips, shape_key_mapping, adjustment_rules):
    target_tracks = {}
    for source_key in CANONICAL_LIP_SYNC_KEYS:
        target_morph_key = shape_key_mapping.get(source_key)
        if target_morph_key is None:
            # 配置未覆盖的规范键直接跳过（如 VRM 标准没有 ん），避免对不存在的形态键告警。
            continue
        target_track = target_tracks.setdefault(target_morph_key, {})
        adjustment_rule = adjustment_rules.get(source_key, {})

        for morph_frame in lips.get(source_key, []):
            adjusted_value = _apply_adjustment_rule(morph_frame["value"], adjustment_rule)
            frame = round(float(morph_frame["frame"]), 3)
            frame_key = f"{frame:.3f}"
            existing_frame = target_track.get(frame_key)
            if existing_frame is None or adjusted_value >= existing_frame["value"]:
                target_track[frame_key] = {
                    "frame": frame,
                    "value": adjusted_value,
                    "frame_type": morph_frame.get("frame_type", "sample"),
                }

    return {
        target_key: sorted(frame_map.values(), key=lambda item: item["frame"])
        for target_key, frame_map in target_tracks.items()
    }


def _apply_adjustment_rule(value, rule):
    base_value = max(0.0, float(value))
    if base_value <= 0.0:
        return 0.0

    priority = float(rule.get("priority", 1.0))
    adjustment_factor = float(rule.get("adjustment_factor", 1.0))
    if adjustment_factor > 0.0 and abs(adjustment_factor - 1.0) > 1e-6:
        base_value = base_value ** (1.0 / adjustment_factor)

    adjusted_value = base_value * priority
    # 强制保留余量，避免目标 morph 被精确锁定到 1.0 时与其他形态键叠加产生穿模
    return min(max(adjusted_value, 0.0), 0.99)


def set_shape_key_value(obj, shape_key_name, value, frame, f_type):  # pylint: disable=unused-argument
    """设置指定对象的形态键值。"""
    if not obj or obj.type != "MESH":
        Log.warning("The object is not of the mesh type.")
        return

    shape_keys = obj.data.shape_keys
    if not shape_keys or shape_key_name not in shape_keys.key_blocks:
        Log.warning(f"The shape key '{shape_key_name}' does not exist.")
        return

    shape_key = shape_keys.key_blocks[shape_key_name]
    shape_key.value = value
    shape_key.keyframe_insert(data_path="value", frame=frame)
